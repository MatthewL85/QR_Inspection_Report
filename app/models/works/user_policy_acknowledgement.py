from datetime import datetime
from app.extensions import db

class UserPolicyAcknowledgement(db.Model):
    __tablename__ = 'user_policy_acknowledgements'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    work_order_policy_id = db.Column(db.Integer, db.ForeignKey('work_order_policies.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)

    # 📅 Acknowledgement Metadata
    acknowledged_at = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledgment_method = db.Column(db.String(50), default='Dashboard')  # Dashboard, Email, Upload, etc.
    signed_copy_url = db.Column(db.String(255), nullable=True)
    policy_version = db.Column(db.String(20), nullable=True)

    # ✅ Compliance Flags
    is_required = db.Column(db.Boolean, default=True)
    is_current = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)

    # 🔁 Relationships
    user = db.relationship('User', backref='work_order_policy_acknowledgements')
    company = db.relationship('Company', backref='user_policy_acknowledgements')
    client = db.relationship('Client', backref='user_policy_acknowledgements')
    work_order_policy = db.relationship('WorkOrderPolicy', backref='acknowledged_users')

    # 🤖 AI / GAR Parsing
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)                   # {"policy_version": "1.2", "method": "Dashboard"}
    parsing_status = db.Column(db.String(50), default='Pending')         # Pending, Completed, Failed
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    parsed_at = db.Column(db.DateTime, nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_confidence_score = db.Column(db.Float, nullable=True)             # 0.0–1.0 confidence
    ai_profile_locked = db.Column(db.Boolean, default=False)

    # 🧠 GAR Governance Layer
    gar_flags = db.Column(db.Text, nullable=True)                        # "Old version signed", "Missing signature"
    gar_risk_score = db.Column(db.Float, nullable=True)                 # 0.0–1.0
    requires_review = db.Column(db.Boolean, default=False)
    gar_recommendation = db.Column(db.String(255), nullable=True)       # "Request re-sign", etc.
    gar_explanation = db.Column(db.Text, nullable=True)

    # 💬 GAR Chat Layer
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return (
            f"<UserPolicyAcknowledgement user_id={self.user_id} "
            f"policy_id={self.work_order_policy_id} acknowledged_at={self.acknowledged_at}>"
        )

