# 📍 app/forms/super_admin/assign_assistant_form.py

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class AssignAssistantForm(FlaskForm):
    """
    🧰 Assign Assistant to Client
    - Super Admin selects an Assistant and assigns to a selected client
    """

    assistant_id = SelectField(
        'Select Assistant',
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

    submit = SubmitField('Assign Assistant', render_kw={"class": "btn btn-secondary w-100 mt-3"})
