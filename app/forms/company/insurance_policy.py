from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, DateField, DecimalField, SelectField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

POLICY_TYPES = [
    ("Public Liability","Public Liability"),
    ("Employers Liability","Employers Liability"),
    ("Professional Indemnity","Professional Indemnity"),
    ("Contractors All Risks","Contractors All Risks"),
]

class InsurancePolicyForm(FlaskForm):
    policy_type = SelectField("Policy Type", choices=POLICY_TYPES, validators=[DataRequired()])
    provider = StringField("Provider", validators=[Optional(), Length(max=255)])
    policy_number = StringField("Policy Number", validators=[Optional(), Length(max=100)])
    coverage_amount = DecimalField("Coverage Amount", validators=[Optional(), NumberRange(min=0)], places=2)
    currency = StringField("Currency", validators=[Optional(), Length(max=10)])
    start_date = DateField("Start Date", validators=[Optional()])
    expiry_date = DateField("Expiry Date", validators=[Optional()])
    is_default = BooleanField("Default for this type", default=False)
    active = BooleanField("Active", default=True)
    document_path = StringField("Document Path (optional)", validators=[Optional(), Length(max=255)])
