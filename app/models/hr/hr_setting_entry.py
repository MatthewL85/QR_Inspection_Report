from datetime import datetime
from app.extensions import db

class HRSettingEntry(db.Model):
    __tablename__ = 'hr_setting_entries'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)

    # 🔑 Key-Value Pair
    setting_key = db.Column(db.String(100), nullable=False)
    setting_value = db.Column(db.String(255), nullable=True)
    data_type = db.Column(db.String(50), default='string')
    category = db.Column(db.String(100), nullable=True)

    # 🧠 AI Parsing
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime)
    parsed_by_ai_version = db.Column(db.String(50))
    ai_source_type = db.Column(db.String(50))
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🛡️ GAR Evaluation
    gar_flags = db.Column(db.Text, nullable=True)
    gar_risk_score = db.Column(db.Float, nullable=True)
    gar_recommendation = db.Column(db.Text, nullable=True)
    is_governance_approved = db.Column(db.Boolean, default=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🧑‍💼 Audit
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    company = db.relationship('Company', backref="hr_setting_entries")
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    updated_by = db.relationship('User', foreign_keys=[updated_by_id])

    def __repr__(self):
        return f"<HRSettingEntry key='{self.setting_key}' value='{self.setting_value}'>"
