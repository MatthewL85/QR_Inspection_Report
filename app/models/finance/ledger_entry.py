# app/models/finance/ledger_entry.py

from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates

class LedgerEntry(db.Model):
    __tablename__ = 'ledger_entries'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Account Relationships
    debit_account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'), nullable=False)
    credit_account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'), nullable=False)
    debit_account = db.relationship('BankAccount', foreign_keys=[debit_account_id], backref='debit_entries')
    credit_account = db.relationship('BankAccount', foreign_keys=[credit_account_id], backref='credit_entries')

    # 💰 Financial Data
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='EUR', index=True)
    entry_type = db.Column(db.String(50), nullable=False, index=True)  # e.g., Payment, Transfer, Adjustment
    reference = db.Column(db.String(100), nullable=True)
    memo = db.Column(db.Text, nullable=True)

    # 🕓 Timestamp & Origin
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    # ✅ Audit & Reconciliation
    is_reconciled = db.Column(db.Boolean, default=False)
    reconciliation_id = db.Column(db.Integer, db.ForeignKey('bank_reconciliations.id'), nullable=True)
    reconciliation = db.relationship('BankReconciliation', backref='ledger_entries')

    # 🤖 AI & GAR Enhancements
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    gar_notes = db.Column(db.Text, nullable=True)
    ai_flagged = db.Column(db.Boolean, default=False)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)  # ['Admin', 'Accountant']

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔗 External Sync References
    third_party_match = db.Column(db.String(100), nullable=True)  # e.g., Xero or QuickBooks Tx ID
    external_system = db.Column(db.String(100), nullable=True)  # e.g., QuickBooks, Xero
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Failed, Manual
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 📅 Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LedgerEntry {self.amount} | {self.debit_account_id} → {self.credit_account_id} | {self.entry_type}>"
