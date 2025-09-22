from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField
from wtforms.validators import DataRequired, Optional, Length, Regexp, Email

CURRENCIES = [("EUR","EUR"), ("GBP","GBP"), ("USD","USD")]

class BankAccountForm(FlaskForm):
    nickname = StringField("Nickname", validators=[Optional(), Length(max=64)])
    account_name = StringField("Account Name", validators=[Optional(), Length(max=255)])
    bank_name = StringField("Bank Name", validators=[Optional(), Length(max=255)])

    iban = StringField("IBAN", validators=[Optional(), Length(max=34),
                                           Regexp(r"^[A-Z0-9 ]{8,34}$", message="Invalid IBAN characters")])
    bic_swift = StringField("BIC/SWIFT", validators=[Optional(), Length(max=11),
                                                    Regexp(r"^[A-Za-z0-9]{8,11}$", message="Invalid BIC/SWIFT")])
    remittance_email = StringField("Remittance Email", validators=[Optional(), Email(), Length(max=255)])

    currency = SelectField("Currency", choices=CURRENCIES, validators=[Optional()])
    account_type = StringField("Account Type", validators=[Optional(), Length(max=50)])  # e.g., operating
    active = BooleanField("Active", default=True)
    is_default = BooleanField("Default for this company", default=False)
