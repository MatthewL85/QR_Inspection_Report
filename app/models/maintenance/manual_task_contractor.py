# app/models/manual_task_contractor.py

from datetime import datetime
from app.extensions import db

class ManualTaskContractor(db.Model):
    __tablename__ = 'manual_task_contractors'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Foreign Keys
    task_id = db.Column(db.Integer, db.ForeignKey('manual_tasks.id'), nullable=False)
    contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    task = db.relationship("ManualTask", backref="contractor_assignments")
    contractor = db.relationship("User", foreign_keys=[contractor_id])

    # 📋 Task Execution Info
    notes = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    completion_notes = db.Column(db.Text, nullable=True)
    attachments_count = db.Column(db.Integer, default=0)
    media_uploaded = db.Column(db.Boolean, default=False)
    task_category = db.Column(db.String(100), nullable=True)  # Cleaning, Pest Control, etc.

    # 🔐 Visibility & Access
    visibility_scope = db.Column(db.String(100), default='Admin,PM,Contractor')
    consent_verified = db.Column(db.Boolean, default=False)
    is_private = db.Column(db.Boolean, default=False)
    shared_with_director = db.Column(db.Boolean, default=False)

    # 🔌 API / External Integration
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    is_external = db.Column(db.Boolean, default=False)
    sync_status = db.Column(db.String(50), default='Pending')  # Pending, Synced, Failed

    # 🤖 AI Parsing Fields
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)

    # 🧠 GAR Governance & Smart Review
    ai_governance_verdict = db.Column(db.String(100))  # Compliant, Non-compliant, Incomplete
    ai_flagged_concerns = db.Column(db.Text)
    ai_completion_confidence = db.Column(db.Float)
    ai_recommended_followup = db.Column(db.Text)
    ai_aligned_with_contract = db.Column(db.Boolean, default=True)
    completion_quality_score = db.Column(db.Float, nullable=True)  # Based on detail, photo match, etc.
    flagged_sections = db.Column(db.JSON, nullable=True)           # e.g., {"photos": "missing", "duration": "inconsistent"}
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<ManualTaskContractor task_id={self.task_id} contractor_id={self.contractor_id}>"

