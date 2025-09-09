# 📍 app/routes/auth/profile/change_password.py

from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from app.extensions import db
from app.routes.auth import auth_bp
from app.forms.auth.change_password_form import ChangePasswordForm
from app.models.audit import PasswordChangeLog
from app.utils.email import send_email
from datetime import datetime


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # ❌ Current password check
        if not check_password_hash(current_user.password_hash, form.current_password.data):
            flash('❌ Current password is incorrect.', 'danger')
            return render_template('auth/change_password.html', form=form)

        # ⚠️ Prevent reusing same password
        if check_password_hash(current_user.password_hash, form.new_password.data):
            flash('⚠️ New password must be different from the current one.', 'warning')
            return render_template('auth/change_password.html', form=form)

        # ✅ Update password
        current_user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()

        # 🛡️ Log audit
        db.session.add(PasswordChangeLog(
            user_id=current_user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            change_type='manual',
            notes='Password changed via profile'
        ))
        db.session.commit()

        # 📧 Notify user
        send_email(
            to=current_user.email,
            subject="🔐 Your LogixPM Password Was Changed",
            template="email/security/password_changed.html",
            context={
                "user": current_user,
                "ip_address": request.remote_addr,
                "user_agent": request.headers.get("User-Agent"),
                "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            }
        )

        flash('✅ Your password has been updated.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/change_password.html', form=form)
