"""
flask_user.views
----------------
Plug-and-play authentication route factory.

Usage — identical to ``ApiMixin``::

    from flask_user.views import AuthViews

    AuthViews(api_bp, UserSchema, url_prefix='/auth')

Routes registered
-----------------
    POST   <prefix>/login      { token, refresh_token, user }
    DELETE <prefix>/login      logout
    POST   <prefix>/register   { ...user fields... }
    POST   <prefix>/refresh    { token }

Customisation
-------------
Override any input schema::

    AuthViews(api_bp, UserSchema, register_schema=StrictRegisterSchema)

Per-route decorators::

    AuthViews(api_bp, UserSchema, route_configs={
        'login'   : [rate_limit('10/minute')],
        'register': [admin_required],
    })
"""
from __future__ import annotations

import logging

from flask import current_app, jsonify
from flask.views import MethodView
from flask_login import current_user, login_required
from marshmallow import ValidationError
from werkzeug.exceptions import BadRequest, Unauthorized, UnprocessableEntity

from .exceptions import InvalidCredentialsError, RegistrationError, TokenError
from .schemas import LoginSchema, RefreshSchema, RegisterSchema, TokenSchema

log = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_service():
    ext = current_app.extensions.get('flask_user')
    if ext is None:
        raise RuntimeError(
            'FlaskUser is not initialised. '
            'Call user_ext.init_app(app, ...) in your app factory.'
        )
    return ext.service


def _load_json(schema) -> dict:
    from flask import request
    raw = request.get_json(silent=True)
    if not raw:
        raise BadRequest('Request body must be valid JSON.')
    try:
        return schema.load(raw)
    except ValidationError as exc:
        raise UnprocessableEntity(exc.messages)


def _apply_decorators(view_func, decorators: list):
    for dec in reversed(decorators):
        if not callable(dec):
            raise TypeError(f'Decorator must be callable, got {type(dec)!r}.')
        view_func = dec(view_func)
    return view_func


def _as_instance(schema):
    return schema() if isinstance(schema, type) else schema


# ── View classes ───────────────────────────────────────────────────────────────

class LoginView(MethodView):

    def __init__(self, login_schema, token_schema, user_schema):
        self._login = login_schema
        self._token = token_schema
        self._user  = user_schema

    def post(self):
        """POST <prefix>/login — authenticate, return tokens + user."""
        data = _load_json(self._login)

        try:
            access_token, refresh_token = _get_service().login(
                email    = data['email'],
                password = data['password'],
            )
        except InvalidCredentialsError as exc:
            raise Unauthorized(str(exc))

        response = self._token.dump({
            'token'        : access_token,
            'refresh_token': refresh_token,
        })
        if self._user is not None:
            response['user'] = self._user.dump(current_user)

        return jsonify(response), 200

    @login_required
    def delete(self):
        """DELETE <prefix>/login — end session."""
        _get_service().logout()
        return '', 204


class RegisterView(MethodView):

    def __init__(self, register_schema, user_schema):
        self._register = register_schema
        self._user     = user_schema

    def post(self):
        """POST <prefix>/register — create a regular user account."""
        data = _load_json(self._register)

        try:
            user = _get_service().register(**data)
        except RegistrationError as exc:
            raise BadRequest(str(exc))

        return jsonify(self._user.dump(user)), 201


class RefreshView(MethodView):

    def __init__(self, refresh_schema):
        self._refresh = refresh_schema

    def post(self):
        """POST <prefix>/refresh — exchange refresh token for new access token."""
        data = _load_json(self._refresh)

        try:
            new_access = _get_service().refresh_access_token(data['refresh_token'])
        except TokenError as exc:
            raise Unauthorized(str(exc))

        return jsonify({'token': new_access}), 200


# ── AuthViews factory ──────────────────────────────────────────────────────────

class AuthViews:
    """
    Register authentication routes on a Blueprint or Flask app.

    :param app_or_bp:       Target Blueprint or app.
    :param user_schema:     **Required.** Marshmallow schema class or instance
                            for the User model.  Supplied automatically when
                            ``FlaskUser.init_app`` is called with ``api_bp``.
    :param url_prefix:      Route prefix (default ``'/auth'``).
    :param login_schema:    Override login input schema.
    :param register_schema: Override register input schema.
    :param refresh_schema:  Override refresh input schema.
    :param token_schema:    Override token output schema.
    :param route_configs:   ``{'action': [decorator, ...]}`` dict.
                            Actions: ``'login'``, ``'logout'``,
                            ``'register'``, ``'refresh'``.
    """

    def __init__(
        self,
        app_or_bp,
        user_schema,
        url_prefix:      str  = '/auth',
        login_schema           = None,
        register_schema        = None,
        refresh_schema         = None,
        token_schema           = None,
        route_configs:   dict = None,
    ) -> None:
        if user_schema is None:
            raise TypeError(
                'AuthViews requires a user_schema argument.\n'
                'Example:\n'
                '    from app.schemas.users import UserSchema\n'
                "    AuthViews(api_bp, UserSchema, url_prefix='/auth')"
            )

        self._bp         = app_or_bp
        self._prefix     = url_prefix.rstrip('/')
        self._route_cfgs = route_configs or {}

        self._login_schema    = _as_instance(login_schema    or LoginSchema)
        self._register_schema = _as_instance(register_schema or RegisterSchema)
        self._refresh_schema  = _as_instance(refresh_schema  or RefreshSchema)
        self._token_schema    = _as_instance(token_schema    or TokenSchema)
        self._user_schema     = _as_instance(user_schema)

        self._register_routes()

    def _decorators(self, action: str) -> list:
        raw = self._route_cfgs.get(action, [])
        return [raw] if callable(raw) and not isinstance(raw, list) else list(raw)

    def _register_routes(self) -> None:
        p = self._prefix

        # ── Login (POST) and Logout (DELETE) share the same URL but need
        # independent decorator stacks, so they are registered separately.
        # Flask dispatches by HTTP method to the matching method on the view
        # class (post / delete), so two rules on the same URL + different
        # methods and endpoints work correctly.

        login_view = LoginView.as_view(
            'user_login',
            login_schema = self._login_schema,
            token_schema = self._token_schema,
            user_schema  = self._user_schema,
        )

        post_login = _apply_decorators(login_view, self._decorators('login'))
        self._bp.add_url_rule(
            f'{p}/login',
            endpoint  = 'user_login_post',
            view_func = post_login,
            methods   = ['POST'],
        )

        delete_login = _apply_decorators(login_view, self._decorators('logout'))
        self._bp.add_url_rule(
            f'{p}/login',
            endpoint  = 'user_login_delete',
            view_func = delete_login,
            methods   = ['DELETE'],
        )

        # ── Register ──────────────────────────────────────────────────────────
        register_view = RegisterView.as_view(
            'user_register',
            register_schema = self._register_schema,
            user_schema     = self._user_schema,
        )
        register_view = _apply_decorators(register_view, self._decorators('register'))
        self._bp.add_url_rule(
            f'{p}/register',
            endpoint  = 'user_register',
            view_func = register_view,
            methods   = ['POST'],
        )

        # ── Refresh ───────────────────────────────────────────────────────────
        refresh_view = RefreshView.as_view(
            'user_refresh',
            refresh_schema = self._refresh_schema,
        )
        refresh_view = _apply_decorators(refresh_view, self._decorators('refresh'))
        self._bp.add_url_rule(
            f'{p}/refresh',
            endpoint  = 'user_refresh',
            view_func = refresh_view,
            methods   = ['POST'],
        )

        log.debug('AuthViews registered: prefix=%s', p)
