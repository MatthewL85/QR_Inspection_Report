from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class LoanInterestRateHistory(db.Model):
    __tablename__ = 'loan_interest_rate_history'

    id = db.Column(db.Integer, primary_key=True)

    # 🔐 Ownership Scope
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    # 🔗 Loan Reference
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)

    # 📊 Rate Change Data
    old_rate = db.Column(db.Numeric(5, 3), nullable=True)
    new_rate = db.Column(db.Numeric(5, 3), nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    rate_type = db.Column(db.String(50), nullable=True)  # Fixed, Variable, Tracker, etc.
    source_document_url = db.Column(db.String(255), nullable=True)

    # 🤖 AI & GAR Smart Fields
    gar_risk_flag = db.Column(db.Boolean, default=False)
    ai_classification = db.Column(db.String(100), nullable=True)  # e.g., Above market avg
    notes = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)

    # 🔄 3rd Party Sync Fields
    synced_with_provider = db.Column(db.String(100), nullable=True)  # e.g., Xero, Sage, Bank API
    external_reference_id = db.Column(db.String(100), nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Failed, Outdated

    # 🛡️ Metadata
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    last_modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    ip_logged_from = db.Column(db.String(45), nullable=True)

    # 🔗 Relationships
    loan = db.relationship('Loan', backref='rate_history')
    company = db.relationship('Company', backref='loan_rate_changes')
    client = db.relationship('Client', backref='loan_rate_changes')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    last_modified_by = db.relationship('User', foreign_keys=[last_modified_by_id])

    def __repr__(self):
        return f"<LoanRateChange LoanID={self.loan_id} {self.old_rate}→{self.new_rate} on {self.effective_date}>"
