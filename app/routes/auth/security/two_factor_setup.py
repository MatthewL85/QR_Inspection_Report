# 📍 app/routes/auth/security/two_factor_setup.py

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import pyotp, qrcode
import io
import base64
from app.routes.auth import auth_bp
from app.extensions import db

@auth_bp.route('/security/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_two_factor():
    if not current_user.two_factor_secret:
        # Generate and store new secret
        secret = pyotp.random_base32()
        current_user.two_factor_secret = secret
        db.session.commit()
    else:
        secret = current_user.two_factor_secret

    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=current_user.email, issuer_name="LogixPM")

    # 🔳 Generate QR Code
    qr_img = qrcode.make(provisioning_uri)
    buffered = io.BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_code_b64 = base64.b64encode(buffered.getvalue()).decode()

    return render_template(
        'auth/security/setup_two_factor.html',
        qr_code_b64=qr_code_b64,
        secret=secret
    )
