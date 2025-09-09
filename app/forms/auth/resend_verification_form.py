# 📍 app/forms/auth/resend_verification_form.py

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class ResendVerificationForm(FlaskForm):
    """
    🔁 Resend Email Verification Form
    - Allows user to request a new verification link
    """

    email = StringField(
        'Email',
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Please enter a valid email address."),
            Length(max=120)
        ],
        render_kw={
            "placeholder": "Enter your email to resend link",
            "class": "form-control"
        }
    )

    submit = SubmitField('Resend Verification Email', render_kw={"class": "btn btn-warning w-100 mt-3"})
