import inspect
from typing import Any, Dict
from flask import request

# Import extensions using the extension manager from extensions module
# This avoids circular import between masonite and helpers
from .extensions import get_extension

# Try to get optional extensions using the core extension manager
try:
    db = get_extension('db')
except:
    db = None

try:
    ma = get_extension('ma')
except:
    ma = None

try:
    bcrypt = get_extension('bcrypt')
except:
    bcrypt = None

try:
    mail = get_extension('mail')
except:
    mail = None

try:
    login_manager = get_extension('login_manager')
except:
    login_manager = None

try:
    jwt_manager = get_extension('jwt_manager')
except:
    jwt_manager = None

try:
    migrate = get_extension('migrate')
except:
    migrate = None

def get_signature(func):
    """Get the signature of a function, handling various wrapper types"""
    if hasattr(func, '__func__'):
        inner = func.__func__
        if hasattr(inner, 'func'):
            return inspect.signature(inner.func)
        return inspect.signature(inner)
    if hasattr(func, '__wrapped__'):
        return inspect.signature(func.__wrapped__)
    try:
        return inspect.signature(func)
    except ValueError:
        if hasattr(func, '__call__'):
            return inspect.signature(func.__call__)
        raise

def resolve_dependency(type_, param_name=None, route_kwargs=None):
    """Resolve a dependency using the DI system"""
    if type_ == inspect.Parameter.empty:
        if route_kwargs and param_name in route_kwargs:
            return route_kwargs[param_name]
        return None

    # 1. Custom Bindings from Controller
    from .masonite import Controller
    annotation_name = getattr(type_, '__name__', str(type_))
    resolver = None
    if type_ in Controller._bindings:
        resolver = Controller._bindings[type_]
    elif annotation_name in Controller._bindings:
        resolver = Controller._bindings[annotation_name]

    if resolver is not None:
        if callable(resolver) and not inspect.isclass(resolver):
            return resolver()
        return resolver

    # 2. Flask Request
    if annotation_name == 'Request' or 'Request' in str(type_):
        return request

    # 3. SQLAlchemy
    if annotation_name == 'SQLAlchemy' or 'SQLAlchemy' in str(type_):
        if db is None:
            return None  # Return None instead of raising an error
        return db

    # 3.1 Bcrypt
    if annotation_name == 'Bcrypt' or 'Bcrypt' in str(type_):
        if bcrypt is None:
            return None
        return bcrypt

    # 3.2 Marshmallow
    if annotation_name == 'Marshmallow' or 'Marshmallow' in str(type_):
        if ma is None:
            return None
        return ma

    # 3.3 Mail
    if annotation_name == 'Mail' or 'Mail' in str(type_):
        if mail is None:
            return None
        return mail

    # 3.4 LoginManager
    if annotation_name == 'LoginManager' or 'LoginManager' in str(type_):
        if login_manager is None:
            return None
        return login_manager

    # 3.5 JWTManager
    if annotation_name == 'JWTManager' or 'JWTManager' in str(type_):
        if jwt_manager is None:
            return None
        return jwt_manager

    # 3.6 Migrate
    if annotation_name == 'Migrate' or 'Migrate' in str(type_):
        if migrate is None:
            return None
        return migrate

    # 4. DB Session
    if annotation_name in ('Session', 'scoped_session') or 'Session' in str(type_) or 'scoped_session' in str(type_):
        if db is None:
            return None
        return db.session

    # 5. WTForms Form Subclasses
    try:
        from wtforms import Form
        if inspect.isclass(type_) and issubclass(type_, Form):
            formdata = request.form if request.form else (request.json if request.is_json else None)
            if not formdata and request.files:
                formdata = request.files
            return type_(formdata=formdata)
    except ImportError:
        pass

    # 5.5 Marshmallow Schema Subclasses
    try:
        from marshmallow import Schema
        if inspect.isclass(type_) and issubclass(type_, Schema):
            return type_()
    except ImportError:
        pass

    # 6. Service classes (naming convention suffix 'Service')
    if 'Service' in annotation_name:
        return type_()

    # 7. Fallback to route kwargs
    if route_kwargs and param_name in route_kwargs:
        return route_kwargs[param_name]

    return None