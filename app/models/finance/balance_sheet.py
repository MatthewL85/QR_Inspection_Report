from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class BalanceSheet(db.Model):
    __tablename__ = 'balance_sheets'

    id = db.Column(db.Integer, primary_key=True)

    # 📆 Reporting Period
    report_date = db.Column(db.Date, nullable=False)

    # 🏢 Contextual References
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 💰 Financial Totals
    total_assets = db.Column(db.Numeric(12, 2), default=0.00)
    total_liabilities = db.Column(db.Numeric(12, 2), default=0.00)
    total_equity = db.Column(db.Numeric(12, 2), default=0.00)

    # 📊 Categorized Breakdown (AI & GAR enhanced)
    asset_breakdown = db.Column(JSONB, nullable=True)        # {"Bank": 10000, "Receivables": 3500}
    liability_breakdown = db.Column(JSONB, nullable=True)    # {"Payables": 2000, "Accruals": 800}
    equity_breakdown = db.Column(JSONB, nullable=True)       # {"Retained Earnings": 9000}

    # 🤖 AI / GAR Enhancements
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)  # Raw, normalized dict of figures
    ai_summary = db.Column(db.Text, nullable=True)
    ai_trend_alerts = db.Column(JSONB, nullable=True)  # e.g., {"EquityDrop": {"percentage": 18, "flagged": true}}
    gar_insights = db.Column(db.Text, nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)
    gar_context_reference = db.Column(db.String(255), nullable=True)
    is_gar_verified = db.Column(db.Boolean, default=False)
    ai_risk_score = db.Column(db.Float, nullable=True)  # e.g., 0.91 confidence of concern

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🌐 External System Integration
    external_ref_id = db.Column(db.String(100), nullable=True)  # e.g., Xero or QuickBooks link
    integration_status = db.Column(db.String(50), nullable=True)  # Synced, Error, Pending
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🔐 Metadata & Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='generated_balance_sheets')

    # 🔗 Relationships
    client = db.relationship('Client', backref='balance_sheets')
    unit = db.relationship('Unit', backref='balance_sheets')

    def __repr__(self):
        return f"<BalanceSheet client_id={self.client_id} date={self.report_date}>"

