# 📍 app/routes/auth/email/verify_email.py

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.routes.auth import auth_bp
from app.extensions import db, serializer
from app.models import User
from datetime import datetime

# 📬 Email Verification Link
@auth_bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-verify', max_age=86400)  # 24 hours
    except Exception:
        flash("⚠️ Invalid or expired verification link.", "danger")
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("⚠️ Verification failed. User not found.", "danger")
        return redirect(url_for('auth.login'))

    if user.email_verified:
        flash("✅ Your email is already verified.", "info")
        return redirect(url_for('auth.login'))

    # ✅ Mark verified
    user.email_verified = True
    user.verified_at = datetime.utcnow()
    db.session.commit()

    flash("✅ Email verified! You can now log in.", "success")
    return redirect(url_for('auth.login'))
