"""
flask_user.service
------------------
Stateless JWT + Flask-Login authentication service.

All config is read lazily from ``current_app.config``.

Required config
---------------
    SECRET_KEY          Access-token signing key.
    JWT_REFRESH_SECRET  Refresh-token signing key (must differ).

Optional config
---------------
    JWT_ALGORITHM       default 'HS256'
    JWT_ACCESS_EXPIRES  default timedelta(minutes=30)
    JWT_REFRESH_EXPIRES default timedelta(days=30)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from flask import current_app
from flask_login import login_user, logout_user
from jwt.exceptions import InvalidTokenError

from .exceptions import InvalidCredentialsError, RegistrationError, TokenError

log = logging.getLogger(__name__)

_DEFAULT_ALGORITHM       = 'HS256'
_DEFAULT_ACCESS_EXPIRES  = timedelta(minutes=30)
_DEFAULT_REFRESH_EXPIRES = timedelta(days=30)


class AuthService:
    """
    Stateless authentication service.

    Instantiated once by :class:`~flask_user.FlaskUser`.

    :param db:              Flask-SQLAlchemy ``db`` instance.
    :param user_model:      User model class.
    :param user_auth_model: UserAuth model class.
    """

    def __init__(self, db, user_model: type, user_auth_model: type) -> None:
        self._db              = db
        self._user_model      = user_model
        self._user_auth_model = user_auth_model

    # ── Config ────────────────────────────────────────────────────────────────

    @property
    def _access_secret(self) -> str:
        return current_app.config['SECRET_KEY']

    @property
    def _refresh_secret(self) -> str:
        s = current_app.config.get('JWT_REFRESH_SECRET')
        if not s:
            raise RuntimeError(
                'JWT_REFRESH_SECRET is not configured. '
                'It must differ from SECRET_KEY.'
            )
        return s

    @property
    def _algorithm(self) -> str:
        return current_app.config.get('JWT_ALGORITHM', _DEFAULT_ALGORITHM)

    @property
    def _access_expires(self) -> timedelta:
        return current_app.config.get('JWT_ACCESS_EXPIRES', _DEFAULT_ACCESS_EXPIRES)

    @property
    def _refresh_expires(self) -> timedelta:
        return current_app.config.get('JWT_REFRESH_EXPIRES', _DEFAULT_REFRESH_EXPIRES)

    # ── Token helpers ─────────────────────────────────────────────────────────

    def _make_token(self, user_id: int, expires_in: timedelta, secret: str) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {'sub': str(user_id), 'iat': now, 'exp': now + expires_in},
            secret,
            algorithm=self._algorithm,
        )

    def _decode_token(self, token: str, secret: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=[self._algorithm],
                options={'require': ['sub', 'exp', 'iat']},
            )
        except InvalidTokenError as exc:
            raise TokenError(str(exc)) from exc

        if self._is_token_revoked(payload):
            raise TokenError('Token has been revoked.')

        return payload

    def _is_token_revoked(self, payload: dict[str, Any]) -> bool:
        """
        Token revocation hook.  Override to integrate a blocklist::

            class MyService(AuthService):
                def _is_token_revoked(self, payload):
                    return redis.exists(f"revoked:{payload['jti']}")
        """
        return False

    # ── Public API ────────────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> tuple[str, str]:
        """
        Verify credentials and return ``(access_token, refresh_token)``.

        :raises InvalidCredentialsError: on mismatch.
        """
        email = email.lower().strip()
        user  = self._user_model.query.filter_by(email=email).first()

        if not user or not user.auth.verify_password(password):
            log.warning('Failed login for email: %s', email)
            raise InvalidCredentialsError('Invalid email or password.')

        login_user(user)
        log.info('User %s logged in (admin=%s).', user.id, user.is_admin)

        return (
            self._make_token(user.id, self._access_expires,  self._access_secret),
            self._make_token(user.id, self._refresh_expires, self._refresh_secret),
        )

    def logout(self) -> None:
        """End the current Flask-Login session."""
        logout_user()

    def register(
        self,
        first_name: str,
        last_name:  str,
        email:      str,
        password:   str,
    ) -> Any:
        """
        Create a new regular user account.

        Admin accounts must be created via ``flask user create-admin``.

        :raises RegistrationError: on duplicate email or DB conflict.
        """
        from sqlalchemy.exc import IntegrityError

        email = email.lower().strip()

        if self._user_model.query.filter_by(email=email).first():
            raise RegistrationError(f"Email '{email}' is already registered.")

        user = self._user_model(
            first_name = first_name.strip(),
            last_name  = last_name.strip(),
            email      = email,
            is_admin   = False,   # never trust client-supplied is_admin
        )
        self._db.session.add(user)

        try:
            self._db.session.flush()
        except IntegrityError as exc:
            self._db.session.rollback()
            raise RegistrationError('Registration failed due to a data conflict.') from exc

        self._db.session.add(self._user_auth_model(user=user, password=password))

        try:
            self._db.session.commit()
        except IntegrityError as exc:
            self._db.session.rollback()
            raise RegistrationError('Registration failed. Please try again.') from exc

        # Trigger welcome email Celery task
        try:
            import importlib
            try:
                publisher_tasks = importlib.import_module('app.core.tasks.publisher_tasks')
                if hasattr(publisher_tasks, 'send_welcome_email_task'):
                    getattr(publisher_tasks, 'send_welcome_email_task').delay(user.email, user.first_name)
            except ImportError:
                # Silently skip if the application package isn't structured this way
                pass
        except Exception as exc:
            log.error('Failed to dispatch welcome email Celery task: %s', exc)

        log.info('New user registered: id=%s email=%s', user.id, email)
        return user

    def verify_access_token(self, token: str) -> Any | None:
        """Decode an access token and return the user, or ``None``."""
        try:
            payload = self._decode_token(token, self._access_secret)
        except TokenError:
            return None
        return self._db.session.get(self._user_model, int(payload['sub']))

    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Validate *refresh_token* and issue a new access token.

        :raises TokenError: on invalid or expired refresh token.
        """
        payload = self._decode_token(refresh_token, self._refresh_secret)
        user    = self._db.session.get(self._user_model, int(payload['sub']))

        if not user:
            raise TokenError('User not found for this refresh token.')

        return self._make_token(user.id, self._access_expires, self._access_secret)
