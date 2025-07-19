from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class BankReconciliation(db.Model):
    __tablename__ = 'bank_reconciliations'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Associations
    account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'), nullable=False)
    reconciliation_batch_id = db.Column(db.Integer, db.ForeignKey('reconciliation_batches.id'), nullable=True)
    reconciliation_engine_id = db.Column(db.Integer, db.ForeignKey('reconciliation_engine.id'), nullable=True)

    # 📆 Statement Period & Balances
    statement_date = db.Column(db.Date, nullable=False)
    statement_opening_balance = db.Column(db.Numeric(14, 2), nullable=False)
    statement_closing_balance = db.Column(db.Numeric(14, 2), nullable=False)
    platform_recorded_balance = db.Column(db.Numeric(14, 2), nullable=False)
    difference = db.Column(db.Numeric(14, 2), nullable=False)

    # ✅ Status & Notes
    status = db.Column(db.String(50), default='Unreconciled')  # Unreconciled, Partially Reconciled, Reconciled
    notes = db.Column(db.Text, nullable=True)
    flagged_entries = db.Column(JSONB, default={})  # e.g., [{"tx_id": 101, "reason": "Date mismatch"}]

    # 🌐 Integration & External Mapping
    external_reference = db.Column(db.String(150), nullable=True)  # e.g., feed ID from Plaid/Xero
    integration_status = db.Column(db.String(50), nullable=True)   # Synced, Pending, Failed
    synced_at = db.Column(db.DateTime, nullable=True)

    # 🤖 AI & GAR Enhancements
    ai_flagged = db.Column(db.Boolean, default=False)
    ai_discrepancy_summary = db.Column(db.Text, nullable=True)
    ai_recommendation = db.Column(db.Text, nullable=True)
    ai_confidence_score = db.Column(db.Float, nullable=True)  # Reconciliation confidence score
    gar_review_score = db.Column(db.Float, nullable=True)      # 0–1 trust flag
    gar_alerts = db.Column(JSONB, default={})
    parsed_summary = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    is_gar_verified = db.Column(db.Boolean, default=False)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔐 Security, Audit & Ownership
    reconciled_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reconciled_by = db.relationship('User', foreign_keys=[reconciled_by_id])
    reconciled_at = db.Column(db.DateTime, nullable=True)

    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_bank_reconciliations')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔁 Relationships
    account = db.relationship('BankAccount', backref='bank_reconciliations')
    reconciliation_batch = db.relationship('ReconciliationBatch', backref='bank_reconciliations')
    reconciliation_engine = db.relationship('ReconciliationEngine', backref='bank_reconciliations')

    def __repr__(self):
        return f"<BankReconciliation account_id={self.account_id} status={self.status} difference={self.difference}>"



