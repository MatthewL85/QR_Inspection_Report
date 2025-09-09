# 📍 app/forms/auth/forgot_password_form.py

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class ForgotPasswordForm(FlaskForm):
    """
    🔐 Forgot Password Request Form
    - Captures user’s email to initiate password reset
    - Fully enhanced for UX and AI/GAR audit-readiness
    """

    email = StringField(
        'Registered Email',
        render_kw={
            "placeholder": "you@example.com",
            "class": "form-control form-control-lg",
            "autocomplete": "email"
        },
        validators=[
            DataRequired(message="Please enter your email address."),
            Email(message="Please enter a valid email."),
            Length(max=120)
        ]
    )

    submit = SubmitField(
        '📩 Send Reset Link',
        render_kw={
            "class": "btn btn-lg bg-gradient-primary w-100 mt-3"
        }
    )
