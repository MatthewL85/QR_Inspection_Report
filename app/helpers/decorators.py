from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(role=None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            user = session.get('user')
            if not user:
                flash('Login required.', 'warning')
                return redirect(url_for('auth.login'))

            if role and user.get('role', '').lower() != role.lower():
                flash('Access denied: Insufficient role.', 'danger')
                return redirect(url_for('auth.login'))

            return view_func(*args, **kwargs)
        return wrapped_view
    return decorator
