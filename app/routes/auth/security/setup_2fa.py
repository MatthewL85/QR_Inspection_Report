# 📍 app/routes/auth/two_factor/setup_2fa.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
import pyotp, qrcode
from io import BytesIO
import base64
from app.extensions import db
from app.routes.auth import auth_bp
from app.forms.auth.two_factor_setup_form import TwoFactorSetupForm
from app.models.audit import ProfileChangeLog

# 🧠 Helper to log field changes
def log_change(user, field, old, new):
    if str(old) != str(new):
        db.session.add(ProfileChangeLog(
            user_id=user.id,
            changed_by=current_user.id,
            field_name=field,
            old_value=str(old),
            new_value=str(new)
        ))

# 📲 Setup 2FA with TOTP
@auth_bp.route('/setup-2fa', methods=['GET', 'POST'], endpoint='setup_2fa')
@login_required
def setup_2fa():
    form = TwoFactorSetupForm()

    # ✅ Generate secret if not already present
    if not current_user.two_factor_secret:
        secret = pyotp.random_base32()
        current_user.two_factor_secret = secret
        log_change(current_user, 'two_factor_secret', '[None]', '[Generated]')
        db.session.commit()
    else:
        secret = current_user.two_factor_secret

    # 🔐 Generate provisioning URI for Google Authenticator
    issuer_name = "LogixPM"
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name=issuer_name)

    # 🖼️ Generate QR Code as base64 image
    qr = qrcode.make(totp_uri)
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    if form.validate_on_submit():
        entered_token = form.token.data.strip()
        totp = pyotp.TOTP(secret)

        if totp.verify(entered_token):
            current_user.two_factor_enabled = True
            db.session.commit()
            flash("✅ Two-Factor Authentication is now enabled.", "success")
            return redirect(url_for('auth.profile'))
        else:
            flash("❌ Invalid token. Please try again.", "danger")

    return render_template('auth/two_factor/setup.html', form=form, qr_base64=qr_base64, secret=secret)