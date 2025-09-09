# 📍 app/forms/auth/two_factor_setup_form.py

from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp


class TwoFactorSetupForm(FlaskForm):
    """
    🛡️ Two-Factor Authentication Setup Form
    - Used to activate or deactivate 2FA using TOTP (e.g. Google Authenticator)
    - Token confirms that user scanned QR and can authenticate
    """

    token = StringField(
        'Verify TOTP Code',
        render_kw={
            "placeholder": "Enter the 6-digit code from your app",
            "class": "form-control form-control-lg text-center",
            "autocomplete": "one-time-code",
            "maxlength": 6,
            "inputmode": "numeric"
        },
        validators=[
            DataRequired(message="Code is required to complete setup."),
            Length(min=6, max=6, message="Must be a 6-digit code."),
            Regexp(r'^\d{6}$', message="Invalid code format.")
        ]
    )

    enable_2fa = BooleanField(
        'Enable Two-Factor Authentication',
        render_kw={"class": "form-check-input"}
    )

    submit = SubmitField(
        '🔒 Save 2FA Settings',
        render_kw={"class": "btn btn-lg bg-gradient-primary w-100 mt-3"}
    )
