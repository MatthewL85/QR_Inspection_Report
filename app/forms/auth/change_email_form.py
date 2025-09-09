# 📍 app/forms/auth/change_email_form.py

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class ChangeEmailForm(FlaskForm):
    """
    ✉️ Super Admin Email Change Form
    - Allows Super Admin to change their account email address
    """

    new_email = StringField(
        'New Email Address',
        validators=[
            DataRequired(message="Please enter a new email address."),
            Email(message="Enter a valid email address."),
            Length(max=120)
        ],
        render_kw={
            "placeholder": "Enter new email",
            "class": "form-control"
        }
    )

    submit = SubmitField('Update Email', render_kw={"class": "btn btn-secondary w-100 mt-3"})
