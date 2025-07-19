# app/models/leave_request.py

from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Leave Info
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    leave_type = db.Column(db.String(50))                               # Annual, Sick, Maternity
    leave_category = db.Column(db.String(50), nullable=True)            # Paid, Unpaid, Compassionate, etc.
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    total_days = db.Column(db.Float, nullable=True)                     # Auto-calculated
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pending')                # Pending, Approved, Rejected, Cancelled
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    leave_balance_at_request = db.Column(db.Float, nullable=True)

    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    # 🔐 Visibility / Consent
    visibility_scope = db.Column(db.String(100), default='Admin,HR')
    is_private = db.Column(db.Boolean, default=True)
    shared_with_director = db.Column(db.Boolean, default=False)
    consent_verified = db.Column(db.Boolean, default=False)

    # 🔌 API / External Sync
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')
    is_external = db.Column(db.Boolean, default=False)

    # 📋 Policy & Governance
    leave_policy_url = db.Column(db.String(255), nullable=True)
    is_policy_violation = db.Column(db.Boolean, default=False)
    review_category = db.Column(db.String(50), nullable=True)           # e.g., Balance Check, Urgent Approval
    review_notes = db.Column(db.Text, nullable=True)

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
    flagged_sections = db.Column(db.JSON, nullable=True)

    # 🧠 GAR Governance
    gar_flags = db.Column(db.Text, nullable=True)
    gar_score = db.Column(db.Float, nullable=True)
    gar_comments = db.Column(db.Text, nullable=True)
    requires_manual_review = db.Column(db.Boolean, default=False)
    last_reviewed_at = db.Column(db.DateTime, nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # ⚠️ Leave Conflict + Impact Fields (NEW)
    conflict_flag = db.Column(db.Boolean, default=False)                    # True if overlapping critical team
    conflict_notes = db.Column(db.Text, nullable=True)                     # Auto-generated explanation
    impacted_services = db.Column(JSONB, nullable=True)                    # e.g. {"work_orders": [1, 2], "ppm_tasks": [5]}
    suggested_alternatives = db.Column(JSONB, nullable=True)               # e.g. {"user_id": 18, "name": "Jane Smith"}

    # 🔁 Relationships
    user = db.relationship("User", foreign_keys=[user_id], backref="leave_requests")
    approver = db.relationship("User", foreign_keys=[approved_by], backref="approved_leaves")

    def __repr__(self):
        return f"<LeaveRequest user_id={self.user_id} type={self.leave_type} status={self.status}>"
