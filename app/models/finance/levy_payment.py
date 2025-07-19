# app/models/finance/levy_payment.py

from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class LevyPayment(db.Model):
    __tablename__ = 'levy_payments'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    levy_id = db.Column(db.Integer, db.ForeignKey('levies.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    paid_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    levy = db.relationship('Levy', backref='payments')
    unit = db.relationship('Unit', backref='levy_payments')
    paid_by = db.relationship('User', foreign_keys=[paid_by_id])
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    # 💰 Payment Details
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), default='EUR')
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=True)       # e.g., Direct Debit, Card, Transfer
    payment_reference = db.Column(db.String(100), nullable=True)
    channel = db.Column(db.String(50), nullable=True)              # e.g., Online, In-Person, Auto

    # ✅ Status & Controls
    is_reversed = db.Column(db.Boolean, default=False)
    reversal_reason = db.Column(db.Text, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verified_by = db.relationship('User', foreign_keys=[verified_by_id])

    # 🧠 AI / GAR Fields
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)               # e.g., matched invoice, payment intent
    ai_flagged = db.Column(db.Boolean, default=False)
    ai_notes = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)

    # 🔄 3rd Party Integration
    synced_with_provider = db.Column(db.String(100), nullable=True)     # e.g., Xero, Sage
    external_payment_id = db.Column(db.String(100), nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')           # Synced, Failed, Queued

    # 🔐 Audit Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    ip_logged_from = db.Column(db.String(45), nullable=True)

    def __repr__(self):
        return f"<LevyPayment {self.amount} for Levy {self.levy_id} on Unit {self.unit_id}>"
