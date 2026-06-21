"""
flask_user.exceptions
---------------------
Typed exception hierarchy.  All inherit from ``UserError`` so callers
can catch broadly or narrowly::

    from flask_user import UserError, InvalidCredentialsError

    try:
        access, refresh = user.service.login(email, password)
    except InvalidCredentialsError:
        abort(401)
    except UserError:
        abort(500)
"""


class UserError(Exception):
    """Base class for all flask-user errors."""


class InvalidCredentialsError(UserError):
    """Raised when an email/password pair does not match any account."""


class TokenError(UserError):
    """Raised when a JWT cannot be decoded, is expired, or has been revoked."""


class RegistrationError(UserError):
    """Raised when account creation fails (e.g. duplicate email, DB conflict)."""
