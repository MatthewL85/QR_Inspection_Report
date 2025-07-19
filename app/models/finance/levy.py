# app/models/finance/levy.py

from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class Levy(db.Model):
    __tablename__ = 'levies'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    client = db.relationship('Client', backref='levies')
    unit = db.relationship('Unit', backref='levies')
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    # 🧾 Core Levy Info
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    amount_due = db.Column(db.Numeric(12, 2), nullable=False)
    amount_paid = db.Column(db.Numeric(12, 2), default=0)
    due_date = db.Column(db.Date, nullable=False)
    issued_date = db.Column(db.DateTime, default=datetime.utcnow)
    currency = db.Column(db.String(10), default="EUR")

    # 💳 Payment Info
    status = db.Column(db.String(50), default='Unpaid')  # Paid, Partially Paid, Overdue
    is_installment_allowed = db.Column(db.Boolean, default=False)
    is_finalised = db.Column(db.Boolean, default=False)
    payment_reference = db.Column(db.String(100), nullable=True)

    # 🔐 Security & Compliance
    is_locked = db.Column(db.Boolean, default=False)
    reason_locked = db.Column(db.Text, nullable=True)

    # 🧠 AI / GAR Enhancements
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_recommendation = db.Column(db.String(255), nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    flagged_by_ai = db.Column(db.Boolean, default=False)
    ai_notes = db.Column(db.Text, nullable=True)
    validated_by_gar = db.Column(db.Boolean, default=False)

    # 🔄 3rd-Party Sync Integration
    synced_with_provider = db.Column(db.String(100), nullable=True)  # e.g., Xero, Sage, QuickBooks
    external_reference_id = db.Column(db.String(100), nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Failed, Outdated

    # 📎 Metadata
    reference_code = db.Column(db.String(100), nullable=True)
    related_documents = db.Column(db.String(255), nullable=True)  # Comma-separated filenames or UUIDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    ip_logged_from = db.Column(db.String(45), nullable=True)

    def __repr__(self):
        return f"<Levy {self.title} | Unit: {self.unit_id} | Amount: {self.amount_due} | Status: {self.status}>"
