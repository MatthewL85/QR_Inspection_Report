from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class Refund(db.Model):
    __tablename__ = 'refunds'

    id = db.Column(db.Integer, primary_key=True)

    # 💸 Refund Context
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)           # Optional: member/tenant scope
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    original_payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)
    reconciliation_batch_id = db.Column(db.Integer, db.ForeignKey('reconciliation_batches.id'), nullable=True)

    # 📄 Refund Details
    refund_reason = db.Column(db.String(255), nullable=False)
    refund_amount = db.Column(db.Numeric(12, 2), nullable=False)
    refund_method = db.Column(db.String(100), nullable=False)  # Bank Transfer, Cheque, Card, Other
    refund_reference = db.Column(db.String(100), nullable=True)
    refunded_to = db.Column(db.String(255), nullable=True)     # Recipient name or account

    refund_status = db.Column(db.String(50), default="Pending")  # Pending, Approved, Refunded, Rejected, Failed
    is_finalised = db.Column(db.Boolean, default=False)
    is_reconciled = db.Column(db.Boolean, default=False)

    # 🧠 AI + GAR Intelligence
    ai_validated = db.Column(db.Boolean, default=False)
    ai_confidence = db.Column(db.Float, nullable=True)                     # 0.0–1.0
    ai_notes = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    smart_tags = db.Column(JSONB, nullable=True)                           # e.g., {"type": "overpayment", "source": "system"}
    
    gar_flagged = db.Column(db.Boolean, default=False)
    gar_reason = db.Column(db.Text, nullable=True)
    gar_score = db.Column(db.String(20), nullable=True)
    approved_by_gar = db.Column(db.Boolean, default=False)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔐 Security + Meta Audit
    issued_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    # 🔗 Relationships
    client = db.relationship('Client', backref='refunds')
    unit = db.relationship('Unit', backref='refunds')
    account = db.relationship('Account', backref='refunds')
    original_payment = db.relationship('Payment', backref='linked_refunds')
    issued_by = db.relationship('User', backref='issued_refunds')
    reconciliation_batch = db.relationship('ReconciliationBatch', backref='linked_refunds')

    def __repr__(self):
        return f"<Refund id={self.id} | amount={self.refund_amount} | status={self.refund_status}>"

