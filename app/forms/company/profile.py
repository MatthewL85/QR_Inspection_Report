from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TelField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, Email, URL, Regexp

COUNTRIES = [("Ireland","Ireland"), ("United Kingdom","United Kingdom"), ("Other","Other")]
LANGS = [("en","English"), ("ga","Irish"), ("fr","French")]
TIMEZONES = [("Europe/Dublin","Europe/Dublin"), ("Europe/London","Europe/London")]

class CompanyProfileForm(FlaskForm):
    name = StringField("Legal / Trading Name", validators=[DataRequired(), Length(max=255)])
    registration_number = StringField("Registration Number", validators=[Optional(), Length(max=100)])
    vat_number = StringField("VAT Number", validators=[Optional(), Length(max=100)])
    tax_identifier = StringField("Tax Identifier", validators=[Optional(), Length(max=100)])
    company_type = StringField("Company Type", validators=[Optional(), Length(max=100)])
    industry = StringField("Industry", validators=[Optional(), Length(max=100)])

    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    phone = TelField("Phone", validators=[Optional(), Length(max=50),
                        Regexp(r"^[0-9+()\-\s]{6,50}$", message="Use digits and + ( ) - only")])
    website = StringField("Website", validators=[Optional(), URL(require_tld=True), Length(max=255)])

    address_line1 = StringField("Address line 1", validators=[Optional(), Length(max=255)])
    address_line2 = StringField("Address line 2", validators=[Optional(), Length(max=255)])
    city = StringField("City / Town", validators=[Optional(), Length(max=100)])
    state = StringField("County / State", validators=[Optional(), Length(max=100)])
    postal_code = StringField("Postal Code", validators=[Optional(), Length(max=50)])
    country = SelectField("Country", choices=COUNTRIES, validators=[Optional()])

    currency = StringField("Currency (ISO 4217)", default="EUR", validators=[Optional(), Length(max=10)])
    timezone = SelectField("Timezone", choices=TIMEZONES, validators=[Optional()])
    preferred_language = SelectField("Preferred Language", choices=LANGS, validators=[Optional()])

    submit = SubmitField("Save")
    
