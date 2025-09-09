# 📄 app/forms/client_compliance_form.py

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, DateField, BooleanField,
    TextAreaField, HiddenField, MultipleFileField
)
from wtforms.validators import DataRequired, Optional, Length

# 🗂️ Standardized document types – editable via admin in future
DOCUMENT_TYPE_CHOICES = [
    ('Fire Cert', 'Fire Cert'),
    ('Lift Inspection', 'Lift Inspection'),
    ('Insurance', 'Insurance'),
    ('Other', 'Other')
]

class ClientComplianceForm(FlaskForm):
    """
    📋 Form used to upload or edit Client Compliance Documents.
    Compatible with Flask-WTF + Material Dashboard + AI-ready compliance logic.
    """

    # 🔐 Optional hidden ID field (used for editing)
    document_id = HiddenField()

    # 🏢 Client selection
    client_id = SelectField(
        'Client',
        coerce=int,
        validators=[DataRequired(message='Please select a client.')]
    )

    # 📂 Type of document (future: make dynamic)
    document_type = SelectField(
        'Document Type',
        choices=DOCUMENT_TYPE_CHOICES,
        validators=[DataRequired(message='Please select a document type.')]
    )

    # 📅 Expiry tracking
    expires_at = DateField(
        'Expiry Date',
        format='%Y-%m-%d',
        validators=[DataRequired(message='Please enter an expiry date.')]
    )

    # 📎 File upload field – supports multiple files
    files = MultipleFileField(
        'Upload File(s)',
        validators=[Optional(message='Please upload at least one file.')]
    )

    # 📝 Optional description / notes
    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=1000)],
        render_kw={
            "rows": 3,
            "placeholder": "Optional document notes or description..."
        }
    )

    # 🔒 Indicates if this document is mandatory for work order creation
    is_required = BooleanField('Required for Work Orders')

    # 🤖 Used to flag manual AI review (optional)
    ai_reviewed = BooleanField('Mark as AI Reviewed')

    # 🗃️ Optional future enhancement:
    # status = SelectField(
    #     'Status',
    #     choices=[('active', 'Active'), ('archived', 'Archived')],
    #     validators=[Optional()]
    # )
