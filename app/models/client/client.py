from datetime import datetime
from app.extensions import db

class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)

    # 🔐 Ownership
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    company = db.relationship('Company', backref='clients')

    # 🔧 Core Information
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(250))
    postal_code = db.Column(db.String(20))
    registration_number = db.Column(db.String(50))
    vat_reg_number = db.Column(db.String(50))
    tax_number = db.Column(db.String(50))
    year_of_construction = db.Column(db.String(10))
    number_of_units = db.Column(db.Integer)
    client_type = db.Column(db.String(50))
    contract_value = db.Column(db.Numeric(10, 2), default=0.0)

    # 📅 Governance Dates
    financial_year_end = db.Column(db.Date, nullable=True)
    last_agm_date = db.Column(db.Date, nullable=True)
    agm_completed = db.Column(db.Boolean, default=False)

    # 🌍 Location & Jurisdiction
    country = db.Column(db.String(100))
    region = db.Column(db.String(100))
    currency = db.Column(db.String(10))
    timezone = db.Column(db.String(50))
    preferred_language = db.Column(db.String(50))
    ownership_type = db.Column(db.String(50))

    # 🛡️ Legal & Compliance
    transfer_of_common_area = db.Column(db.Boolean, default=False)
    deed_of_covenants = db.Column(db.String(250))
    data_protection_compliance = db.Column(db.String(50))
    consent_to_communicate = db.Column(db.Boolean, default=True)
    resident_logic = db.Column(db.String(100), default='owner=member, tenant=resident')  # 🔁 Explicit occupancy logic
    enforce_gdpr = db.Column(db.Boolean, default=True)
    default_visibility_scope = db.Column(db.String(100), default="Admin,Director,PropertyManager")

    # 🏢 Block Structure
    min_directors = db.Column(db.Integer)
    max_directors = db.Column(db.Integer)
    number_of_blocks = db.Column(db.Integer)
    block_names = db.Column(db.String(300))
    cores_per_block = db.Column(db.String(300))
    apartments_per_block = db.Column(db.String(300))

    # 👤 Assigned Property Manager
    assigned_pm_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_pm = db.relationship('User', backref='assigned_clients', foreign_keys=[assigned_pm_id])

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🏗️ Valuation Details
    reinstatement_value = db.Column(db.Numeric(14, 2))
    reinstatement_valuation_date = db.Column(db.Date)
    ai_valuation_analysis = db.Column(db.Text)
    ai_insurance_trend_flag = db.Column(db.Text)

    # 📎 Contract & Document Parsing (AI Phase 1)
    document_filename = db.Column(db.String(255))
    ai_parsed_contract_terms = db.Column(db.Text)
    ai_governance_summary = db.Column(db.Text)
    ai_ownership_structure_analysis = db.Column(db.Text)
    ai_service_charge_insight = db.Column(db.Text)
    ai_flagged_risks = db.Column(db.Text)
    parsed_at = db.Column(db.DateTime)
    parsed_by_ai_version = db.Column(db.String(50))
    ai_source_type = db.Column(db.String(50))
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Intelligence (Phase 2+)
    ai_governance_score = db.Column(db.Float, nullable=True)
    ai_compliance_index = db.Column(db.Float, nullable=True)
    ai_health_index = db.Column(db.Float, nullable=True)
    ai_trend_insight = db.Column(db.Text, nullable=True)
    ai_advice_summary = db.Column(db.Text, nullable=True)
    ai_prediction_flags = db.Column(db.String(300), nullable=True)
    ai_risk_level = db.Column(db.String(50), nullable=True)
    is_gar_monitored = db.Column(db.Boolean, default=True)

    # 💬 GAR Chat & Feedback
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)
    gar_last_message_at = db.Column(db.DateTime, nullable=True)
    gar_resolution_status = db.Column(db.String(50), default='Open')  # Open, Resolved, Escalated

    # 🧩 JSON-Compatible Fields (API & AI)
    ownership_types = db.Column(db.JSON, nullable=True)              # e.g., ['Freehold', 'Leasehold']
    ai_key_clauses = db.Column(db.JSON, nullable=True)               # e.g., {"break_clause": "...", "notice": "90 days"}

    # 🏷️ Tags / Classification
    tags = db.Column(db.String(255), nullable=True)
    capex_profile = db.Column(db.String(100), nullable=True)

    # 📝 Review/Audit Trail
    ai_last_reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ai_review_comment = db.Column(db.Text, nullable=True)
    ai_last_reviewed_at = db.Column(db.DateTime, nullable=True)

    ai_reviewer = db.relationship('User', foreign_keys=[ai_last_reviewed_by])

    # 🔗 Governance Config Reference
    country_config_id = db.Column(db.Integer, db.ForeignKey('country_client_config.id'), nullable=True)
    country_config = db.relationship('CountryClientConfig', backref='linked_clients')

    def __repr__(self):
        return f"<Client {self.name} ({self.client_type})>"
