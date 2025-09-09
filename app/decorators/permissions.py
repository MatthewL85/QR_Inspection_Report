from functools import wraps
from flask import session, redirect, url_for, flash
from app.models.core.role import Role
from app.models.core.role_permissions import RolePermission


def has_permission(required_permission):
    """
    🔐 Decorator to enforce role-based permission access.

    - Grants full access to Super Admins
    - Checks RolePermission table for explicit permission match
    - Redirects to login with appropriate flash message if unauthorized
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            role_name = session.get('role')

            if not role_name:
                flash("⚠️ Access denied: Not logged in", "danger")
                return redirect(url_for('auth.login'))

            # 🔓 Super Admin bypasses all checks
            if role_name == 'Super Admin':
                return f(*args, **kwargs)

            role = Role.query.filter_by(name=role_name).first()
            if not role:
                flash("⚠️ Access denied: Role not found", "danger")
                return redirect(url_for('auth.login'))

            has_perm = RolePermission.query.filter_by(
                role_id=role.id,
                permission=required_permission
            ).first()

            if not has_perm:
                flash(f"⛔ Access denied: Missing permission '{required_permission}'", "danger")
                return redirect(url_for('auth.login'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
