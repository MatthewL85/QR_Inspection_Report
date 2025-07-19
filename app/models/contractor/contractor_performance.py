# app/models/contractor_performance.py

from datetime import datetime
from app.extensions import db

class ContractorPerformance(db.Model):
    __tablename__ = 'contractor_performance'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Entity Relationships
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractors.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # PM/admin who logged it
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'))

    contractor = db.relationship('User', backref='performance_records')
    work_order = db.relationship('WorkOrder', backref='contractor_performance')

    # 📊 Performance Metrics
    response_time = db.Column(db.Integer)           # Time until accepted (mins or hours)
    completion_time = db.Column(db.Integer)         # From acceptance to completion
    performance_rating = db.Column(db.String(10))   # A, B, C, etc.
    performance_period = db.Column(db.String(50))   # e.g., 'Q2 2025', 'Annual 2024'

    # 🔐 Privacy, Visibility
    consent_verified = db.Column(db.Boolean, default=False)
    is_private = db.Column(db.Boolean, default=False)         # Only admin/director can view
    visibility_scope = db.Column(db.String(100), default='Admin,PM')

    # 🔌 External System Support
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Pending, Failed
    is_external = db.Column(db.Boolean, default=False)

    # 🤖 Phase 1: AI Parsing Fields
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)  # system_generated, log, email
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)

    # 🧠 Phase 2: GAR Evaluation Support
    ai_scorecard = db.Column(db.JSON, nullable=True)         # {"quality": 0.85, "followup": 0.6}
    ai_recommendation = db.Column(db.Text, nullable=True)
    ai_risk_level = db.Column(db.String(20), nullable=True)  # Low, Medium, High
    ai_confidence_score = db.Column(db.Float, nullable=True)
    ai_feedback_flags = db.Column(db.Text, nullable=True)
    ai_preferred_status = db.Column(db.Boolean, default=False)
    ai_evaluation_source = db.Column(db.String(50))          # Based on feedback, logs, combined

    # 💬 Interaction & Governance
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)
    gar_explanation = db.Column(db.Text, nullable=True)      # Why preferred/flagged
    audit_trail_linked = db.Column(db.Boolean, default=False)  # Whether audit trail is linked (future log viewer)

    # 🕒 Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ContractorPerformance contractor_id={self.contractor_id} rating={self.performance_rating}>"
