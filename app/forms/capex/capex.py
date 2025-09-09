# app/forms/capex.py
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, SelectField, TextAreaField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange

PRIORITY_CHOICES = [("High","High"),("Medium","Medium"),("Low","Low")]
FUNDING_CHOICES  = [("Reserve Fund","Reserve Fund"),("Special Levy","Special Levy"),("Insurance","Insurance"),("Other","Other")]
STATUS_CHOICES   = [("Planned","Planned"),("Approved","Approved"),("In Tender","In Tender"),
                    ("In Progress","In Progress"),("Done","Done"),("Deferred","Deferred")]

class CapexProjectForm(FlaskForm):
    id = HiddenField()  # UUID; blank => new
    name = StringField("Project Name", validators=[DataRequired()])
    target_year = IntegerField("Target Year", validators=[Optional(), NumberRange(min=1900, max=2100)])
    cost = DecimalField("Estimated Cost", validators=[Optional(), NumberRange(min=0)], places=2)
    priority = SelectField("Priority", choices=PRIORITY_CHOICES, default="Medium")
    funding = SelectField("Funding Source", choices=FUNDING_CHOICES, default="Reserve Fund")
    status = SelectField("Status", choices=STATUS_CHOICES, default="Planned")
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save")
