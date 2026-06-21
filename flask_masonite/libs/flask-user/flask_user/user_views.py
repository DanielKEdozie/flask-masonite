"""
flask_user.user_views
---------------------
Plug-and-play User CRUD route factory.

Works identically to ``ApiMixin`` — call it once in your blueprint setup
and all standard user management routes are registered::

    from flask_user.user_views import UserViews

    UserViews(api_bp, url_prefix='/users')

Routes registered
-----------------
    GET    <prefix>/             List users (paginated, filterable, sortable)
    POST   <prefix>/             Create a new user (admin-side)
    GET    <prefix>/<id>         Get a single user
    PUT    <prefix>/<id>         Full update
    PATCH  <prefix>/<id>         Partial update
    DELETE <prefix>/<id>         Delete user

All views read the active models and schema from
``current_app.extensions['flask_user']`` — the same object
:class:`~flask_user.FlaskUser` registers at startup.

Query parameters (GET list)
---------------------------
    page        Page number (default 1)
    per_page    Items per page (default 20, max 100)
    q           Full-text search across email, first_name, last_name
    sort        Column to sort by (email | first_name | last_name | created_at)
    order       asc | desc (default asc)
    is_admin    Filter by admin flag (true | false)

Customisation
-------------
Supply a custom schema::

    UserViews(api_bp, schema=MyUserSchema, url_prefix='/users')

Per-route decorators (same pattern as ApiMixin route_configs)::

    UserViews(api_bp, route_configs={
        'get_all': [login_required],
        'update' : [login_required, admin_required],
        'delete' : [login_required, admin_required],
    })
"""
from __future__ import annotations

import logging

from flask import current_app, jsonify, request
from flask.views import MethodView
from marshmallow import ValidationError
from sqlalchemy import asc, desc, or_, cast, String
from werkzeug.exceptions import BadRequest, Forbidden, NotFound, UnprocessableEntity

log = logging.getLogger(__name__)

_SORT_FIELDS  = {'email', 'first_name', 'last_name', 'created_at'}
_FILTER_FIELDS = {'is_admin'}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_ext():
    ext = current_app.extensions.get('flask_user')
    if ext is None:
        raise RuntimeError(
            'FlaskUser is not initialised. '
            'Call user_ext.init_app(app, ...) in your app factory.'
        )
    return ext


def _apply_decorators(view_func, decorators: list):
    for dec in reversed(decorators):
        if not callable(dec):
            raise TypeError(f'Decorator must be callable, got {type(dec)!r}.')
        view_func = dec(view_func)
    return view_func


def _as_instance(schema):
    return schema() if isinstance(schema, type) else schema


def _load_json(schema) -> dict:
    from flask import request
    raw = request.get_json(silent=True)
    if not raw:
        raise BadRequest('Request body must be valid JSON.')
    try:
        return schema.load(raw)
    except ValidationError as exc:
        raise UnprocessableEntity(exc.messages)


# ── View classes ───────────────────────────────────────────────────────────────

class UserListView(MethodView):
    """GET <prefix>/ — paginated, searchable user list."""

    def __init__(self, schema, page_size, max_page_size):
        self._schema       = schema
        self._page_size    = page_size
        self._max_page_size = max_page_size

    def post(self):
        """POST <prefix>/ — create a new user (admin-side creation)."""
        ext = _get_ext()

        from .schemas import RegisterSchema
        from .exceptions import RegistrationError

        raw = request.get_json(silent=True)
        if not raw:
            from werkzeug.exceptions import BadRequest
            raise BadRequest('Request body must be valid JSON.')

        try:
            data = RegisterSchema().load(raw)
        except ValidationError as exc:
            raise UnprocessableEntity(exc.messages)

        # Admin may explicitly set is_admin via this endpoint (unlike the
        # public /auth/register route which always forces is_admin=False).
        is_admin = bool(raw.get('is_admin', False))

        try:
            user = ext.service.register(
                first_name = data['first_name'],
                last_name  = data['last_name'],
                email      = data['email'],
                password   = data['password'],
            )
            # Apply is_admin after creation — service.register() always
            # sets it to False for safety; we override here for admin routes.
            if is_admin:
                user.is_admin = True
                ext.db.session.commit()
        except RegistrationError as exc:
            from werkzeug.exceptions import BadRequest as BR
            raise BR(str(exc))

        return jsonify(self._schema.dump(user)), 201

    def get(self):
        ext  = _get_ext()
        User = ext.User
        db   = ext.db

        from sqlalchemy import select, func

        stmt = select(User)

        # ── Filters ──────────────────────────────────────────────────────────
        if 'is_admin' in request.args:
            val = request.args['is_admin'].lower()
            if val in ('true', '1'):
                stmt = stmt.where(User.is_admin == True)   # noqa: E712
            elif val in ('false', '0'):
                stmt = stmt.where(User.is_admin == False)  # noqa: E712

        # ── Search ───────────────────────────────────────────────────────────
        q = request.args.get('q', '').strip()
        if q:
            pattern = f'%{q}%'
            stmt = stmt.where(
                or_(
                    cast(User.email,      String).ilike(pattern),
                    cast(User.first_name, String).ilike(pattern),
                    cast(User.last_name,  String).ilike(pattern),
                )
            )

        # ── Sorting ───────────────────────────────────────────────────────────
        sort_col = request.args.get('sort', '').strip()
        order    = request.args.get('order', 'asc').strip().lower()
        if sort_col in _SORT_FIELDS and hasattr(User, sort_col):
            col  = getattr(User, sort_col)
            stmt = stmt.order_by(desc(col) if order == 'desc' else asc(col))
        else:
            stmt = stmt.order_by(asc(User.id))

        # ── Pagination ────────────────────────────────────────────────────────
        page     = max(request.args.get('page', 1, type=int), 1)
        per_page = min(
            request.args.get('per_page', self._page_size, type=int),
            self._max_page_size,
        )

        total = db.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar_one()

        users = db.session.execute(
            stmt.limit(per_page).offset((page - 1) * per_page)
        ).scalars().all()

        return jsonify({
            'items': self._schema.dump(users, many=True),
            'meta' : {
                'page'    : page,
                'per_page': per_page,
                'total'   : total,
                'pages'   : -(-total // per_page),
            },
        })


class UserDetailView(MethodView):
    """GET / PUT / PATCH / DELETE <prefix>/<id>."""

    def __init__(self, schema):
        self._schema = schema

    def _get_or_404(self, user_id: int):
        ext  = _get_ext()
        user = ext.db.session.get(ext.User, user_id)
        if user is None:
            raise NotFound(f'User {user_id} not found.')
        return user, ext.db

    def get(self, id: int):
        """GET <prefix>/<id> — return a single user."""
        user, _ = self._get_or_404(id)
        return jsonify(self._schema.dump(user))

    def put(self, id: int):
        """PUT <prefix>/<id> — full update."""
        return self._update(id, partial=False)

    def patch(self, id: int):
        """PATCH <prefix>/<id> — partial update."""
        return self._update(id, partial=True)

    def _update(self, user_id: int, partial: bool):
        user, db = self._get_or_404(user_id)
        raw = request.get_json(silent=True) or {}

        # Prevent clients from elevating is_admin via this endpoint.
        # Use the CLI or a dedicated admin promotion route instead.
        raw.pop('is_admin', None)

        try:
            updated = self._schema.load(raw, instance=user, partial=partial)
        except ValidationError as exc:
            raise UnprocessableEntity(exc.messages)

        try:
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            raise BadRequest(str(exc))

        return jsonify(self._schema.dump(updated))

    def delete(self, id: int):
        """DELETE <prefix>/<id> — remove a user and their auth record."""
        user, db = self._get_or_404(id)

        try:
            db.session.delete(user)
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            raise BadRequest(str(exc))

        return '', 204


# ── UserViews factory ──────────────────────────────────────────────────────────

class UserViews:
    """
    Register User CRUD routes on a Blueprint or Flask app.

    Mirrors ``ApiMixin`` — instantiate once and all routes are live::

        from flask_user.user_views import UserViews

        UserViews(api_bp, url_prefix='/users')

    :param app_or_bp:    Target Blueprint or Flask app.
    :param schema:       Marshmallow schema class or instance for the User
                         model.  When omitted the schema registered by
                         ``FlaskUser.init_app`` is used automatically.
    :param url_prefix:   Route prefix (default ``'/users'``).
    :param page_size:    Default page size for list endpoint (default 20).
    :param max_page_size: Hard cap on per_page (default 100).
    :param route_configs: ``{'action': [decorator, ...]}`` dict.
                          Actions: ``'get_all'``, ``'create'``,
                          ``'get_one'``, ``'update'``, ``'patch'``,
                          ``'delete'``.
    """

    def __init__(
        self,
        app_or_bp,
        schema          = None,
        url_prefix: str = '/users',
        page_size:  int = 20,
        max_page_size: int = 100,
        route_configs: dict = None,
    ) -> None:
        self._bp           = app_or_bp
        self._prefix       = url_prefix.rstrip('/')
        self._schema       = schema   # resolved lazily on first request if None
        self._page_size    = page_size
        self._max_page_size = max_page_size
        self._route_cfgs   = route_configs or {}

        self._register_routes()

    def _schema_instance(self):
        """Return the schema instance, falling back to the extension's schema."""
        if self._schema is not None:
            return _as_instance(self._schema)
        ext = current_app.extensions.get('flask_user')
        if ext is None or ext.UserSchema is None:
            raise RuntimeError(
                'No schema supplied to UserViews and FlaskUser has not been '
                'initialised.  Pass schema=UserSchema explicitly or call '
                'user_ext.init_app() first.'
            )
        return ext.UserSchema()

    def _decorators(self, action: str) -> list:
        raw = self._route_cfgs.get(action, [])
        return [raw] if callable(raw) and not isinstance(raw, list) else list(raw)

    def _register_routes(self) -> None:
        p      = self._prefix
        schema = self._schema  # may be None — resolved at request time

        # ── GET /users ────────────────────────────────────────────────────────
        list_view = UserListView.as_view(
            'user_list',
            schema       = _as_instance(schema) if schema else _LazySchema(self),
            page_size    = self._page_size,
            max_page_size = self._max_page_size,
        )
        get_all_view = _apply_decorators(list_view, self._decorators('get_all'))
        self._bp.add_url_rule(
            f'{p}/',
            endpoint  = 'user_list',
            view_func = get_all_view,
            methods   = ['GET'],
        )

        create_view = _apply_decorators(list_view, self._decorators('create'))
        self._bp.add_url_rule(
            f'{p}/',
            endpoint  = 'user_create',
            view_func = create_view,
            methods   = ['POST'],
        )

        # ── GET / PUT / PATCH / DELETE /users/<id> ────────────────────────────
        detail_view = UserDetailView.as_view(
            'user_detail',
            schema = _as_instance(schema) if schema else _LazySchema(self),
        )

        for action, methods, ep in [
            ('get_one', ['GET'],    'user_detail_get'),
            ('update',  ['PUT'],    'user_detail_put'),
            ('patch',   ['PATCH'],  'user_detail_patch'),
            ('delete',  ['DELETE'], 'user_detail_delete'),
        ]:
            decorated = _apply_decorators(detail_view, self._decorators(action))
            self._bp.add_url_rule(
                f'{p}/<int:id>',
                endpoint  = ep,
                view_func = decorated,
                methods   = methods,
            )

        log.debug('UserViews registered: prefix=%s', p)


class _LazySchema:
    """
    Proxy that resolves the schema from the FlaskUser extension at
    request time, so UserViews can be instantiated before init_app runs.
    """
    def __init__(self, user_views: UserViews):
        self._uv = user_views

    def dump(self, obj, many=False):
        return self._uv._schema_instance().dump(obj, many=many)

    def load(self, data, instance=None, partial=False):
        return self._uv._schema_instance().load(
            data, instance=instance, partial=partial
        )
