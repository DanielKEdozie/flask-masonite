"""
flask_user.extension
--------------------
:class:`FlaskUser` — the single entry point for the entire package.

One ``init_app`` call wires:

- Built-in or custom ``User`` + ``UserAuth`` models (with ``is_admin``)
- Default or custom ``UserSchema``
- Flask-Login ``user_loader``, ``request_loader``, ``unauthorized_handler``
- Auth API routes on any Blueprint/app (optional)
- Flask CLI ``user`` command group

Usage
-----
::

    # extensions.py
    from flask_user import FlaskUser
    user_ext = FlaskUser()

    # app/__init__.py
    from .extensions import db, ma, bcrypt, login_manager, user_ext

    def create_app(config='development'):
        app = Flask(__name__)
        app.config.from_object(...)

        db.init_app(app)
        ma.init_app(app)
        bcrypt.init_app(app)
        login_manager.init_app(app)   # must come before user_ext.init_app

        api_bp = Blueprint('api', __name__)

        # One call — models, schema, login hooks, CLI, API routes all wired.
        user_ext.init_app(app, db, bcrypt, ma, api_bp)

        app.register_blueprint(api_bp, url_prefix='/api')
        return app

After init_app, ``user_ext`` exposes:

    user_ext.User        User model class
    user_ext.UserAuth    UserAuth model class
    user_ext.UserSchema  UserSchema class
    user_ext.service     AuthService instance
    user_ext.db          db instance (used by CLI commands)

CLI commands (available after init_app):

    flask user create-admin   Create / promote an admin account
    flask user list           List all users
    flask user delete         Delete a user by email
    flask user set-password   Reset a user's password
"""
from __future__ import annotations

import logging
from typing import Any

from .service import AuthService

log = logging.getLogger(__name__)


def _find_login_manager(app: Any) -> Any:
    """Find a Flask-Login LoginManager across all known storage locations."""
    lm = app.extensions.get('login_manager')
    if lm is not None:
        return lm
    try:
        from flask_login import LoginManager
        lm = app.extensions.get(LoginManager)
        if lm is not None:
            return lm
    except ImportError:
        pass
    return getattr(app, 'login_manager', None)


class FlaskUser:
    """
    Flask extension bundling user management, JWT auth, and CLI tools.

    :attr service:    Live :class:`~flask_user.AuthService` instance.
    :attr User:       Active User model class.
    :attr UserAuth:   Active UserAuth model class.
    :attr UserSchema: Active UserSchema class.
    :attr db:         SQLAlchemy ``db`` instance (exposed for CLI commands).
    """

    def __init__(self, app: Any = None, **kwargs) -> None:
        self.service:    AuthService | None = None
        self.User:       type | None        = None
        self.UserAuth:   type | None        = None
        self.UserSchema: type | None        = None
        self.db:         Any                = None

        if app is not None:
            self.init_app(app, **kwargs)

    def init_app(
        self,
        app,
        db,
        bcrypt,
        ma,
        api_bp                  = None,
        *,
        user_model:      type | None = None,
        user_auth_model: type | None = None,
        user_schema             = None,
        auth_url_prefix:  str  = '/auth',
        users_url_prefix: str  = '/users',
        login_schema            = None,
        register_schema         = None,
        refresh_schema          = None,
        token_schema            = None,
        route_configs:   dict   = None,
        users_route_configs: dict = None,
        users_schema            = None,
        users_page_size:  int  = 20,
        users_max_page_size: int = 100,
        login_manager           = None,
    ) -> None:
        """
        Bind FlaskUser to *app*.

        Parameters
        ----------
        app             Flask application instance.
        db              Flask-SQLAlchemy ``SQLAlchemy`` instance.
        bcrypt          Flask-Bcrypt ``Bcrypt`` instance.
        ma              Flask-Marshmallow ``Marshmallow`` instance.
        api_bp          Blueprint or app to register auth routes on.
                        When given, routes are wired automatically.
        user_model      Custom User model class.  Auto-created when omitted.
        user_auth_model Custom UserAuth model class.  Auto-created when omitted.
        user_schema     Custom UserSchema class or instance.  Auto-created
                        when omitted.
        auth_url_prefix URL prefix for auth routes (default ``'/auth'``).
        login_schema    Override the login input schema.
        register_schema Override the register input schema.
        refresh_schema  Override the refresh input schema.
        token_schema    Override the token output schema.
        route_configs        Per-action auth decorator dict.
        users_route_configs  Per-action decorator dict for user CRUD routes.
                             Actions: get_all, get_one, update, patch, delete.
        users_schema         Override the schema used for user CRUD routes.
                             Defaults to the built-in / auto-generated UserSchema.
        users_url_prefix     URL prefix for user CRUD routes (default '/users').
        users_page_size      Default page size for user list (default 20).
        users_max_page_size  Hard cap on per_page (default 100).
        login_manager        Explicit LoginManager.  Auto-detected when omitted.

        :raises RuntimeError: if no LoginManager is found on *app*.
        """
        self.db = db

        # ── 1. Resolve / create models ────────────────────────────────────────
        if user_model is None or user_auth_model is None:
            from .models import init_models
            _User, _UserAuth = init_models(db, bcrypt)
            user_model      = user_model      or _User
            user_auth_model = user_auth_model or _UserAuth

        self.User     = user_model
        self.UserAuth = user_auth_model

        # ── 2. Resolve / build user schema ────────────────────────────────────
        if user_schema is None:
            from .user_schema import build_user_schema
            user_schema = build_user_schema(ma, user_model)

        self.UserSchema = (
            user_schema if isinstance(user_schema, type) else type(user_schema)
        )

        # ── 3. Initialise service ─────────────────────────────────────────────
        self.service = AuthService(db, user_model, user_auth_model)
        app.extensions['flask_user'] = self

        # ── 4. Flask-Login hooks ──────────────────────────────────────────────
        if login_manager is None:
            login_manager = _find_login_manager(app)

        if login_manager is None:
            raise RuntimeError(
                'FlaskUser.init_app: no LoginManager found on this app.\n'
                'Pass it explicitly:\n'
                '    user_ext.init_app(app, ..., login_manager=login_manager)\n'
                'or call login_manager.init_app(app) first.'
            )

        _svc = self.service

        auth_method = app.config.get('USER_AUTH_METHOD', 'both')

        if auth_method in ('session', 'session_cookie', 'both'):
            @login_manager.user_loader
            def _user_loader(user_id: str):
                return db.session.get(user_model, int(user_id))

        if auth_method in ('token', 'token_auth', 'both'):
            @login_manager.request_loader
            def _request_loader(req):
                header = req.headers.get('Authorization', '')
                if not header.startswith('Bearer '):
                    return None
                return _svc.verify_access_token(header[len('Bearer '):])

        @login_manager.unauthorized_handler
        def _unauthorized():
            from flask import redirect, request as req, url_for
            if req.path.startswith('/api/') or auth_method in ('token', 'token_auth'):
                return {'message': 'Authentication required.'}, 401
            
            # Check if 'login' or 'auth.login' is registered in app view functions
            login_url_name = 'login'
            if 'auth.login' in app.view_functions:
                login_url_name = 'auth.login'
            return redirect(url_for(login_url_name))

        # ── 5. Register auth API routes ───────────────────────────────────────
        if api_bp is not None:
            from .views import AuthViews
            AuthViews(
                api_bp,
                user_schema     = user_schema,
                url_prefix      = auth_url_prefix,
                login_schema    = login_schema,
                register_schema = register_schema,
                refresh_schema  = refresh_schema,
                token_schema    = token_schema,
                route_configs   = route_configs,
            )

        # ── 6. Register user CRUD routes ──────────────────────────────────────
        if api_bp is not None:
            from .user_views import UserViews
            UserViews(
                api_bp,
                schema          = users_schema,
                url_prefix      = users_url_prefix,
                page_size       = users_page_size,
                max_page_size   = users_max_page_size,
                route_configs   = users_route_configs,
            )

        # ── 7. Register CLI commands ──────────────────────────────────────────
        from .cli import user_cli
        app.cli.add_command(user_cli)

        log.debug(
            'FlaskUser initialised: user_model=%s is_admin=True',
            user_model.__name__,
        )

    # ── Proxy methods ──────────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> tuple[str, str]:
        """Proxy to :meth:`~flask_user.AuthService.login`."""
        return self.service.login(email, password)

    def logout(self) -> None:
        """Proxy to :meth:`~flask_user.AuthService.logout`."""
        self.service.logout()

    def register(self, **kwargs) -> Any:
        """Proxy to :meth:`~flask_user.AuthService.register`."""
        return self.service.register(**kwargs)

    def verify_access_token(self, token: str) -> Any | None:
        """Proxy to :meth:`~flask_user.AuthService.verify_access_token`."""
        return self.service.verify_access_token(token)

    def refresh_access_token(self, refresh_token: str) -> str:
        """Proxy to :meth:`~flask_user.AuthService.refresh_access_token`."""
        return self.service.refresh_access_token(refresh_token)
