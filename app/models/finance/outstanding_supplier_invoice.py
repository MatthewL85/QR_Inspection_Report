from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB


class OutstandingSupplierInvoice(db.Model):
    __tablename__ = 'outstanding_supplier_invoices'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Associations
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractors.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 📄 Invoice Details
    invoice_number = db.Column(db.String(100), nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    amount_due = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='Unpaid')  # Unpaid, Partially Paid, Paid, Disputed

    # 📎 Attachments
    file_path = db.Column(db.String(255), nullable=True)

    # 🧠 AI & GAR Enhancements
    ai_extracted_data = db.Column(JSONB, nullable=True)
    gar_validated = db.Column(db.Boolean, default=False)
    reason_for_dispute = db.Column(db.String(255), nullable=True)
    smart_tags = db.Column(JSONB, nullable=True)

    # 🔄 Reconciliation Engine Integration
    reconciliation_status = db.Column(db.String(50), default='Pending')  # Pending, Matched, Failed, Manual Review
    matched_transaction_id = db.Column(db.Integer, db.ForeignKey('bank_transactions.id'), nullable=True)

    # 📅 Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔗 Relationships
    contractor = db.relationship('Contractor', backref='outstanding_invoices')
    client = db.relationship('Client', backref='outstanding_invoices')
    unit = db.relationship('Unit', backref='supplier_invoices')
    work_order = db.relationship('WorkOrder', backref='supplier_invoice')
    uploaded_by = db.relationship('User', backref='uploaded_supplier_invoices')
    matched_transaction = db.relationship('BankTransaction', backref='matched_invoices', foreign_keys=[matched_transaction_id])

    def __repr__(self):
        return f"<OutstandingSupplierInvoice #{self.invoice_number} | Amount Due: {self.amount_due}>"

