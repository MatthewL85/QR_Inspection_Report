# app/models/finance/ledger_batch.py

from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates

class LedgerBatch(db.Model):
    __tablename__ = 'ledger_batches'

    id = db.Column(db.Integer, primary_key=True)

    # 📌 Metadata
    batch_name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    batch_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 🔢 Financial Summary
    total_entries = db.Column(db.Integer, default=0)
    total_debit = db.Column(db.Numeric(14, 2), default=0)
    total_credit = db.Column(db.Numeric(14, 2), default=0)
    currency = db.Column(db.String(10), nullable=False, default='EUR', index=True)

    # ✅ Status & Validation
    is_balanced = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default='Draft', nullable=False, index=True)  # Draft, Posted, Reconciled, Archived
    posted_at = db.Column(db.DateTime, nullable=True)
    posted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    posted_by = db.relationship('User', foreign_keys=[posted_by_id])

    # 🔐 Audit & Ownership
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔗 Relationships
    ledger_entries = db.relationship(
        'LedgerEntry',
        backref='ledger_batch',
        lazy=True,
        cascade="all, delete",
        foreign_keys='LedgerEntry.ledger_batch_id'
    )

    # 🤖 AI / GAR Integration
    gar_context_reference = db.Column(db.String(100), nullable=True)
    gar_notes = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)

    # 🔌 3rd-Party Integration
    third_party_batch_id = db.Column(db.String(100), nullable=True)  # e.g., Xero or QuickBooks ID
    external_system = db.Column(db.String(100), nullable=True)       # e.g., 'Xero', 'QuickBooks'
    sync_status = db.Column(db.String(50), default='Pending')        # Synced, Failed, Manual
    last_synced_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<LedgerBatch {self.batch_name} | Status: {self.status} | Total Debit: {self.total_debit}>"

