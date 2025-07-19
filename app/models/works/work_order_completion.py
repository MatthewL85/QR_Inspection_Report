# app/models/work_order_completion.py

from app.extensions import db
from datetime import datetime

class WorkOrderCompletion(db.Model):
    __tablename__ = 'work_order_completions'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Foreign Keys
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), unique=True, nullable=False)
    completed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractors.id'), nullable=True)

    # ✅ NEW: Internal Delegation Tracking
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_team_id = db.Column(db.Integer, db.ForeignKey('contractor_teams.id'), nullable=True)
    completion_type = db.Column(db.String(50), default='Contractor Staff')  # Contractor Admin, Contractor Staff, Team-based

    # ✅ Optional Confirmation Logic (future moderation)
    confirmed_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 🔁 Relationships
    work_order = db.relationship('WorkOrder', backref='completion', uselist=False)
    completed_by = db.relationship('User', foreign_keys=[completed_by_id])
    contractor = db.relationship('Contractor', backref='completed_work_orders')
    assigned_user = db.relationship('User', foreign_keys=[assigned_user_id])
    assigned_team = db.relationship('ContractorTeam', foreign_keys=[assigned_team_id])
    confirmed_by_admin = db.relationship('User', foreign_keys=[confirmed_by_admin_id])

    # 🔧 Core Completion Details
    completion_notes = db.Column(db.Text)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    attachments_count = db.Column(db.Integer, default=0)
    media_uploaded = db.Column(db.Boolean, default=False)

    # 🔐 Privacy & Role Access
    access_masked = db.Column(db.Boolean, default=False)
    visibility_scope = db.Column(db.String(100), default='Admin,PM,Contractor')
    consent_verified = db.Column(db.Boolean, default=False)

    # 🔌 External/API Sync
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    is_external = db.Column(db.Boolean, default=False)
    sync_status = db.Column(db.String(50), default='Not Synced')  # Synced, Pending, Failed

    # 🤖 AI Parsing Fields (Standardized)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')  # Pending, Completed, Failed
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)

    # ⚖️ GAR Governance Fields (Phase 2+)
    gar_verdict = db.Column(db.String(50))                      # Compliant, Incomplete, Flagged
    gar_flagged_issues = db.Column(db.Text)
    gar_confidence_score = db.Column(db.Float)
    gar_alignment_with_contract = db.Column(db.Boolean, default=True)
    gar_recommendation = db.Column(db.String(255))
    gar_explanation = db.Column(db.Text, nullable=True)
    attachment_quality_score = db.Column(db.Float)

    # 💬 GAR Chat Layer
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<WorkOrderCompletion work_order_id={self.work_order_id}>"
