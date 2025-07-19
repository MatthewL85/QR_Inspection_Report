from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 🧍 Parties
    payer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # member / Tenant
    payee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Contractor / Mgmt Co
    payer = db.relationship('User', foreign_keys=[payer_id])
    payee = db.relationship('User', foreign_keys=[payee_id])

    # 🔗 Related Objects
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    account = db.relationship('Account', backref='payments')

    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)
    transaction = db.relationship('Transaction', backref='payments')

    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    invoice = db.relationship('Invoice', backref='payments')

    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    unit = db.relationship('Unit', backref='payments')

    # 💸 Payment Details
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), default="EUR")
    method = db.Column(db.String(50))  # e.g., "Bank Transfer", "Stripe", etc.
    reference = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default="Pending")  # Pending, Completed, Failed, Refunded
    is_refundable = db.Column(db.Boolean, default=True)

    # 🧾 Reconciliation Engine Fields
    is_reconciled = db.Column(db.Boolean, default=False)
    reconciliation_batch_id = db.Column(db.String(100), nullable=True)
    reconciliation_status = db.Column(db.String(50), default='Unmatched')  # Unmatched, Partial, Matched
    matched_transaction_id = db.Column(db.Integer, db.ForeignKey('bank_transactions.id'), nullable=True)

    # 🔐 Security & Logging
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))

    # 🧠 AI / GAR Support
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_verified = db.Column(db.Boolean, default=False)
    ai_classification = db.Column(db.String(100), nullable=True)  # e.g., “arrears settlement”
    gar_context_reference = db.Column(db.String(100), nullable=True)
    flagged_by_ai = db.Column(db.Boolean, default=False)
    ai_notes = db.Column(db.Text)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 📎 External Integration
    external_provider = db.Column(db.String(50), nullable=True)           # e.g., Stripe, GoCardless
    external_transaction_ref = db.Column(db.String(100), nullable=True)
    synced_at = db.Column(db.DateTime, nullable=True)
    integration_status = db.Column(db.String(50), nullable=True)          # Synced, Failed, Skipped

    def __repr__(self):
        return f"<Payment {self.id} | {self.amount} {self.currency} | Status: {self.status}>"
