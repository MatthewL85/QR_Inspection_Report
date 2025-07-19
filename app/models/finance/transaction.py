from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    finance_batch_id = db.Column(db.Integer, db.ForeignKey('finance_batches.id'), nullable=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)

    # 💸 Transaction Details
    amount = db.Column(db.Numeric(precision=12, scale=2), nullable=False)
    currency = db.Column(db.String(10), default='EUR', nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # payment, credit, refund, reversal
    description = db.Column(db.Text, nullable=True)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)

    # 💳 Payment Info
    payment_method = db.Column(db.String(50), nullable=True)  # Stripe, SEPA, GoCardless, Cheque
    payment_status = db.Column(db.String(50), default='Pending')  # Pending, Completed, Failed, Refunded
    payment_reference = db.Column(db.String(100), nullable=True)
    gateway_response = db.Column(JSONB, nullable=True)  # full JSON from provider
    transaction_hash = db.Column(db.String(100), nullable=True)  # future-proof blockchain-ready

    # 🔁 Status Flags
    is_reversed = db.Column(db.Boolean, default=False)
    reversed_reason = db.Column(db.Text, nullable=True)
    reversal_date = db.Column(db.DateTime, nullable=True)

    # 🧠 AI / GAR Integration
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    gar_notes = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    gar_confidence_score = db.Column(db.Float, nullable=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔐 GDPR & Audit
    payer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔁 Relationships
    unit = db.relationship("Unit", backref="transactions")
    client = db.relationship("Client", backref="transactions")
    invoice = db.relationship("Invoice", backref="transactions")
    finance_batch = db.relationship("FinanceBatch", backref="transactions")
    payer = db.relationship("User", foreign_keys=[payer_id])
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<Transaction {self.transaction_type} €{self.amount} [{self.payment_status}]>"


