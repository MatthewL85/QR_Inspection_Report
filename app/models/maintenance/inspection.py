# app/models/inspection.py

from datetime import datetime
from app.extensions import db

class Inspection(db.Model):
    __tablename__ = 'inspections'

    id = db.Column(db.Integer, primary_key=True)

    # 🔧 Core Inspection Info
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    inspector_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    role = db.Column(db.String(50))                            # Contractor, PM, Auditor
    inspection_date = db.Column(db.Date, nullable=False)
    next_due = db.Column(db.String(20))                        # DD-MM-YYYY or pattern
    status = db.Column(db.String(50))                          # Passed, Failed, Needs Review
    notes = db.Column(db.Text)
    inspected_remotely = db.Column(db.Boolean, default=False)
    inspection_channel = db.Column(db.String(50))              # App, Email Upload, Manual

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_notes = db.Column(db.Text, nullable=True)

    # 📎 File Metadata
    document_filename = db.Column(db.String(255))
    attachments_count = db.Column(db.Integer, default=0)
    media_uploaded = db.Column(db.Boolean, default=False)
    doc_links = db.Column(db.JSON, nullable=True)
    photo_links = db.Column(db.JSON, nullable=True)
    ai_source_type = db.Column(db.String(50))                  # pdf, image, doc, etc.

    # 🔐 Visibility / Consent
    visibility_scope = db.Column(db.String(100), default='Admin,PM,Contractor')
    is_private = db.Column(db.Boolean, default=False)
    consent_verified = db.Column(db.Boolean, default=False)
    shared_with_director = db.Column(db.Boolean, default=False)

    # 🔌 External System Sync
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    is_external = db.Column(db.Boolean, default=False)
    sync_status = db.Column(db.String(50), default='Pending')

    # 🤖 AI Parsing Fields
    parsed_text = db.Column(db.Text)
    ai_parsed_summary = db.Column(db.Text)
    ai_flagged_issues = db.Column(db.Text)
    ai_recommendations = db.Column(db.Text)
    extracted_data = db.Column(db.JSON)
    ai_confidence_score = db.Column(db.Float)
    parsed_fields_confidence = db.Column(db.JSON, nullable=True)  # {"findings": 0.91, "risk": 0.77}
    ai_parsed_at = db.Column(db.DateTime)
    parsed_by_ai_version = db.Column(db.String(50))
    parsing_status = db.Column(db.String(50), default='Pending')
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)

    # 🧠 GAR Scoring & Recommendation
    ai_scorecard = db.Column(db.JSON, nullable=True)           # e.g., {"risk": "Low", "urgency": "High"}
    ai_rank = db.Column(db.String(20), nullable=True)          # A, B, C
    is_ai_preferred = db.Column(db.Boolean, default=False)
    reason_for_recommendation = db.Column(db.Text)
    flagged_sections = db.Column(db.JSON, nullable=True)       # {"fire_alarm": "missing visual proof"}

    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)


    # 🔁 Relationships
    equipment = db.relationship('Equipment', backref='inspections')
    inspector = db.relationship('User', backref='inspections')

    def __repr__(self):
        return f"<Inspection id={self.id} equipment_id={self.equipment_id} status={self.status}>"
