from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB


class ReconciliationBatch(db.Model):
    __tablename__ = 'reconciliation_batches'

    id = db.Column(db.Integer, primary_key=True)

    # 📅 Batch Meta
    reconciliation_date = db.Column(db.Date, nullable=False)
    statement_period_start = db.Column(db.Date, nullable=False)
    statement_period_end = db.Column(db.Date, nullable=False)

    # 🔗 Context
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)  # Optional: unit-level recon

    # 💼 Financial Info
    opening_balance = db.Column(db.Numeric(12, 2), nullable=True)
    closing_balance = db.Column(db.Numeric(12, 2), nullable=True)
    reconciled_balance = db.Column(db.Numeric(12, 2), nullable=True)
    is_reconciled = db.Column(db.Boolean, default=False)
    reconciliation_status = db.Column(db.String(50), default="Pending")  # ✅ Optional enum: Pending, In Progress, Reconciled, Failed

    # 📄 Matched/Unmatched Line Items
    matched_transactions = db.Column(JSONB, nullable=True)     # [{transaction_id, amount, confidence}]
    unmatched_transactions = db.Column(JSONB, nullable=True)   # [{reason, reference, amount, suggested_action}]

    # 🤖 AI + GAR Enhancements
    ai_flags = db.Column(JSONB, nullable=True)                 # AI anomaly findings, e.g. {"type": "duplicate", "transaction_id": 999}
    gar_summary = db.Column(db.Text, nullable=True)
    gar_score = db.Column(db.String(20), nullable=True)        # A+, B, C, Warning
    gar_recommendation = db.Column(db.Text, nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    requires_human_review = db.Column(db.Boolean, default=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 📊 Extended Metadata
    source_type = db.Column(db.String(50), default="manual")   # manual, csv_upload, api_sync, smart_link
    batch_notes = db.Column(db.Text, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)

    # 🔒 Audit + Security
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔗 Relationships
    account = db.relationship('Account', backref='reconciliation_batches')
    client = db.relationship('Client', backref='reconciliation_batches')
    unit = db.relationship('Unit', backref='reconciliation_batches')
    performed_by = db.relationship('User', backref='reconciliation_actions')

    def __repr__(self):
        return f"<ReconciliationBatch id={self.id} client_id={self.client_id} status={self.reconciliation_status}>"
