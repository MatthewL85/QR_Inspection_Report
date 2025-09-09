from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional
from app.models.core.role import Role
from app.models.company import Company

class AddUserForm(FlaskForm):
    """👤 Form for adding new users by Super Admin."""

    # ─── 🧍 Identity ───────────────────────────────────────────────────
    full_name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=2, message="Full name must be at least 2 characters.")
    ])
    
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message="Enter a valid email address.")
    ])
    
    password = PasswordField('Temporary Password', validators=[
        DataRequired(),
        Length(min=6, message="Password must be at least 6 characters.")
    ])

    # ─── 🛡️ Role & Company ─────────────────────────────────────────────
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    company_id = SelectField('Company', coerce=int, validators=[DataRequired()])

    # ─── ✅ Submit ──────────────────────────────────────────────────────
    submit = SubmitField('Add User')

    def populate_choices(self):
        """Dynamically populate dropdowns from DB."""
        self.role_id.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.company_id.choices = [(c.id, c.name) for c in Company.query.order_by(Company.name).all()]
