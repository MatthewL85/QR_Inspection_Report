from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class LoanStatement(db.Model):
    __tablename__ = 'loan_statements'

    id = db.Column(db.Integer, primary_key=True)

    # 🔐 Multi-Tenant Context
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)

    # 🔗 Loan Relationship
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)

    # 📄 Statement Line Item
    entry_date = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_type = db.Column(db.String(100), nullable=False)  # Repayment, Interest, Fee, Adjustment, etc.
    description = db.Column(db.Text, nullable=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    balance_after = db.Column(db.Numeric(12, 2), nullable=True)
    reference = db.Column(db.String(100), nullable=True)

    # 🧾 Status Flags
    is_reconciled = db.Column(db.Boolean, default=False)
    is_reversal = db.Column(db.Boolean, default=False)
    linked_payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)

    # ☁️ 3rd-Party Integration Fields
    external_reference_id = db.Column(db.String(255), nullable=True)  # For ERP/Banking API sync
    integration_source = db.Column(db.String(100), nullable=True)  # e.g., Stripe, SEPA, QuickBooks
    sync_status = db.Column(db.String(50), default='Pending')  # Pending, Synced, Failed
    synced_at = db.Column(db.DateTime, nullable=True)

    # 🧠 AI & GAR Enhancements
    ai_tag = db.Column(db.String(100), nullable=True)
    gar_flagged = db.Column(db.Boolean, default=False)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    ai_notes = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)

    # 🛡️ Security & Audit Metadata
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    last_modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ip_logged_from = db.Column(db.String(45), nullable=True)

    # 🔁 Relationships
    loan = db.relationship('Loan', backref='loan_statements')
    company = db.relationship('Company', backref='loan_statements')
    client = db.relationship('Client', backref='loan_statements')
    unit = db.relationship('Unit', backref='loan_statements')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    last_modified_by = db.relationship('User', foreign_keys=[last_modified_by_id])
    linked_payment = db.relationship('Payment', backref='loan_statement_entry', foreign_keys=[linked_payment_id])

    def __repr__(self):
        return f"<LoanStatement LoanID={self.loan_id} Type={self.transaction_type} Amount={self.amount} Date={self.entry_date}>"

