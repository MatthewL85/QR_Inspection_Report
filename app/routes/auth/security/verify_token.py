# 📍 app/routes/auth/security/verify_token.py

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import pyotp
from app.routes.auth import auth_bp
from app.extensions import db

@auth_bp.route('/security/verify-2fa', methods=['GET', 'POST'], endpoint='verify_2fa_token')
@login_required
def verify_token():
    if request.method == 'POST':
        token = request.form.get('token')
        totp = pyotp.TOTP(current_user.two_factor_secret)

        if totp.verify(token):
            current_user.two_factor_enabled = True
            db.session.commit()
            flash("✅ Two-factor authentication is now active.", "success")
            return redirect(url_for('auth.two_factor_settings'))
        else:
            flash("❌ Invalid token. Try again.", "danger")

    return render_template('auth/security/verify_token.html')
