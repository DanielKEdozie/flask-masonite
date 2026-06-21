"""
flask_user.schemas
------------------
Marshmallow input schemas for the built-in auth views.

These are intentionally minimal.  Override any of them by passing a
subclass to :class:`~flask_user.views.AuthViews`.
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate


class LoginSchema(Schema):
    email    = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class RegisterSchema(Schema):
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    last_name  = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    email      = fields.Email(required=True)
    password   = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=6),
    )


class RefreshSchema(Schema):
    refresh_token = fields.Str(required=True)


class TokenSchema(Schema):
    """
    Output schema for login responses.

    ``user`` is merged into the response dict directly by the view
    using the caller-supplied ``user_schema``, so no nested field is
    declared here.
    """
    token         = fields.Str(dump_only=True)
    refresh_token = fields.Str(dump_only=True)
