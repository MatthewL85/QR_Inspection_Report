# app/models/finance/ledger_journal.py

from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates

class LedgerJournal(db.Model):
    __tablename__ = 'ledger_journals'

    id = db.Column(db.Integer, primary_key=True)

    # 📌 Metadata
    journal_name = db.Column(db.String(255), nullable=False, index=True)
    journal_type = db.Column(db.String(100), nullable=False)  # e.g., Sales, Purchase, Cash, Adjustment
    description = db.Column(db.Text, nullable=True)
    journal_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 🧾 Source Link (generic, expandable)
    source_document_type = db.Column(db.String(100), nullable=True)
    source_document_id = db.Column(db.Integer, nullable=True)

    # 📊 Status Tracking
    status = db.Column(db.String(50), default='Draft', nullable=False)  # Draft, Validated, Posted, Archived
    is_locked = db.Column(db.Boolean, default=False)
    posted_at = db.Column(db.DateTime, nullable=True)
    posted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    posted_by = db.relationship('User', foreign_keys=[posted_by_id])

    # 🔐 Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    # 🔗 Relationships
    ledger_entries = db.relationship('LedgerEntry', backref='journal', lazy=True, cascade="all, delete")

    # 🤖 AI & GAR Integration
    gar_context_reference = db.Column(db.String(100), nullable=True)
    gar_notes = db.Column(db.Text, nullable=True)
    ai_recommendation = db.Column(db.Text, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)  # e.g., ['Admin', 'Accountant']

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔌 External Sync / API Compatibility
    external_reference = db.Column(db.String(100), nullable=True)
    external_reference_system = db.Column(db.String(100), nullable=True)  # e.g., QuickBooks, Xero
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Failed, Manual
    last_synced_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<LedgerJournal {self.journal_name} | Type: {self.journal_type} | Status: {self.status}>"
