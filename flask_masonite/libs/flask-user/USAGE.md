# flask-user — Usage Guide

## Installation

```bash
# Drop the flask_user/ folder into your project root (no pip needed)
# OR install as a package:
pip install flask-user
```

---

## Required config

```python
SECRET_KEY         = 'your-access-token-secret'
JWT_REFRESH_SECRET = 'a-different-refresh-secret'   # must differ from SECRET_KEY
```

### Optional config

```python
JWT_ALGORITHM       = 'HS256'                  # default
JWT_ACCESS_EXPIRES  = timedelta(minutes=30)    # default
JWT_REFRESH_EXPIRES = timedelta(days=30)       # default
```

---

## Zero-config quick start (built-in models)

### 1. Extensions

```python
# app/extensions.py
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
```

### 2. App factory

```python
# app/__init__.py
from flask import Flask, Blueprint
from .extensions import db, ma, login_manager, bcrypt, user_ext

def create_app(config='development'):
    app = Flask(__name__)
    app.config.from_object(f'config.{config.title()}Config')

    db.init_app(app)
    ma.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)   # ← must come before user_ext.init_app

    api_bp = Blueprint('api', __name__)

    # One call — models, schema, login hooks, CLI, and API routes all wired.
    user_ext.init_app(app, db, bcrypt, ma, api_bp)

    app.register_blueprint(api_bp, url_prefix='/api')
    return app
```

This registers four routes on `api_bp`:

| Method | URL | Returns |
|--------|-----|---------|
| `POST` | `/api/auth/login` | `{ token, refresh_token, user }` |
| `DELETE` | `/api/auth/login` | `204` (logout) |
| `POST` | `/api/auth/register` | `{ id, email, first_name, … }` |
| `POST` | `/api/auth/refresh` | `{ token }` |

And registers the `flask user` CLI group on `app`.

After `init_app`, `user_ext` exposes:

```python
user_ext.User        # User model class — use in FK columns, queries
user_ext.UserAuth    # UserAuth model class
user_ext.UserSchema  # UserSchema class — use in other views
user_ext.service     # AuthService instance — call .login(), .register(), etc.
user_ext.db          # SQLAlchemy db — used internally by CLI commands
```

---

## Built-in models

### User

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer | Primary key |
| `first_name` | String(120) | Required |
| `last_name` | String(120) | Required |
| `email` | String(255) | Required, unique, indexed |
| `is_admin` | Boolean | Default `False` — set via CLI only |
| `created_at` | DateTime | Server-side, set on insert |
| `updated_at` | DateTime | Server-side, auto-updated on every write |

**Properties:**

```python
user.full_name   # → '{first_name} {last_name}'
user.auth        # → related UserAuth instance (one-to-one, lazy='joined')
```

### UserAuth

| Column | Type | Notes |
|--------|------|-------|
| `user_id` | Integer | Primary key **and** FK → `users.id` |
| `password` | String(255) | Stored as bcrypt hash — write-only |

```python
UserAuth(user=user, password='plain')   # hashes immediately on construction
user.auth.verify_password('plain')      # → bool
user.auth.password                      # → raises AttributeError (write-only)
```

> **Why `user_id` as the primary key?**  Using the FK as the PK enforces
> the one-to-one relationship at the database level — no extra `UNIQUE`
> constraint needed and orphaned auth rows are structurally impossible.

> **Why a write-only property?**  Prevents the bcrypt hash from being
> accidentally logged or serialised.  The setter guarantees the plain text
> is always hashed before it reaches the database, even in unit tests.

---

## CLI commands

All commands require `FLASK_APP` to point at your app factory.

### `flask user create-admin`

Create a new admin user or promote an existing account to admin.

```bash
# Interactive (prompts for all fields)
flask user create-admin

# Non-interactive
flask user create-admin \
    --email admin@example.com \
    --first-name Jane \
    --last-name Doe \
    --password secret
```

If a user with the given email already exists their `is_admin` flag is
set to `True` and their password is updated.  If no user exists a new
account is created with `is_admin=True`.

> Admin accounts can **only** be created via this command, never through
> the public `POST /auth/register` endpoint (`is_admin` is forced to
> `False` there regardless of the request body).

---

### `flask user list`

Print a table of all users.

```bash
flask user list
flask user list --admin-only   # show only admins
```

Output:

```
ID     EMAIL                               NAME                      ADMIN  CREATED
-------------------------------------------------------------------------------------
1      admin@example.com                   Jane Doe                  yes    2024-01-15
2      jane@example.com                    John Smith                no     2024-01-16
```

---

### `flask user delete <email>`

Delete a user account and its auth record (cascaded at the DB level).

```bash
flask user delete jane@example.com          # prompts for confirmation
flask user delete jane@example.com --yes    # skips confirmation
```

---

### `flask user set-password <email>`

Reset a user's password.

```bash
flask user set-password jane@example.com
# → prompts for new password (hidden input, confirmed twice)
```

---

## HTTP API reference

### `POST /auth/login`

**Request body**

```json
{ "email": "jane@example.com", "password": "secret" }
```

**Response 200**

```json
{
  "token": "<access_jwt>",
  "refresh_token": "<refresh_jwt>",
  "user": {
    "id": 1,
    "email": "jane@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "full_name": "Jane Doe",
    "is_admin": false,
    "created_at": "2024-01-15T10:00:00"
  }
}
```

| Status | When |
|--------|------|
| `200` | Success |
| `401` | Wrong email or password |
| `422` | Missing or invalid fields |

---

### `DELETE /auth/login`

Requires `Authorization: Bearer <token>` header.

**Response** `204 No Content`

---

### `POST /auth/register`

**Request body**

```json
{
  "first_name": "Jane",
  "last_name":  "Doe",
  "email":      "jane@example.com",
  "password":   "secret"
}
```

**Response 201** — serialised via `UserSchema`

| Status | When |
|--------|------|
| `201` | Created |
| `400` | Email already registered |
| `422` | Missing or invalid fields |

---

### `POST /auth/refresh`

**Request body**

```json
{ "refresh_token": "<refresh_jwt>" }
```

**Response 200**

```json
{ "token": "<new_access_jwt>" }
```

| Status | When |
|--------|------|
| `200` | Success |
| `401` | Refresh token invalid or expired |

---

## Custom models

Drop in your own models by passing them to `init_app`.  The package only
requires the contract below — field names and extras are up to you.

**Contract:**

```python
# User must have:
user.auth                           # one-to-one relationship to UserAuth
user.is_admin                       # boolean

# UserAuth must have:
UserAuth(user=user, password=plain) # hashes on construction
user.auth.verify_password(plain)    # returns bool
```

```python
# app/models/users.py
from app.extensions import db, bcrypt

class User(db.Model):
    __tablename__ = 'users'
    id         = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name  = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(255), nullable=False, unique=True)
    is_admin   = db.Column(db.Boolean, default=False, nullable=False)
    auth       = db.relationship('UserAuth', back_populates='user',
                                 uselist=False, lazy='joined',
                                 cascade='all, delete-orphan')

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'


class UserAuth(db.Model):
    __tablename__ = 'user_auth'
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                          primary_key=True)
    _password = db.Column('password', db.String(255), nullable=False)
    user      = db.relationship('User', back_populates='auth')

    def __init__(self, user, password):
        self.user     = user
        self.password = password

    @property
    def password(self):
        raise AttributeError('write-only')

    @password.setter
    def password(self, plain):
        self._password = bcrypt.generate_password_hash(plain).decode('utf-8')

    def verify_password(self, plain):
        return bcrypt.check_password_hash(self._password, plain)
```

```python
# app/schemas/users.py
from app.extensions import ma
from app.models.users import User

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model         = User
        load_instance = True
        exclude       = ('auth',)
        dump_only     = ('id', 'is_admin', 'created_at')
```

```python
# app/__init__.py
from app.models.users  import User, UserAuth
from app.schemas.users import UserSchema

user_ext.init_app(
    app, db, bcrypt, ma, api_bp,
    user_model      = User,
    user_auth_model = UserAuth,
    user_schema     = UserSchema,
)
```

---

## Custom validation schemas

Subclass any input schema and pass it in:

```python
from marshmallow   import validates, ValidationError
from flask_user    import RegisterSchema
import re

class StrictRegisterSchema(RegisterSchema):
    @validates('password')
    def strong_password(self, value):
        if len(value) < 8:
            raise ValidationError('Password must be at least 8 characters.')
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Must contain an uppercase letter.')
        if not re.search(r'[0-9]', value):
            raise ValidationError('Must contain a number.')

user_ext.init_app(
    app, db, bcrypt, ma, api_bp,
    register_schema = StrictRegisterSchema,
)
```

---

## Per-route decorators

Same pattern as `ApiMixin.route_configs`:

```python
from flask_limiter import Limiter

limiter = Limiter(key_func=get_remote_address)

user_ext.init_app(
    app, db, bcrypt, ma, api_bp,
    route_configs = {
        'login'   : [limiter.limit('10 per minute')],
        'register': [limiter.limit('3 per hour')],
    },
)
```

---

## Protecting views with `is_admin`

```python
from functools import wraps
from flask import abort
from flask_login import current_user, login_required

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return 'Admin only'
```

---

## Using `user_ext.User` in your own models

```python
# app/models/products.py
from app.extensions import db, user_ext

class Product(db.Model):
    __tablename__ = 'products'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(255), nullable=False)
    created_by = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False,
    )
    creator = db.relationship(user_ext.User, backref='products')
```

> Access `user_ext.User` **after** `init_app` has run.  Inside an
> app factory this means defining models that reference it in a function
> body, not at module import time.

---

## Token revocation (blocklist)

Override `_is_token_revoked` in a subclass:

```python
from flask_user import AuthService, FlaskUser

class BlocklistAuthService(AuthService):
    def __init__(self, db, user_model, user_auth_model, redis_client):
        super().__init__(db, user_model, user_auth_model)
        self._redis = redis_client

    def _is_token_revoked(self, payload):
        jti = payload.get('jti')
        return bool(jti and self._redis.exists(f'revoked:{jti}'))

# After init_app, swap in the custom service:
user_ext.init_app(app, db, bcrypt, ma, api_bp)
user_ext.service = BlocklistAuthService(
    db, user_ext.User, user_ext.UserAuth, redis_client
)
```

---

## User CRUD API

Registered automatically alongside the auth routes when you pass `api_bp`
to `init_app`. No extra code needed.

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/users/` | Paginated user list |
| `GET` | `/api/users/<id>` | Single user |
| `PUT` | `/api/users/<id>` | Full update |
| `PATCH` | `/api/users/<id>` | Partial update |
| `DELETE` | `/api/users/<id>` | Delete user |

### GET /users/ — query parameters

| Param | Type | Description |
|-------|------|-------------|
| `page` | int | Page number (default 1) |
| `per_page` | int | Items per page (default 20, max 100) |
| `q` | string | Search across email, first_name, last_name |
| `sort` | string | `email` \| `first_name` \| `last_name` \| `created_at` |
| `order` | string | `asc` (default) \| `desc` |
| `is_admin` | bool | Filter to `true` or `false` |

**Response 200**

```json
{
  "items": [{ "id": 1, "email": "jane@example.com", "is_admin": false, ... }],
  "meta":  { "page": 1, "per_page": 20, "total": 42, "pages": 3 }
}
```

### Protecting user routes

By default the user CRUD routes have no auth guard — add decorators via
`users_route_configs`:

```python
user_ext.init_app(
    app, db, bcrypt, ma, api_bp,
    users_route_configs = {
        'get_all': [login_required],
        'get_one': [login_required],
        'update' : [login_required, admin_required],
        'patch'  : [login_required, admin_required],
        'delete' : [login_required, admin_required],
    },
)
```

### Standalone usage (without init_app auto-registration)

```python
from flask_user.user_views import UserViews

UserViews(
    api_bp,
    url_prefix          = '/users',
    users_route_configs = {
        'delete': [login_required, admin_required],
    },
)
```

> **Note:** `is_admin` is stripped from `PUT`/`PATCH` request bodies
> — it can never be changed through the REST API.  Use
> `flask user create-admin` or a direct DB update instead.


---

## Exception reference

| Exception | Raised when |
|-----------|-------------|
| `UserError` | Base — catches all below |
| `InvalidCredentialsError` | Login email/password mismatch |
| `TokenError` | JWT invalid, expired, or revoked |
| `RegistrationError` | Duplicate email or DB conflict on register |

```python
from flask_user import InvalidCredentialsError, TokenError

try:
    access, refresh = user_ext.service.login(email, password)
except InvalidCredentialsError:
    abort(401)
```
