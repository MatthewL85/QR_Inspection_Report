# app/models/finance/payment_adjustment.py

from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class PaymentAdjustment(db.Model):
    __tablename__ = 'payment_adjustments'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    # ⚖️ Adjustment Details
    adjustment_type = db.Column(db.String(50), nullable=False)  # e.g., Overpayment, Write-off, Correction, Reallocation
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # 📅 Dates
    adjustment_date = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔍 Audit & Security
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_archived = db.Column(db.Boolean, default=False)

    # 🧠 GAR / AI Enhancements
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    gar_feedback = db.Column(JSONB, nullable=True)               # e.g., {"flagged": true, "recommendation": "Needs approval"}
    gar_chat_reference = db.Column(db.String(255), nullable=True)
    ai_tags = db.Column(JSONB, nullable=True)                    # e.g., ["adjustment", "refund", "suspicious"]

    # 🌐 Integration & API Tracking
    external_reference = db.Column(db.String(100), nullable=True)
    external_source = db.Column(db.String(100), nullable=True)
    synced_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<PaymentAdjustment #{self.id} | Type: {self.adjustment_type} | Amount: {self.amount}>"
