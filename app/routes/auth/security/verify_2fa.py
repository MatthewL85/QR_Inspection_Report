# 📍 app/routes/auth/two_factor/verify_2fa.py

from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_user
from app.extensions import db
from app.routes.auth import auth_bp
from app.forms.auth.two_factor_setup_form import TwoFactorSetupForm
import pyotp
from app.models import User
from datetime import datetime

@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    form = TwoFactorSetupForm()
    user_id = session.get('2fa_user_id')

    if not user_id:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)

    if not user or not user.two_factor_enabled:
        flash("Invalid user or 2FA not enabled.", "danger")
        return redirect(url_for('auth.login'))

    totp = pyotp.TOTP(user.two_factor_secret)

    if form.validate_on_submit():
        token = form.token.data

        if totp.verify(token, valid_window=1):
            login_user(user)
            session.pop('2fa_user_id', None)
            flash("🔐 2FA verification successful. Welcome!", "success")
            return redirect(url_for('super_admin.dashboard' if user.role_name == 'Super Admin' else 'auth.profile'))
        else:
            flash("❌ Invalid or expired 2FA code.", "danger")

    return render_template('auth/two_factor_verify.html', form=form)
