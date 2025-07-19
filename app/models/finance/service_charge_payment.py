from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class ServiceChargePayment(db.Model):
    __tablename__ = 'service_charge_payments'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    service_charge_id = db.Column(
        db.Integer,
        db.ForeignKey('service_charges.id', use_alter=True, name='fk_scp_service_charge', deferrable=True, initially='DEFERRED'),
        nullable=False
    )
    unit_id = db.Column(
        db.Integer,
        db.ForeignKey('units.id', use_alter=True, name='fk_scp_unit', deferrable=True, initially='DEFERRED'),
        nullable=False
    )
    paid_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', use_alter=True, name='fk_scp_paid_by', deferrable=True, initially='DEFERRED'),
        nullable=True
    )

    # 💰 Payment Info
    amount_paid = db.Column(db.Numeric(12, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=True)
    receipt_reference = db.Column(db.String(100), nullable=True)
    transaction_reference = db.Column(db.String(100), nullable=True)
    currency = db.Column(db.String(10), default="EUR")

    # 🧾 Categorization / Context
    allocation_notes = db.Column(db.String(255), nullable=True)
    is_partial = db.Column(db.Boolean, default=False)
    is_late = db.Column(db.Boolean, default=False)
    is_reversed = db.Column(db.Boolean, default=False)
    reversal_reason = db.Column(db.Text, nullable=True)
    is_refundable = db.Column(db.Boolean, default=True)
    is_reconciled = db.Column(db.Boolean, default=False)
    reconciliation_batch_id = db.Column(
        db.Integer,
        db.ForeignKey('reconciliation_batches.id', use_alter=True, name='fk_scp_recon_batch', deferrable=True, initially='DEFERRED'),
        nullable=True
    )

    # 🤖 AI / GAR Integration
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    ai_flagged = db.Column(db.Boolean, default=False)
    ai_confidence_score = db.Column(db.Float, nullable=True)
    gar_notes = db.Column(db.Text, nullable=True)
    approved_by_gar = db.Column(db.Boolean, default=False)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🔐 Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    created_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', use_alter=True, name='fk_scp_created_by', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    modified_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    modified_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', use_alter=True, name='fk_scp_modified_by', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    modified_by = db.relationship('User', foreign_keys=[modified_by_id])

    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    # 🔁 Relationships
    service_charge = db.relationship('ServiceCharge', backref='payments')
    unit = db.relationship('Unit', backref='service_charge_payments')
    paid_by = db.relationship('User', foreign_keys=[paid_by_id])
    reconciliation_batch = db.relationship('ReconciliationBatch', backref='service_charge_payments')

    def __repr__(self):
        return f"<ServiceChargePayment unit_id={self.unit_id} | amount={self.amount_paid} | method={self.payment_method}>"
