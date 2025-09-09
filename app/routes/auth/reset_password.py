# 📍 app/routes/auth/reset_password.py

from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user
from werkzeug.security import generate_password_hash
from app.extensions import db, serializer
from app.forms.auth.reset_password_form import ResetPasswordForm
from app.models import User
from app.routes.auth import auth_bp


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    # 🚫 Prevent authenticated users from accessing this
    if current_user.is_authenticated:
        flash("You're already logged in.", "info")
        return redirect(url_for('super_admin.dashboard'))  # Adjust to dynamic redirect later

    try:
        # 🔐 Decode token — expires after 1 hour
        email = serializer.loads(token, salt='password-reset', max_age=3600)
    except Exception:
        flash('⚠️ This reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.filter_by(email=email).first_or_404()
    form = ResetPasswordForm()

    if form.validate_on_submit():
        user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()

        flash('✅ Your password has been reset successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form, token=token)
