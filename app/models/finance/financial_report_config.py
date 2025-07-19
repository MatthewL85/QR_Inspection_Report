# app/models/finance/financial_report_config.py

from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class FinancialReportConfig(db.Model):
    __tablename__ = 'financial_report_configs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "P&L Statement", "Balance Sheet"
    report_type = db.Column(db.String(100), nullable=False)  # Enum-like: P&L, BS, Tax, AgedDebtors, etc.
    config_json = db.Column(JSONB, nullable=False)  # e.g., filters, accounts, date ranges, currencies
    visibility = db.Column(db.String(50), default='AdminOnly')  # AdminOnly, PM, Director
    schedule = db.Column(db.String(50), nullable=True)  # Optional: monthly, quarterly

    # AI / GAR Readiness
    gar_summary = db.Column(db.Text, nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    gar_notes = db.Column(db.Text, nullable=True)

    # Audit
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<FinancialReportConfig {self.name}>"
