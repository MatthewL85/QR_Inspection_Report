from datetime import datetime
from app.extensions import db

class UserPolicyAcknowledgements(db.Model):
    __tablename__ = 'user_policy_acknowledgements'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    policy_id = db.Column(db.Integer, db.ForeignKey('hr_policies.id'), nullable=False)
    hr_profile_id = db.Column(db.Integer, db.ForeignKey('hr_profiles.id'), nullable=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('employment_contracts.id'), nullable=True)

    # 📅 Acknowledgement Info
    acknowledged_at = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged_by_user = db.Column(db.Boolean, default=True)  # True = user, False = admin override
    signature_captured = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(50), nullable=True)
    device_info = db.Column(db.String(255), nullable=True)
    version_acknowledged = db.Column(db.String(20), nullable=True)
    policy_snapshot = db.Column(db.Text, nullable=True)  # Optional historical policy text

    # 🤖 AI Parsing & Context
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')  # Pending, Completed, Failed
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Evaluation
    gar_flags = db.Column(db.Text, nullable=True)                   # e.g., "Outdated version acknowledged"
    gar_trust_score = db.Column(db.Float, nullable=True)
    gar_compliance_notes = db.Column(db.Text, nullable=True)
    is_gar_verified = db.Column(db.Boolean, default=False)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)


    # 🔁 Relationships
    user = db.relationship("User", backref="policy_acknowledgements")
    policy = db.relationship("HRPolicy", backref="acknowledgements")
    hr_profile = db.relationship("HRProfile", backref="policy_acknowledgements")
    contract = db.relationship("EmploymentContract", backref="policy_acknowledgements")

    def __repr__(self):
        return f"<UserPolicyAcknowledgement user_id={self.user_id} policy_id={self.policy_id}>"
