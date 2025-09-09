# 📍 app/routes/auth/security/two_factor.py

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.routes.auth import auth_bp
from app.extensions import db

@auth_bp.route('/security/two-factor', methods=['GET', 'POST'], endpoint='two_factor_settings')
@login_required
def two_factor_settings():
    if request.method == 'POST':
        enabled = request.form.get('enabled') == 'on'
        method = request.form.get('method', 'email')  # default to email

        current_user.two_factor_enabled = enabled
        current_user.two_factor_method = method
        db.session.commit()

        status = "enabled" if enabled else "disabled"
        flash(f"Two-factor authentication {status}.", "success")
        return redirect(url_for('auth.two_factor_settings'))

    return render_template('auth/security/two_factor_settings.html', user=current_user)
