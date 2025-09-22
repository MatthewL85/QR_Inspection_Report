# 📄 app/forms/super_admin/edit_user_form.py

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, PasswordField, SubmitField
)
from wtforms.validators import DataRequired, Email, Optional, Length
from app.models.core.role import Role
from app.models.onboarding.company import Company

class EditUserForm(FlaskForm):
    """👤 Form for editing an existing user within LogixPM."""

    # ─── 🧑‍💼 Identity Fields ───────────────────────────────
    full_name = StringField(
        'Full Name',
        validators=[DataRequired(), Length(min=2)],
        render_kw={"placeholder": "e.g., Sarah O'Connell"}
    )

    email = StringField(
        'Email Address',
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "e.g., sarah@example.com"}
    )

    password = PasswordField(
        'New Password (leave blank to keep current)',
        validators=[Optional(), Length(min=6)],
        render_kw={"placeholder": "Minimum 6 characters"}
    )

    # ─── 🔐 Role & Company ──────────────────────────────────
    role_id = SelectField(
        'System Role',
        coerce=int,
        validators=[DataRequired()],
        description="Select the user’s role (e.g., Property Manager, Contractor, Super Admin)"
    )

    company_id = SelectField(
        'Assigned Company',
        coerce=int,
        validators=[DataRequired()],
        description="Choose the company or contractor this user belongs to"
    )

    # ─── 💾 Submit ──────────────────────────────────────────
    submit = SubmitField('Save Changes')

    def populate_choices(self):
        """📥 Dynamically populate role and company dropdowns."""
        self.role_id.choices = [
            (role.id, role.name) for role in Role.query.order_by(Role.name).all()
        ]
        self.company_id.choices = [
            (company.id, company.name) for company in Company.query.order_by(Company.name).all()
        ]
