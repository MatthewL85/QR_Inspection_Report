# 📍 app/forms/auth/login_form.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    # Accepts either email OR username
    identifier = StringField(
        'Email or Username',
        render_kw={"placeholder": "you@example.com or yourusername", "class": "form-control"},
        validators=[
            DataRequired(message="Email or Username is required."),
            Length(max=120, message="Must be 120 characters or fewer.")
        ]
    )

    password = PasswordField(
        'Password',
        render_kw={"placeholder": "Enter your password", "class": "form-control"},
        validators=[
            DataRequired(message="Password is required."),
            Length(min=6, max=128, message="Password must be between 6–128 characters.")
        ]
    )

    remember_me = BooleanField(
        'Remember Me',
        default=False,
        render_kw={"class": "form-check-input"}
    )

    submit = SubmitField(
        'Sign In',
        render_kw={"class": "btn btn-primary w-100 mt-3"}
    )
