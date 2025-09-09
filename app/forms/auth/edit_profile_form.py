# 📍 app/forms/auth/edit_profile_form.py

from flask_wtf import FlaskForm
from wtforms import StringField, FileField, BooleanField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, EqualTo
from flask_wtf.file import FileAllowed


class EditProfileForm(FlaskForm):
    """
    👤 Profile Edit Form
    - Supports name, photo, optional password, and director sharing toggle
    """

    full_name = StringField(
        'Full Name',
        validators=[DataRequired(), Length(max=120)],
        render_kw={"placeholder": "Enter your full name", "class": "form-control"}
    )

    profile_photo = FileField(
        'Profile Photo',
        validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')],
        render_kw={"class": "form-control"}
    )

    share_with_directors = BooleanField('Share profile with assigned directors')

    new_password = PasswordField(
        'New Password',
        validators=[Optional(), Length(min=6)],
        render_kw={"placeholder": "Enter new password", "class": "form-control"}
    )

    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[EqualTo('new_password', message='Passwords must match')],
        render_kw={"placeholder": "Confirm password", "class": "form-control"}
    )

    submit = SubmitField('Update Profile', render_kw={"class": "btn btn-primary w-100 mt-3"})
