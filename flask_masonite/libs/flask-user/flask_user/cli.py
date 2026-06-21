"""
flask_user.cli
--------------
Flask CLI commands registered under the ``user`` group.

Commands
--------
    flask user create-admin     Create or promote a user to admin.
    flask user list             List all users.
    flask user delete           Delete a user by email.
    flask user set-password     Reset a user's password.

All commands require the Flask app context (i.e. run inside a project
with ``FLASK_APP`` set).  They retrieve the active models and ``db``
from ``app.extensions['flask_user']``.
"""
from __future__ import annotations

import sys

import click
from flask import current_app
from flask.cli import AppGroup

user_cli = AppGroup('user', help='Manage application users.')


def _get_ext():
    """Return the FlaskUser extension registered on the current app."""
    ext = current_app.extensions.get('flask_user')
    if ext is None:
        click.echo(
            'Error: FlaskUser is not initialised on this app.\n'
            'Make sure FLASK_APP points to your app factory.',
            err=True,
        )
        sys.exit(1)
    return ext


# ── create-admin ───────────────────────────────────────────────────────────────

@user_cli.command('create-admin')
@click.option('--email',      prompt=True,              help='Admin email address.')
@click.option('--first-name', prompt=True,              help='First name.')
@click.option('--last-name',  prompt=True,              help='Last name.')
@click.option('--password',   prompt=True, hide_input=True,
              confirmation_prompt=True,                  help='Password (hidden).')
def create_admin(email, first_name, last_name, password):
    """
    Create a new admin user or promote an existing one.

    If a user with the given email already exists their ``is_admin`` flag
    is set to ``True`` and their password is updated.  If no user exists
    a new account is created with ``is_admin=True``.

    Example::

        flask user create-admin
        flask user create-admin --email admin@example.com --first-name Jane \\
            --last-name Doe --password secret
    """
    ext  = _get_ext()
    db   = ext.db
    User = ext.User
    UserAuth = ext.UserAuth

    email = email.lower().strip()
    existing = User.query.filter_by(email=email).first()

    if existing:
        existing.is_admin = True
        if existing.auth:
            existing.auth.password = password   # re-hash via setter
        else:
            db.session.add(UserAuth(user=existing, password=password))
        db.session.commit()
        click.echo(
            f"✓ Existing user '{email}' promoted to admin and password updated."
        )
    else:
        user = User(
            first_name = first_name.strip(),
            last_name  = last_name.strip(),
            email      = email,
            is_admin   = True,
        )
        db.session.add(user)
        db.session.flush()
        db.session.add(UserAuth(user=user, password=password))
        db.session.commit()
        click.echo(f"✓ Admin user '{email}' created (id={user.id}).")


# ── list ───────────────────────────────────────────────────────────────────────

@user_cli.command('list')
@click.option('--admin-only', is_flag=True, default=False,
              help='Show only admin accounts.')
def list_users(admin_only):
    """
    Print a table of all users.

    Example::

        flask user list
        flask user list --admin-only
    """
    ext  = _get_ext()
    User = ext.User

    query = User.query
    if admin_only:
        query = query.filter_by(is_admin=True)

    users = query.order_by(User.id).all()

    if not users:
        click.echo('No users found.')
        return

    header = f"{'ID':<6} {'EMAIL':<35} {'NAME':<25} {'ADMIN':<6} {'CREATED'}"
    click.echo(header)
    click.echo('-' * len(header))
    for u in users:
        created = u.created_at.strftime('%Y-%m-%d') if u.created_at else 'n/a'
        click.echo(
            f"{u.id:<6} {u.email:<35} {u.full_name:<25} "
            f"{'yes' if u.is_admin else 'no':<6} {created}"
        )


# ── delete ─────────────────────────────────────────────────────────────────────

@user_cli.command('delete')
@click.argument('email')
@click.option('--yes', is_flag=True, default=False,
              help='Skip confirmation prompt.')
def delete_user(email, yes):
    """
    Delete a user account by EMAIL.

    Also deletes their UserAuth record (cascade).

    Example::

        flask user delete jane@example.com
        flask user delete jane@example.com --yes
    """
    ext  = _get_ext()
    db   = ext.db
    User = ext.User

    user = User.query.filter_by(email=email.lower().strip()).first()
    if not user:
        click.echo(f"Error: no user found with email '{email}'.", err=True)
        sys.exit(1)

    if not yes:
        click.confirm(
            f"Delete user '{user.email}' (id={user.id})? This cannot be undone.",
            abort=True,
        )

    db.session.delete(user)
    db.session.commit()
    click.echo(f"✓ User '{email}' deleted.")


# ── set-password ───────────────────────────────────────────────────────────────

@user_cli.command('set-password')
@click.argument('email')
@click.option('--password', prompt=True, hide_input=True,
              confirmation_prompt=True, help='New password (hidden).')
def set_password(email, password):
    """
    Reset the password for a user identified by EMAIL.

    Example::

        flask user set-password jane@example.com
    """
    ext  = _get_ext()
    db   = ext.db
    User = ext.User

    user = User.query.filter_by(email=email.lower().strip()).first()
    if not user:
        click.echo(f"Error: no user found with email '{email}'.", err=True)
        sys.exit(1)

    if not user.auth:
        click.echo(f"Error: user '{email}' has no auth record.", err=True)
        sys.exit(1)

    user.auth.password = password   # re-hash via setter
    db.session.commit()
    click.echo(f"✓ Password updated for '{email}'.")
