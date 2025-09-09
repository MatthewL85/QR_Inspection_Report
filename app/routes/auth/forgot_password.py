# 📍 app/routes/auth/forgot_password.py

from flask import render_template, request, flash, redirect, url_for
from app.forms.auth.forgot_password_form import ForgotPasswordForm
from app.models import User
from app.utils.email import send_reset_email
from app.routes.auth import auth_bp


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()

        if user:
            send_reset_email(user)
            flash("✅ If that email is registered, a reset link has been sent.", "success")
        else:
            # Same flash to avoid email enumeration
            flash("✅ If that email is registered, a reset link has been sent.", "success")

        return redirect(url_for('auth.reset_sent'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-sent', endpoint='reset_sent')
def reset_sent():
    return render_template('auth/reset_sent.html')
