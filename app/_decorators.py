# 📍 app/decorators.py

from functools import wraps
from flask import session, redirect, url_for, flash
from app.models.core.user import User
from app.models.core.role import Role
from app.models.core.permission import Permission  # <-- make sure you have this model

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'Super Admin':
            flash("Access denied: Super Admins only", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def has_permission(permission_name):
    """✅ Decorator to check if the current user has a specific permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                flash("Please log in first.", "warning")
                return redirect(url_for('auth.login'))

            user = User.query.get(user_id)
            if not user or not user.role:
                flash("Invalid user or role.", "danger")
                return redirect(url_for('auth.login'))

            # Permissions are expected to be stored per-role
            role_permissions = {p.name for p in user.role.permissions}
            if permission_name not in role_permissions:
                flash("🚫 You do not have permission to access this page.", "danger")
                return redirect(url_for('auth.login'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
