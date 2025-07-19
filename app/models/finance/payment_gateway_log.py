# app/models/finance/payment_gateway_log.py

from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class PaymentGatewayLog(db.Model):
    __tablename__ = 'payment_gateway_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Associations
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 💳 Gateway Metadata
    provider = db.Column(db.String(50), nullable=False)  # Stripe, GoCardless, Revolut, etc.
    event_type = db.Column(db.String(100), nullable=True)  # payment_intent.succeeded, invoice.paid
    status_code = db.Column(db.String(20), nullable=True)  # 200, 400, 500
    response_message = db.Column(db.Text, nullable=True)  # Optional message from gateway

    # 📦 Raw & Parsed Payloads
    raw_payload = db.Column(JSONB, nullable=True)  # Raw response/request JSON
    parsed_data = db.Column(JSONB, nullable=True)  # Optional: AI parsed or system-extracted

    # 🔁 Status Tracking
    status = db.Column(db.String(50), default='received')  # received, processed, failed, flagged
    is_flagged = db.Column(db.Boolean, default=False)
    retry_attempts = db.Column(db.Integer, default=0)
    reconciled = db.Column(db.Boolean, default=False)
    matched_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)  # Optional match

    # 🧠 AI / GAR Readiness
    gar_flag_reason = db.Column(db.String(255), nullable=True)
    ai_notes = db.Column(db.Text, nullable=True)
    extracted_metadata = db.Column(JSONB, nullable=True)
    gar_context_reference = db.Column(db.String(255), nullable=True)

    # 🧾 Logging & Timeline
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 🔗 Relationships
    transaction = db.relationship('Transaction', foreign_keys=[transaction_id], backref='gateway_logs')
    matched_transaction = db.relationship('Transaction', foreign_keys=[matched_transaction_id], post_update=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<PaymentGatewayLog provider={self.provider} event={self.event_type} status={self.status}>"
