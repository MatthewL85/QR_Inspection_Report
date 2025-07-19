from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class SupplierPaymentReconciliation(db.Model):
    __tablename__ = 'supplier_payment_reconciliations'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Foreign Keys
    supplier_id = db.Column(db.Integer, db.ForeignKey('creditors.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('outstanding_supplier_invoices.id'), nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)

    # 📊 Reconciliation Metadata
    status = db.Column(db.String(50), default='Pending')  # Pending, Reconciled, Partial, Disputed, Overpaid
    reconciled_amount = db.Column(db.Numeric(12, 2), nullable=True)
    discrepancy_reason = db.Column(db.Text, nullable=True)
    reconciliation_batch_id = db.Column(db.Integer, db.ForeignKey('reconciliation_batches.id'), nullable=True)
    reconciled_at = db.Column(db.DateTime)
    reconciled_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 🤖 AI & GAR Support
    ai_flagged = db.Column(db.Boolean, default=False)
    ai_summary = db.Column(db.Text, nullable=True)
    ai_tags = db.Column(JSONB, default={})  # e.g., {"reason": "Duplicate Invoice", "confidence": 0.74}
    gar_score = db.Column(db.Float, nullable=True)
    gar_notes = db.Column(db.Text, nullable=True)
    gar_justification = db.Column(db.Text, nullable=True)
    approved_by_gar = db.Column(db.Boolean, default=False)

    # 🕵️ Audit + Traceability
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    # 🔁 Relationships
    supplier = db.relationship('Creditor', backref='payment_reconciliations')
    invoice = db.relationship('OutstandingSupplierInvoice', backref='payment_reconciliations')
    payment = db.relationship('Payment', backref='supplier_reconciliation')
    reconciled_by = db.relationship('User', foreign_keys=[reconciled_by_id])
    reconciliation_batch = db.relationship('ReconciliationBatch', backref='supplier_reconciliations')

    def __repr__(self):
        return f"<SupplierPaymentReconciliation supplier_id={self.supplier_id} invoice_id={self.invoice_id} status={self.status}>"

