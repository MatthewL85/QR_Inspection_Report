from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, DateField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length

STATUS = [("active","Active"), ("suspended","Suspended"), ("expired","Expired"), ("pending","Pending")]

class CompanyLicenseForm(FlaskForm):
    regulator_name = StringField("Regulator / Governing Body", validators=[DataRequired(), Length(max=255)])
    license_type = StringField("License Type", validators=[Optional(), Length(max=120)])
    license_number = StringField("License Number", validators=[DataRequired(), Length(max=120)])

    country = StringField("Country", validators=[DataRequired(), Length(max=100)])
    region = StringField("Region / County", validators=[Optional(), Length(max=100)])
    city = StringField("City", validators=[Optional(), Length(max=100)])

    status = SelectField("Status", choices=STATUS, validators=[DataRequired()], default="active")
    valid_from = DateField("Valid From", validators=[Optional()])
    expiry_date = DateField("Expiry Date", validators=[Optional()])
    is_default = BooleanField("Default for this jurisdiction", default=False)
    active = BooleanField("Active", default=True)

    scope_json = TextAreaField("Scope (JSON)", validators=[Optional(), Length(max=4000)])
    document_path = StringField("Document Path", validators=[Optional(), Length(max=255)])
