# app/models/manual_task.py

from datetime import datetime
from app.extensions import db

class ManualTask(db.Model):
    __tablename__ = 'manual_tasks'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    client = db.relationship("Client", backref="manual_tasks")
    created_by_user = db.relationship("User", foreign_keys=[created_by_id])

    # 📋 Task Details
    task_name = db.Column(db.String(150), nullable=False)
    task_category = db.Column(db.String(100), nullable=True)  # e.g., Cleaning, Powerwash, Inspection
    frequency = db.Column(db.String(50))                      # Daily, Weekly, Monthly, etc.
    status = db.Column(db.String(50), default='Scheduled')    # Scheduled, Completed, Missed
    due_date = db.Column(db.Date, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(120))                    # For legacy traceability
    notes = db.Column(db.Text, nullable=True)
    region = db.Column(db.String(100), nullable=True)
    site_block_name = db.Column(db.String(100), nullable=True)
    tags = db.Column(db.String(255), nullable=True)           # e.g., "external, window, high risk"

    # 🔐 Visibility & Privacy
    visibility_scope = db.Column(db.String(100), default='Admin,PM')
    consent_verified = db.Column(db.Boolean, default=False)
    is_private = db.Column(db.Boolean, default=False)
    shared_with_director = db.Column(db.Boolean, default=False)

    # 🔌 External/API Integration
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
    ai_confidence_score = db.Column(db.Float, nullable=True)
    flagged_sections = db.Column(db.JSON, nullable=True)      # e.g., {"frequency": "undefined"}

    # 🧠 GAR Governance Fields
    ai_governance_recommendation = db.Column(db.Text)
    ai_priority = db.Column(db.String(50))                    # Low, Medium, High
    ai_flagged_risks = db.Column(db.Text)
    is_ai_governance_compliant = db.Column(db.Boolean, default=True)
    ai_alignment_score = db.Column(db.Float)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)


    def __repr__(self):
        return f"<ManualTask {self.task_name} for Client {self.client_id}>"

