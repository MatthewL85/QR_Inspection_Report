from functools import wraps
from flask import redirect, url_for, session, flash

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session.get('role') != 'Super Admin':
            flash('Access denied: Super Admins only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
