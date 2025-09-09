# 📍 app/forms/super_admin/assign_fc_form.py

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class AssignFCForm(FlaskForm):
    """
    💰 Assign Financial Controller to Client or Company
    - Super Admin selects a financial controller and links them
    """

    financial_controller_id = SelectField(
        'Select Financial Controller',
        coerce=int,
        validators=[DataRequired()],
        render_kw={"class": "form-select"}
    )

    target_scope = SelectField(
        'Assign To',
        choices=[
            ('client', 'Client'),
            ('company', 'Management Company')
        ],
        validators=[DataRequired()],
        render_kw={"class": "form-select"}
    )

    target_id = SelectField(
        'Select Client or Company',
        coerce=int,
        validators=[DataRequired()],
        render_kw={"class": "form-select"}
    )

    submit = SubmitField('Assign Financial Controller', render_kw={"class": "btn btn-success w-100 mt-3"})
