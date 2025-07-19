from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class DebitNote(db.Model):
    __tablename__ = 'debit_notes'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # issued by
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # issued to (optional)

    # 💳 Financial Info
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), default='EUR')
    reason = db.Column(db.Text, nullable=False)
    issue_date = db.Column(db.Date, default=datetime.utcnow)
    due_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), default='Pending')  # Pending, Sent, Paid, Cancelled, Disputed

    # 🔁 Ledger Link (if posted)
    ledger_entry_id = db.Column(db.Integer, db.ForeignKey('ledger_entries.id'), nullable=True)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entries.id'), nullable=True)

    # ⚖️ Dispute Handling
    is_disputed = db.Column(db.Boolean, default=False)
    dispute_reason = db.Column(db.Text, nullable=True)
    dispute_resolution_notes = db.Column(db.Text, nullable=True)
    dispute_resolution_status = db.Column(db.String(50), nullable=True)  # Resolved, Escalated, Denied

    # 🔐 Access Control
    visibility_scope = db.Column(db.String(100), default='Internal')  # Internal, Client, Unit, Director

    # 📎 Attachments & Notes
    attachment_url = db.Column(db.String(255), nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)

    # 🧠 AI / GAR Enhancements
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_tags = db.Column(JSONB, nullable=True)
    gar_feedback = db.Column(db.Text, nullable=True)
    gar_chat_thread_id = db.Column(db.String(100), nullable=True)  # GAR Q&A reference

    # 🌐 API / External System Support
    external_reference = db.Column(db.String(100), nullable=True)
    external_system = db.Column(db.String(100), nullable=True)
    integration_status = db.Column(db.String(50), default='Pending')  # Pending, Synced, Failed
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🕵️ Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 🔁 Relationships
    invoice = db.relationship('Invoice', backref='debit_notes', foreign_keys=[invoice_id])
    client = db.relationship('Client', backref='debit_notes')
    unit = db.relationship('Unit', backref='debit_notes')
    creator = db.relationship('User', foreign_keys=[created_by])
    updater = db.relationship('User', foreign_keys=[updated_by])
    issuer = db.relationship('User', foreign_keys=[user_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])

    ledger_entry = db.relationship('LedgerEntry', backref='linked_debit_notes', foreign_keys=[ledger_entry_id])
    journal_entry = db.relationship('JournalEntry', backref='linked_debit_notes', foreign_keys=[journal_entry_id])
