"""
flask_user.user_schema
-----------------------
Default ``UserSchema`` factory for the built-in ``User`` model.

Built automatically when no ``user_schema`` is passed to
:meth:`~flask_user.FlaskUser.init_app`.

Fields serialised: ``id``, ``email``, ``first_name``, ``last_name``,
``full_name``, ``is_admin``, ``created_at``.

The ``auth`` relationship is always excluded.
"""
from __future__ import annotations


def build_user_schema(ma, User):
    """
    Return a ``UserSchema`` class introspected from *User* via *ma*.

    :param ma:   Flask-Marshmallow ``Marshmallow`` instance.
    :param User: The ``User`` model class.
    :returns:    A ``SQLAlchemyAutoSchema`` subclass.
    """

    class UserSchema(ma.SQLAlchemyAutoSchema):

        class Meta:
            model         = User
            load_instance = True
            exclude       = ('auth',)
            dump_only     = ('id', 'is_admin', 'created_at', 'updated_at')

        full_name = ma.Method('get_full_name', dump_only=True)

        def get_full_name(self, obj) -> str:
            return obj.full_name

    return UserSchema
