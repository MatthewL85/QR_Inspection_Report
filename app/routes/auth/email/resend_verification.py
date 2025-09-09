# 📍 app/routes/auth/email/resend_verification.py

from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from app.routes.auth import auth_bp
from app.extensions import serializer
from app.utils.email import send_email
from datetime import datetime

@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
@login_required
def resend_verification():
    # ⛔ Block if already verified
    if current_user.email_verified:
        flash("✅ Your email is already verified.", "info")
        return redirect(url_for('auth.profile'))

    if request.method == 'POST':
        # 🔐 Generate secure verification token
        token = serializer.dumps(current_user.email, salt='email-verify')
        verify_url = url_for('auth.verify_email', token=token, _external=True)

        # 📬 Send verification email
        send_email(
            to=current_user.email,
            subject="Please Verify Your LogixPM Email",
            template="email/security/verify_email.html",
            context={
                "user": current_user,
                "verify_url": verify_url,
                "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                "ip_address": request.remote_addr,
                "user_agent": request.headers.get("User-Agent"),
            }
        )

        flash("📨 Verification link resent! Please check your inbox.", "success")
        return redirect(url_for('auth.profile'))

    return render_template('auth/resend_verification.html')
