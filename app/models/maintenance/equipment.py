# app/models/equipment.py

from datetime import datetime
from app.extensions import db

class Equipment(db.Model):
    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)

    # 🆔 Identification
    qr_code_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150))
    equipment_type = db.Column(db.String(50))
    serial_number = db.Column(db.String(100))
    model = db.Column(db.String(100))
    age = db.Column(db.String(50))
    maintenance_frequency = db.Column(db.String(50))
    warranty_expiry = db.Column(db.String(20))
    last_inspection = db.Column(db.String(20))
    last_service_date = db.Column(db.Date, nullable=True)
    expected_lifespan_years = db.Column(db.Integer, nullable=True)
    last_inspected_by = db.Column(db.String(100), nullable=True)

    # 🧩 Structure / Location
    site_block_name = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    tags = db.Column(db.String(255), nullable=True)  # e.g., “fire safety, critical, pump”

    # 🔐 Ownership and Access
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship('Company', backref='equipment')
    client = db.relationship('Client', backref='equipment_list')
    unit = db.relationship('Unit', backref='equipment')
    creator = db.relationship('User', foreign_keys=[created_by])

    # 🔐 Security & Visibility
    visibility_scope = db.Column(db.String(100), default='Admin,PM,Contractor')
    is_private = db.Column(db.Boolean, default=False)
    consent_verified = db.Column(db.Boolean, default=False)
    shared_with_director = db.Column(db.Boolean, default=False)

    # 🔌 API / External System Fields
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')
    is_external = db.Column(db.Boolean, default=False)

    # 📎 File / Media Info
    document_filename = db.Column(db.String(255))
    media_uploaded = db.Column(db.Boolean, default=False)
    attachments_count = db.Column(db.Integer, default=0)
    ai_source_type = db.Column(db.String(50))  # pdf, scan, doc, etc.

    # 🤖 AI Outputs
    parsed_at = db.Column(db.DateTime)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)

    ai_parsed_warranty_terms = db.Column(db.Text)
    ai_compliance_flags = db.Column(db.Text)
    ai_lifecycle_notes = db.Column(db.Text)
    ai_risks_detected = db.Column(db.Text)
    ai_predicted_failure_window = db.Column(db.String(100))  # e.g., "12–18 months"
    ai_maintenance_recommendations = db.Column(db.Text)
    ai_replacement_recommendation = db.Column(db.Text, nullable=True)
    ai_confidence_score = db.Column(db.Float, nullable=True)
    ai_field_completeness = db.Column(db.JSON, nullable=True)  # {"warranty": 0.95, "docs": 0.6}
    flagged_sections = db.Column(db.JSON, nullable=True)       # {"safety_cert": "missing"}

    # 🧠 GAR Scoring & Recommendation
    ai_scorecard = db.Column(db.JSON, nullable=True)  # {"risk": 0.8, "compliance": 0.95}
    ai_rank = db.Column(db.String(20), nullable=True) # A, B, C
    is_ai_preferred = db.Column(db.Boolean, default=False)
    reason_for_recommendation = db.Column(db.Text)

    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Equipment id={self.id} name={self.name}>"
