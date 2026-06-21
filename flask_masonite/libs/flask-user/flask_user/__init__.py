"""
flask_user
----------
JWT + Flask-Login user management extension for Flask.

Everything is wired by a single ``init_app`` call:

- Built-in ``User`` + ``UserAuth`` models (including ``is_admin``)
- Default ``UserSchema`` (Marshmallow)
- Flask-Login hooks (user_loader, request_loader, unauthorized_handler)
- Auth API routes on any Blueprint
- Flask CLI ``user`` command group

Quick start
-----------
::

    # extensions.py
    from flask_sqlalchemy  import SQLAlchemy
    from flask_marshmallow import Marshmallow
    from flask_login       import LoginManager
    from flask_bcrypt      import Bcrypt
    from flask_user        import FlaskUser

    db            = SQLAlchemy()
    ma            = Marshmallow()
    login_manager = LoginManager()
    bcrypt        = Bcrypt()
    user_ext      = FlaskUser()

    # app/__init__.py
    from flask import Flask, Blueprint
    from .extensions import db, ma, login_manager, bcrypt, user_ext

    def create_app(config='development'):
        app = Flask(__name__)
        app.config.from_object(f'config.{config.title()}Config')

        db.init_app(app)
        ma.init_app(app)
        bcrypt.init_app(app)
        login_manager.init_app(app)   # must come before user_ext.init_app

        api_bp = Blueprint('api', __name__)

        # One call — models, schema, hooks, CLI, routes all wired.
        user_ext.init_app(app, db, bcrypt, ma, api_bp)

        app.register_blueprint(api_bp, url_prefix='/api')
        return app

Routes registered on api_bp
----------------------------
    POST   /api/auth/login      { token, refresh_token, user }
    DELETE /api/auth/login      logout (requires Bearer token)
    POST   /api/auth/register   { id, email, first_name, last_name, is_admin, … }
    POST   /api/auth/refresh    { token }

    GET    /api/users/           list users (paginated, searchable, sortable)
    GET    /api/users/<id>       get one user
    PUT    /api/users/<id>       full update
    PATCH  /api/users/<id>       partial update
    DELETE /api/users/<id>       delete user

Attributes exposed after init_app
----------------------------------
    user_ext.User        User model class — use in relationships and queries
    user_ext.UserAuth    UserAuth model class
    user_ext.UserSchema  UserSchema class
    user_ext.service     AuthService instance
    user_ext.db          SQLAlchemy db instance

CLI commands
------------
    flask user create-admin     Create / promote an admin account
    flask user list             List all users (--admin-only flag available)
    flask user delete <email>   Delete a user
    flask user set-password <email>   Reset a password

User model fields
-----------------
    id          integer primary key
    first_name  string, required
    last_name   string, required
    email       string, unique, indexed
    is_admin    boolean, default False
    created_at  server timestamp
    updated_at  server timestamp (auto-updated)

    user.full_name  property → '{first_name} {last_name}'
    user.auth       one-to-one UserAuth relationship

UserAuth model
--------------
    user_id     primary key + foreign key → users.id
    password    write-only property (bcrypt-hashed)

    user_auth.verify_password(plain) → bool

Custom models
-------------
::

    from app.models.users  import User, UserAuth
    from app.schemas.users import UserSchema

    user_ext.init_app(
        app, db, bcrypt, ma, api_bp,
        user_model      = User,
        user_auth_model = UserAuth,
        user_schema     = UserSchema,
    )

Required config
---------------
    SECRET_KEY         access-token signing key
    JWT_REFRESH_SECRET refresh-token signing key (must differ)

Optional config
---------------
    JWT_ALGORITHM       'HS256'              (default)
    JWT_ACCESS_EXPIRES  timedelta(minutes=30) (default)
    JWT_REFRESH_EXPIRES timedelta(days=30)    (default)
"""

from .extension  import FlaskUser
from .service    import AuthService
from .views      import AuthViews
from .user_views import UserViews
from .models     import init_models
from .user_schema import build_user_schema
from .schemas    import LoginSchema, RegisterSchema, RefreshSchema, TokenSchema
from .exceptions import (
    UserError,
    InvalidCredentialsError,
    TokenError,
    RegistrationError,
)

__version__ = '1.0.0'

__all__ = [
    # Primary interface
    'FlaskUser',
    'AuthViews',
    'UserViews',
    # Service (for subclassing)
    'AuthService',
    # Model + schema factories
    'init_models',
    'build_user_schema',
    # Input schemas (for overriding)
    'LoginSchema',
    'RegisterSchema',
    'RefreshSchema',
    'TokenSchema',
    # Exceptions
    'UserError',
    'InvalidCredentialsError',
    'TokenError',
    'RegistrationError',
]
