"""
flask_user.models
-----------------
Built-in ``User`` and ``UserAuth`` SQLAlchemy models.

Used automatically when you do not supply custom models to
:class:`~flask_user.FlaskUser`.  Both classes are built lazily via
:func:`init_models` so ``db`` is never imported at module level.

User fields
-----------
    id          Integer primary key.
    first_name  Required string (max 120).
    last_name   Required string (max 120).
    email       Required, unique, indexed.
    is_admin    Boolean flag, default False.
                Set to True to grant admin privileges.
                Use the ``flask user create-admin`` CLI command to create
                the first admin account without an existing session.
    created_at  Server-side timestamp set on insert.
    updated_at  Server-side timestamp updated on every write.

UserAuth design
---------------
- ``user_id`` is both the primary key and the foreign key to ``users.id``.
  A single column enforces the one-to-one constraint at the database level
  with no extra ``UNIQUE`` index required.
- ``password`` is a **write-only property**.  Reading raises ``AttributeError``
  so the bcrypt hash is never accidentally logged or serialised.
- The setter hashes the plain-text password immediately — it never touches
  the database in its raw form, even in tests.
"""
from __future__ import annotations
from flask_login import UserMixin

def init_models(db, bcrypt):
    """
    Build and return ``(User, UserAuth)`` model classes bound to *db*.

    Called once by :meth:`~flask_user.FlaskUser.init_app`.

    :param db:      Flask-SQLAlchemy ``SQLAlchemy`` instance.
    :param bcrypt:  Flask-Bcrypt ``Bcrypt`` instance.
    :returns:       ``(User, UserAuth)``
    """

    class User(db.Model, UserMixin):
        """Default user profile model."""

        __tablename__ = 'users'

        id         = db.Column(db.Integer, primary_key=True)
        first_name = db.Column(db.String(120), nullable=False)
        last_name  = db.Column(db.String(120), nullable=False)
        email      = db.Column(
            db.String(255),
            nullable = False,
            unique   = True,
            index    = True,
        )
        is_admin   = db.Column(db.Boolean, nullable=False, default=False)
        created_at = db.Column(db.DateTime, server_default=db.func.now())
        updated_at = db.Column(
            db.DateTime,
            server_default = db.func.now(),
            onupdate       = db.func.now(),
        )

        # One-to-one — access as ``user.auth``
        auth = db.relationship(
            'UserAuth',
            back_populates = 'user',
            uselist        = False,
            lazy           = 'joined',
            cascade        = 'all, delete-orphan',
        )
        

        @property
        def full_name(self) -> str:
            return f'{self.first_name} {self.last_name}'

        def __repr__(self) -> str:
            return (
                f'<User id={self.id} email={self.email}'
                f'{" [admin]" if self.is_admin else ""}>'
            )

    class UserAuth(db.Model):
        """
        Stores hashed credentials for a ``User``.

        ``user_id`` is both the primary key and the foreign key so the
        database enforces the one-to-one relationship without an extra
        ``UNIQUE`` constraint.
        """

        __tablename__ = 'user_auth'

        user_id = db.Column(
            db.Integer,
            db.ForeignKey('users.id', ondelete='CASCADE'),
            primary_key = True,
            nullable    = False,
        )
        _password = db.Column('password', db.String(255), nullable=False)

        user = db.relationship('User', back_populates='auth')

        def __init__(self, user: User, password: str) -> None:
            """
            :param user:     Related ``User`` instance.
            :param password: Plain-text password — hashed immediately.
            """
            self.user     = user
            self.password = password   # triggers the setter

        # ── Password ──────────────────────────────────────────────────────────

        @property
        def password(self) -> str:
            """Write-only.  Use :meth:`verify_password` instead."""
            raise AttributeError(
                'UserAuth.password is write-only. '
                'Call verify_password() to check credentials.'
            )

        @password.setter
        def password(self, plain_text: str) -> None:
            """Hash *plain_text* with bcrypt and store the result."""
            self._password = bcrypt.generate_password_hash(
                plain_text
            ).decode('utf-8')

        def verify_password(self, plain_text: str) -> bool:
            """Return ``True`` when *plain_text* matches the stored hash."""
            return bcrypt.check_password_hash(self._password, plain_text)

        def __repr__(self) -> str:
            return f'<UserAuth user_id={self.user_id}>'

    return User, UserAuth
