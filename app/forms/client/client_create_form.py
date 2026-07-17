from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, BooleanField, SelectField, SelectMultipleField,
    DecimalField, IntegerField, DateField, SubmitField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
import json
from flask_wtf.file import FileField, FileAllowed

# 🔎 JSON validation helper
def validate_json(form, field):
    if field.data:
        try:
            json.loads(field.data)
        except ValueError:
            raise ValidationError("Invalid JSON format.")

class ClientCreateForm(FlaskForm):
    # 🔧 Core Info
    name = StringField('Client Name', validators=[DataRequired()])
    property_name = StringField('Property Name', validators=[DataRequired(), Length(max=255)])
    address_line1 = StringField('Address Line 1', validators=[DataRequired(), Length(max=255)])
    address_line2 = StringField('Address Line 2', validators=[Optional(), Length(max=255)])
    city         = StringField('City/Town',        validators=[Optional(), Length(max=128)])
    postal_code  = StringField('Postal Code',      validators=[Optional(), Length(max=32)])
    registration_number = StringField('Registration Number')
    vat_reg_number = StringField('VAT Reg. Number')
    tax_number = StringField('Tax Number')
    year_of_construction = StringField('Year of Construction', validators=[Optional(), Length(max=10)])
    number_of_units = IntegerField('Number of Units', validators=[Optional()])
    units_apartments = IntegerField('Apartments', validators=[Optional(), NumberRange(min=0)])
    units_houses = IntegerField('Houses', validators=[Optional(), NumberRange(min=0)])
    units_duplexes = IntegerField('Duplexes', validators=[Optional(), NumberRange(min=0)])
    units_commercial = IntegerField('Commercial Units', validators=[Optional(), NumberRange(min=0)])
    units_other = IntegerField('Other Units', validators=[Optional(), NumberRange(min=0)])
    client_type = SelectField('Client Type', choices=[], validators=[Optional()])
    contract_value = DecimalField('Contract Value', validators=[Optional()])

    # 📅 Governance
    financial_year_end = DateField('Financial Year End', validators=[Optional()])
    last_agm_date = DateField('Last AGM Date', validators=[Optional()])
    agm_completed = BooleanField('AGM Completed')

    # 🌍 Location
    country = StringField('Country')
    region = StringField('Region')
    currency = StringField('Currency')
    timezone = StringField('Timezone')
    preferred_language = StringField('Preferred Language')
    ownership_type = StringField('Ownership Type')

    # 🛡️ Legal
    transfer_of_common_area = BooleanField('Transfer of Common Area')
    deed_of_covenants = StringField('Deed of Covenants')
    data_protection_compliance = StringField('Data Protection Compliance')
    consent_to_communicate = BooleanField('Consent to Communicate', default=True)
    resident_logic = StringField('Resident Logic')
    enforce_gdpr = BooleanField('Enforce GDPR', default=True)
    default_visibility_scope = StringField('Default Visibility Scope')

    # 🏢 Block Structure
    min_directors = IntegerField('Min Directors')
    max_directors = IntegerField('Max Directors')
    number_of_blocks = IntegerField('Number of Blocks')
    block_names = StringField('Block Names')
    cores_per_block = StringField('Cores Per Block')
    apartments_per_block = StringField('Apartments Per Block')

    # 🏗️ Valuation
    reinstatement_value = DecimalField('Reinstatement Value', validators=[Optional()])
    reinstatement_valuation_date = DateField('Valuation Date', validators=[Optional()])

    # 👥 Assignments (with neutral placeholders handled in routes)
    assigned_pm_id = SelectField('Assigned Property Manager', coerce=int, validators=[Optional()])
    assigned_fc_id = SelectField('Assigned Financial Controller', coerce=int, validators=[Optional()])
    assigned_assistant_id = SelectField('Assigned Assistant PM', coerce=int, validators=[Optional()])

    # 📎 File Upload
    document_file = FileField(
        'Upload Contract File',
        validators=[Optional(), FileAllowed(['pdf', 'doc', 'docx'], 'Documents only!')]
    )

    # 🧠 AI Integration
    ownership_types = SelectMultipleField(
        'Ownership Types',
        choices=[('Freehold','Freehold'), ('Leasehold','Leasehold'), ('Share of Freehold','Share of Freehold')]
    )
    ai_key_clauses = TextAreaField(
        'AI Key Clauses (JSON Format)',
        validators=[Optional(), validate_json],
        render_kw={"placeholder": '{"clause1": "value", "clause2": "value"}'}
    )
    capex_status = SelectField(
        'CAPEX Profile Status',
        choices=[('not_created','Not Created'), ('in_progress','In Progress'), ('completed','Completed')],
        default='not_created'
    )
    tags = StringField('Tags')
    ai_governance_summary = TextAreaField('AI Governance Summary', validators=[Optional()])
    ai_flagged_risks = TextAreaField('AI Flagged Risks', validators=[Optional()])
    ai_advice_summary = TextAreaField('AI Advice Summary', validators=[Optional()])
    ai_review_comment = TextAreaField('AI Review Comment', validators=[Optional()])

    # 🌐 GAR Integration
    is_gar_monitored = BooleanField('Enable GAR Monitoring?')
    gar_chat_ready = BooleanField('GAR Chat Ready?')
    gar_resolution_status = SelectField(
        'GAR Status',
        choices=[('Open','Open'), ('Resolved','Resolved'), ('Escalated','Escalated')],
        validators=[Optional()]
    )

    # 🔗 Governance Config Reference
    country_config_id = SelectField('Country Config', coerce=int, validators=[Optional()])

    submit = SubmitField('Save Client')
