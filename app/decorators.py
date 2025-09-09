# app/decorators.py

from functools import wraps
from flask import session, redirect, url_for, flash

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'Super Admin':
            flash("Access denied: Super Admins only", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
