from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class TrialBalance(db.Model):
    __tablename__ = 'trial_balances'

    id = db.Column(db.Integer, primary_key=True)

    # 📆 Reporting Context
    report_date = db.Column(db.Date, nullable=False)

    # 🔗 Contextual Reference
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 🧾 Financial Core
    total_debits = db.Column(db.Numeric(precision=12, scale=2), default=0)
    total_credits = db.Column(db.Numeric(precision=12, scale=2), default=0)
    is_balanced = db.Column(db.Boolean, default=True)

    # 📊 Breakdown of all account balances
    account_summaries = db.Column(JSONB, nullable=True)
    # Example: [{"account": "Service Charge Income", "debit": 0.00, "credit": 5000.00}, ...]

    # 🤖 AI / GAR Intelligence
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_summary = db.Column(db.Text, nullable=True)
    gar_score = db.Column(db.String(20), nullable=True)
    gar_flag = db.Column(db.String(255), nullable=True)
    gar_recommendation = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)

    # 🔐 GDPR + Security Meta
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    # 🕵️ Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔗 Relationships
    client = db.relationship('Client', backref='trial_balances')
    unit = db.relationship('Unit', backref='trial_balances')
    created_by = db.relationship('User', backref='generated_trial_balances')

    def __repr__(self):
        return f"<TrialBalance client_id={self.client_id} report_date={self.report_date} balanced={self.is_balanced}>"

