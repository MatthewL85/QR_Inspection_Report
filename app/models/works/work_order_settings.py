from datetime import datetime
from app.extensions import db

class WorkOrderSettings(db.Model):
    __tablename__ = 'work_order_settings'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # 🔧 Defaults & Thresholds
    default_response_time_hours = db.Column(db.Integer, default=48)
    default_completion_time_hours = db.Column(db.Integer, default=168)  # One week
    enable_preferred_contractor_routing = db.Column(db.Boolean, default=True)
    allow_multi_contractor_routing = db.Column(db.Boolean, default=False)
    auto_reassign_on_rejection = db.Column(db.Boolean, default=True)
    require_completion_notes = db.Column(db.Boolean, default=True)
    allow_media_upload_on_completion = db.Column(db.Boolean, default=True)

    # ✅ NEW: Internal Assignment Policies
    allow_assign_to_staff = db.Column(db.Boolean, default=True)
    allow_assign_to_team = db.Column(db.Boolean, default=True)
    restrict_completion_to_assigned = db.Column(db.Boolean, default=True)
    require_admin_confirmation_for_completion = db.Column(db.Boolean, default=False)
    allow_staff_self_acceptance = db.Column(db.Boolean, default=False)

    # 📊 Ratings & Feedback
    enable_contractor_ratings = db.Column(db.Boolean, default=True)
    allow_director_feedback = db.Column(db.Boolean, default=False)
    show_performance_summary_to_pm = db.Column(db.Boolean, default=True)

    # 🧠 AI / GAR Recommendations
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    ai_confidence_score = db.Column(db.Float, nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)

    gar_flags = db.Column(db.Text, nullable=True)
    gar_risk_score = db.Column(db.Float, nullable=True)
    gar_recommendation = db.Column(db.Text, nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🔐 Governance & Audit
    escalation_threshold_hours = db.Column(db.Integer, default=72)
    notify_on_overdue = db.Column(db.Boolean, default=True)
    require_compliance_docs = db.Column(db.Boolean, default=True)
    lock_assignment_post_acceptance = db.Column(db.Boolean, default=True)

    # 📎 Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    company = db.relationship('Company', backref='work_order_settings')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    updated_by = db.relationship('User', foreign_keys=[updated_by_id])

    def __repr__(self):
        return f"<WorkOrderSettings company_id={self.company_id}>"
