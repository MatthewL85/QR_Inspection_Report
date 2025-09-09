# 📍 app/forms/auth/change_password_form.py

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length


class ChangePasswordForm(FlaskForm):
    """
    🔐 Change Password Form
    - Used from within authenticated profile settings
    - Includes secure UX, strong validation, and audit-ready labels
    """

    current_password = PasswordField(
        'Current Password',
        render_kw={
            "placeholder": "Enter current password",
            "class": "form-control form-control-lg",
            "autocomplete": "current-password"
        },
        validators=[
            DataRequired(message="Please enter your current password.")
        ]
    )

    new_password = PasswordField(
        'New Password',
        render_kw={
            "placeholder": "Enter a new secure password",
            "class": "form-control form-control-lg",
            "autocomplete": "new-password"
        },
        validators=[
            DataRequired(message="Please enter a new password."),
            Length(min=8, message="Password must be at least 8 characters long.")
        ]
    )

    confirm_new_password = PasswordField(
        'Confirm New Password',
        render_kw={
            "placeholder": "Re-enter the new password",
            "class": "form-control form-control-lg",
            "autocomplete": "new-password"
        },
        validators=[
            DataRequired(message="Please confirm your new password."),
            EqualTo('new_password', message="Passwords must match.")
        ]
    )

    submit = SubmitField(
        '🔐 Update Password',
        render_kw={"class": "btn btn-lg bg-gradient-primary w-100 mt-3"}
    )

