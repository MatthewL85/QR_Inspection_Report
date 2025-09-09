# 📍 app/forms/super_admin/assign_pm_form.py

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class AssignPMForm(FlaskForm):
    """
    📋 Assign Property Manager to Client
    - Super Admin selects a PM from dropdown and assigns to a selected client
    """

    property_manager_id = SelectField(
        'Select Property Manager',
        coerce=int,
        validators=[DataRequired()],
        render_kw={"class": "form-select"}
    )

    client_id = SelectField(
        'Select Client',
        coerce=int,
        validators=[DataRequired()],
        render_kw={"class": "form-select"}
    )

    submit = SubmitField('Assign Property Manager', render_kw={"class": "btn btn-primary w-100 mt-3"})
