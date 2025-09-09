from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, FileField, SubmitField
from wtforms.validators import DataRequired, Optional, Email, Length
from flask_wtf.file import FileAllowed

class CompanyOnboardingForm(FlaskForm):
    # 🔖 Basic Identity
    name = StringField("Company Name", validators=[DataRequired(), Length(max=255)])
    registration_number = StringField("Company Registration Number", validators=[Optional(), Length(max=100)])
    vat_number = StringField("VAT Number", validators=[Optional(), Length(max=100)])
    tax_identifier = StringField("Tax Identifier", validators=[Optional(), Length(max=100)])
    company_type = SelectField(
        "Company Type",
        choices=[
            ("Property Management", "Property Management"),
            ("Contractor", "Contractor"),
            ("OMC", "OMC"),
            ("Director Group", "Director Group")
        ],
        validators=[DataRequired()]
    )
    industry = StringField("Industry", validators=[Optional(), Length(max=100)])

    # 🌍 Jurisdictional Details
    country = StringField("Country", validators=[DataRequired(), Length(max=100)])
    region = StringField("Region / State", validators=[Optional(), Length(max=100)])
    currency = StringField("Currency (ISO 4217)", default="EUR", validators=[Optional(), Length(max=10)])
    timezone = StringField("Timezone", default="Europe/Dublin", validators=[Optional(), Length(max=100)])
    preferred_language = StringField("Preferred Language", default="en", validators=[Optional(), Length(max=50)])

    # 📞 Contact Info
    email = StringField("Company Email", validators=[Optional(), Email(), Length(max=255)])
    phone = StringField("Company Phone", validators=[Optional(), Length(max=50)])
    website = StringField("Website", validators=[Optional(), Length(max=255)])

    # 🏢 Address Info
    address_line1 = StringField("Address Line 1", validators=[Optional(), Length(max=255)])
    address_line2 = StringField("Address Line 2", validators=[Optional(), Length(max=255)])
    city = StringField("City", validators=[Optional(), Length(max=100)])
    state = StringField("State", validators=[Optional(), Length(max=100)])
    postal_code = StringField("Postal Code", validators=[Optional(), Length(max=50)])

    # 🧾 Compliance & Branding
    data_protection_compliant = BooleanField("Data Protection Compliant (GDPR)")
    terms_agreed = BooleanField("I agree to the Terms of Service", validators=[DataRequired()])
    consent_to_communicate = BooleanField("Consent to receive communications")
    logo_path = FileField("Upload Company Logo", validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png'], "Images only!")])
    brand_color = StringField("Brand Color (HEX)", validators=[Optional(), Length(max=20)])

    submit = SubmitField("Complete Onboarding")
