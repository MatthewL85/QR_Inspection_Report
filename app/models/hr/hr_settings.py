from datetime import datetime
from app.extensions import db

class HRSettings(db.Model):
    __tablename__ = 'hr_settings'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # 🏖️ Leave Accrual Defaults
    default_annual_accrual = db.Column(db.Float, default=20.0)       # Days per year
    default_sick_accrual = db.Column(db.Float, default=10.0)
    accrual_frequency = db.Column(db.String(20), default="Monthly")  # Monthly, Quarterly, Yearly
    carry_forward_limit = db.Column(db.Float, default=5.0)
    allow_negative_balance = db.Column(db.Boolean, default=False)

    # 🔌 API & External Sync (optional future use)
    source_system = db.Column(db.String(100), nullable=True)
    external_reference = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')

    # 🧠 AI / GAR Evaluation
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    parsed_at = db.Column(db.DateTime, nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)

    gar_flags = db.Column(db.Text, nullable=True)
    gar_risk_score = db.Column(db.Float, nullable=True)
    gar_recommendation = db.Column(db.Text, nullable=True)
    is_governance_approved = db.Column(db.Boolean, default=True)

    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🧑‍💼 Audit Trail
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    created_by = db.relationship('User', foreign_keys=[created_by_id])
    updated_by = db.relationship('User', foreign_keys=[updated_by_id])
    company = db.relationship("Company", backref="hr_settings")

    def __repr__(self):
        return f"<HRSettings company_id={self.company_id}>"