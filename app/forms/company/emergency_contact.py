from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, BooleanField, IntegerField,
    TimeField, DateField, TextAreaField
)
from wtforms.validators import DataRequired, Optional, Length, Email, NumberRange

COVERAGE_CHOICES = [
    ("24x7", "24×7"),
    ("weeknights", "Weeknights"),
    ("weekends", "Weekends"),
    ("holidays", "Holidays"),
    ("custom", "Custom"),
]

class EmergencyContactForm(FlaskForm):
    label = StringField("Label", validators=[DataRequired(), Length(max=120)])
    provider = StringField("Provider", validators=[Optional(), Length(max=255)])
    service_type = StringField("Service", validators=[Optional(), Length(max=120)])

    phone = StringField("Phone", validators=[DataRequired(), Length(max=50)])
    alt_phone = StringField("Alt Phone", validators=[Optional(), Length(max=50)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])

    coverage = SelectField("Coverage", choices=COVERAGE_CHOICES, validators=[DataRequired()])
    days_of_week = StringField("Days (custom, 0=Mon..6=Sun)", validators=[Optional(), Length(max=20)])
    start_time = TimeField("Start Time", validators=[Optional()])
    end_time = TimeField("End Time", validators=[Optional()])

    priority = IntegerField("Priority (1=first)", validators=[NumberRange(min=1)], default=1)
    active = BooleanField("Active", default=True)
    is_default = BooleanField("Default for this service", default=False)

    valid_from = DateField("Valid From", validators=[Optional()])
    valid_to = DateField("Valid To", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=2000)])
