# app/models/termination_record.py

from datetime import datetime
from app.extensions import db

class TerminationRecord(db.Model):
    __tablename__ = 'termination_records'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], backref="termination_records")
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])

    # 📅 Core Termination Data
    termination_date = db.Column(db.Date, nullable=False)
    termination_type = db.Column(db.String(50))                        # Voluntary, Involuntary, Redundancy
    reason = db.Column(db.Text, nullable=True)
    notice_period_given = db.Column(db.Boolean, default=None)
    exit_interview_notes = db.Column(db.Text, nullable=True)
    exit_survey_url = db.Column(db.String(255), nullable=True)
    replacement_required = db.Column(db.Boolean, default=False)
    replacement_role_title = db.Column(db.String(100), nullable=True)
    handover_required = db.Column(db.Boolean, default=False)
    handover_notes = db.Column(db.Text, nullable=True)
    termination_document_url = db.Column(db.String(255), nullable=True)

    # 🔐 Visibility & Consent
    visibility_scope = db.Column(db.String(100), default='Admin,HR')
    is_private = db.Column(db.Boolean, default=True)
    shared_with_director = db.Column(db.Boolean, default=False)
    consent_verified = db.Column(db.Boolean, default=False)

    # 🔌 External API Integration
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')
    is_external = db.Column(db.Boolean, default=False)

    # 🤖 AI Parsing Fields
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_confidence_score = db.Column(db.Float, nullable=True)
    ai_profile_locked = db.Column(db.Boolean, default=False)
    flagged_sections = db.Column(db.JSON, nullable=True)               # {"policy": "missing", "notice": "incomplete"}
    recommendation_category = db.Column(db.String(50), nullable=True)  # e.g., Legal Review, Follow-up Exit Survey

    # ⚖️ GAR Governance Fields
    gar_risk_score = db.Column(db.Float, nullable=True)
    gar_summary = db.Column(db.Text, nullable=True)
    gar_flagged_issues = db.Column(db.Text, nullable=True)
    is_gar_reviewed = db.Column(db.Boolean, default=False)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)


    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TerminationRecord user_id={self.user_id} date={self.termination_date} type={self.termination_type}>"

