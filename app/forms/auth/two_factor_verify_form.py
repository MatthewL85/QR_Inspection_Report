# 📍 app/forms/auth/two_factor_verify_form.py

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp


class TwoFactorVerifyForm(FlaskForm):
    """
    🔐 Two-Factor Verification Form
    - Used after password login to verify TOTP (e.g. Google Authenticator)
    - Styled for high usability on mobile and desktop
    - Future-ready for AI/GAR logging
    """

    token = StringField(
        'Authentication Code',
        render_kw={
            "placeholder": "Enter 6-digit code",
            "class": "form-control form-control-lg text-center",
            "autocomplete": "one-time-code",
            "maxlength": 6,
            "inputmode": "numeric"
        },
        validators=[
            DataRequired(message="Authentication code is required."),
            Length(min=6, max=6, message="Code must be 6 digits."),
            Regexp(r'^\d{6}$', message="Code must be 6 digits.")
        ]
    )

    submit = SubmitField(
        '✅ Verify Code',
        render_kw={"class": "btn btn-lg bg-gradient-success w-100 mt-3"}
    )
