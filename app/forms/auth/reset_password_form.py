# 📍 app/forms/auth/reset_password_form.py

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length


class ResetPasswordForm(FlaskForm):
    """
    🔐 Reset Password Form
    - Used after token verification to set a new secure password
    - Includes UX validation + secure audit support for GAR/AI
    """

    password = PasswordField(
        'New Password',
        render_kw={
            "placeholder": "Enter a strong password",
            "class": "form-control form-control-lg",
            "autocomplete": "new-password"
        },
        validators=[
            DataRequired(message="Please enter a new password."),
            Length(min=8, message="Password must be at least 8 characters long.")
        ]
    )

    confirm_password = PasswordField(
        'Confirm New Password',
        render_kw={
            "placeholder": "Re-enter the new password",
            "class": "form-control form-control-lg",
            "autocomplete": "new-password"
        },
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo('password', message="Passwords must match.")
        ]
    )

    submit = SubmitField(
        '🔐 Reset Password',
        render_kw={
            "class": "btn btn-lg bg-gradient-success w-100 mt-3"
        }
    )
