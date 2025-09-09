# 📍 app/forms/super_admin/assign_admin_form.py

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class AssignAdminForm(FlaskForm):
    """
    🛡️ Assign Admin to Management Company
    - Super Admin assigns an admin to a selected company
    """

    admin_id = SelectField(
        'Select Admin',
        coerce=int,
        validators=[DataRequired()],
        render_kw={"class": "form-select"}
    )

    company_id = SelectField(
        'Select Management Company',
        coerce=int,
        validators=[DataRequired()],
        render_kw={"class": "form-select"}
    )

    submit = SubmitField('Assign Admin', render_kw={"class": "btn btn-dark w-100 mt-3"})
