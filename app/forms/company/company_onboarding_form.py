# app/forms/company/company_onboarding_form.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, SubmitField, FileField
)
from wtforms.validators import DataRequired, Optional, Email, Length, URL, Regexp

# You can tweak these lists centrally if you like
COUNTRY_CHOICES = [
    ("Ireland", "Ireland"),
    ("United Kingdom", "United Kingdom"),
    ("United States", "United States"),
    ("Other", "Other"),
]

COMPANY_TYPE_CHOICES = [
    ("", "Select…"),
    ("management", "Management"),
    ("contractor", "Contractor"),
    ("omc", "OMC / Director"),
]


class CompanyOnboardingForm(FlaskForm):
    """
    Step 1 (Company Details) — uses the SAME field names as your Settings form
    so data stays consistent and templates look/behave the same.
    """
    # Core identity
    name = StringField("Company Name", validators=[DataRequired(message="Company name is required."), Length(max=255)])
    registration_number = StringField("Registration Number", validators=[Optional(), Length(max=128)])
    vat_number = StringField("VAT Number", validators=[Optional(), Length(max=50)])
    tax_identifier = StringField("Tax Identifier", validators=[Optional(), Length(max=50)])

    company_type = SelectField("Company Type", choices=COMPANY_TYPE_CHOICES, validators=[Optional()])
    industry = StringField("Industry", validators=[Optional(), Length(max=128)])

    # Contacts
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    phone = StringField("Phone", validators=[Optional(), Length(max=64)])
    website = StringField("Website", validators=[Optional(), URL(require_tld=False), Length(max=255)])

    # Address
    address_line1 = StringField("Address Line 1", validators=[Optional(), Length(max=255)])
    address_line2 = StringField("Address Line 2", validators=[Optional(), Length(max=255)])
    city = StringField("City", validators=[Optional(), Length(max=120)])
    state = StringField("State / Region", validators=[Optional(), Length(max=120)])
    postal_code = StringField("Postal Code", validators=[Optional(), Length(max=32)])
    country = SelectField("Country", choices=COUNTRY_CHOICES, validators=[Optional()])

    # Locale / prefs
    currency = StringField("Currency", validators=[Optional(), Length(max=8), Regexp(r"^[A-Za-z]{0,8}$", message="Use an ISO code like EUR or GBP")])
    timezone = StringField("Timezone", validators=[Optional(), Length(max=64)])
    preferred_language = StringField("Preferred Language", validators=[Optional(), Length(max=16)])

    submit = SubmitField("Save & Continue")


class CompanyBrandingForm(FlaskForm):
    """
    Step 2 (Branding) — uses your existing model columns.
    Keep this if you want CSRF/validation on branding too.
    """
    brand_primary_color = StringField("Primary Color (hex)", validators=[Optional(), Regexp(r"^#?[0-9A-Fa-f]{3,8}$", message="Enter a hex color like #1976d2")])
    brand_secondary_color = StringField("Secondary Color (hex)", validators=[Optional(), Regexp(r"^#?[0-9A-Fa-f]{3,8}$", message="Enter a hex color like #e91e63")])
    brand_color = StringField("Legacy Brand Color (hex)", validators=[Optional(), Regexp(r"^#?[0-9A-Fa-f]{3,8}$", message="Enter a hex color like #4caf50")])
    # If you use Flask-Uploads/WTForms-Alchemy/FileAllowed, add validators here
    logo_file = FileField("Logo")  # validators=[Optional(), FileAllowed(['jpg','jpeg','png','gif'], 'Images only!')]
    submit = SubmitField("Save & Continue")
