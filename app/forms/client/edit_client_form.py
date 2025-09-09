from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, BooleanField, SelectField,
    SelectMultipleField, DecimalField, IntegerField, DateField,
    FileField, SubmitField, HiddenField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from flask_wtf.file import FileAllowed

class EditClientForm(FlaskForm):
    """🧾 Form for editing existing client entities in LogixPM."""

    # 🔐 Internal Use
    client_id = HiddenField()

    # ─── 🔧 Core Identity ───────────────────────────────────────────────
    name = StringField('Client Name', validators=[DataRequired()])
    property_name = StringField('Property Name', validators=[DataRequired(), Length(max=255)])
    address_line1 = StringField('Address Line 1', validators=[DataRequired(), Length(max=255)])
    address_line2 = StringField('Address Line 2', validators=[Optional(), Length(max=255)])
    city         = StringField('City/Town',        validators=[Optional(), Length(max=128)])
    postal_code = StringField('Postal Code')
    registration_number = StringField('Registration Number')
    vat_reg_number = StringField('VAT Registration Number')
    tax_number = StringField('Tax Number')
    year_of_construction = StringField('Year of Construction', validators=[Optional(), Length(max=10)])
    number_of_units = IntegerField('Number of Units', validators=[Optional(), NumberRange(min=0)])
    contract_value = DecimalField('Contract Value (€)', validators=[Optional()], places=2)

    # ─── 📅 Governance Info ─────────────────────────────────────────────
    client_type = SelectField('Client Type', choices=[], validators=[Optional()])

    financial_year_end = DateField('Financial Year End', format='%Y-%m-%d', validators=[Optional()])
    last_agm_date = DateField('Last AGM Date', format='%Y-%m-%d', validators=[Optional()])
    agm_completed = BooleanField('AGM Completed?')

    # ─── 🌍 Jurisdictional Details ──────────────────────────────────────
    country = StringField('Country')
    region = StringField('Region')
    currency = StringField('Currency')
    timezone = StringField('Timezone')
    preferred_language = StringField('Preferred Language')
    ownership_type = StringField('Ownership Type')

    # ─── 🛡️ Legal & Compliance ──────────────────────────────────────────
    transfer_of_common_area = BooleanField('Transfer of Common Area?')
    deed_of_covenants = StringField('Deed of Covenants')
    data_protection_compliance = StringField('Data Protection Compliance Notes')
    consent_to_communicate = BooleanField('Consent to Communicate?')
    enforce_gdpr = BooleanField('Enforce GDPR?')

    # ─── 🏢 Block Configuration ─────────────────────────────────────────
    min_directors = IntegerField('Min Directors', validators=[Optional(), NumberRange(min=0)])
    max_directors = IntegerField('Max Directors', validators=[Optional(), NumberRange(min=0)])
    number_of_blocks = IntegerField('Number of Blocks', validators=[Optional(), NumberRange(min=0)])
    block_names = StringField('Block Names (comma-separated)')
    cores_per_block = StringField('Cores per Block (comma-separated)')
    apartments_per_block = StringField('Apartments per Block (comma-separated)')

    # ─── 👥 Assignments ─────────────────────────────────────────────────
    assigned_pm_id = SelectField('Assigned Property Manager', coerce=int, validators=[Optional()])
    assigned_fc_id = SelectField('Assigned Financial Controller', coerce=int, validators=[Optional()])
    assigned_assistant_id = SelectField('Assigned Assistant PM', coerce=int, validators=[Optional()])

    # ─── 📎 Contract Upload ─────────────────────────────────────────────
    document_file = FileField('Replace Contract Document (PDF)', validators=[
        Optional(),
        FileAllowed(['pdf'], 'PDFs only.')
    ])

    # ─── 🧠 AI Metadata ─────────────────────────────────────────────────
    ownership_types = SelectMultipleField('Ownership Types', choices=[
        ('Freehold', 'Freehold'),
        ('Leasehold', 'Leasehold'),
        ('Share of Freehold', 'Share of Freehold')
    ])
    ai_key_clauses = TextAreaField('AI Key Clauses (JSON Format)', validators=[Optional()])
    capex_profile = StringField('CAPEX Profile')
    tags = StringField('Tags / Keywords')

    ai_governance_summary = TextAreaField('AI Governance Summary', validators=[Optional()])
    ai_flagged_risks = TextAreaField('AI Flagged Risks', validators=[Optional()])
    ai_advice_summary = TextAreaField('AI Advice Summary', validators=[Optional()])
    ai_review_comment = TextAreaField('AI Review Comment', validators=[Optional()])

    # ─── 🌐 GAR Fields ─────────────────────────────────────────────────
    is_gar_monitored = BooleanField('Enable GAR Monitoring?')
    gar_chat_ready = BooleanField('GAR Chat Ready?')
    gar_resolution_status = SelectField('GAR Status', choices=[
        ('Open', 'Open'),
        ('Resolved', 'Resolved'),
        ('Escalated', 'Escalated')
    ], validators=[Optional()])

    # ─── 🔘 Submit ──────────────────────────────────────────────────────
    submit = SubmitField('Update Client')
