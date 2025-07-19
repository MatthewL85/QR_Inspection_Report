# models/members/resident_request.py

from app.extensions import db
from datetime import datetime

class ResidentRequest(db.Model):
    __tablename__ = 'resident_requests'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    unit = db.relationship('Unit', backref='resident_requests')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])

    # 🙋 Resident Info
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    request_notes = db.Column(db.Text, nullable=True)

    # 📌 Status & Dates
    status = db.Column(db.String(50), default='Pending')  # Pending, Approved, Rejected
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)

    # 🔐 GDPR / Privacy Consent
    consent_to_contact = db.Column(db.Boolean, default=False)
    data_sharing_opt_in = db.Column(db.Boolean, default=False)
    share_info_with_directors = db.Column(db.Boolean, default=False)

    # 🔌 External/API Fields
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    is_external = db.Column(db.Boolean, default=False)

    # 🤖 AI Parsing & GAR Context
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')  # Pending, Completed, Failed
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)  # Freezes parsing once reviewed

    # ⚖️ GAR Governance Fields
    gar_flagged = db.Column(db.Boolean, default=False)
    gar_trust_score = db.Column(db.Float, nullable=True)
    gar_alignment_score = db.Column(db.Float, nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)
    gar_risk_reason = db.Column(db.Text, nullable=True)  # e.g., “Missing proof of residence”
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)


    def __repr__(self):
        return f"<ResidentRequest name={self.full_name} unit_id={self.unit_id}>"

