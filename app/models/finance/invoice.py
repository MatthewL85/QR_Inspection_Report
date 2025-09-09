from datetime import datetime
from app.extensions import db

class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Foreign Keys
    work_order_id = db.Column(
        db.Integer,
        db.ForeignKey('work_orders.id', use_alter=True, name='fk_invoice_work_order', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    service_charge_id = db.Column(
        db.Integer,
        db.ForeignKey('service_charges.id', use_alter=True, name='fk_invoice_service_charge', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    levy_id = db.Column(
        db.Integer,
        db.ForeignKey('levies.id', use_alter=True, name='fk_invoice_levy', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    contractor_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', use_alter=True, name='fk_invoice_contractor', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    approved_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', use_alter=True, name='fk_invoice_approved_by', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    finance_batch_id = db.Column(
        db.Integer,
        db.ForeignKey('finance_batches.id', use_alter=True, name='fk_invoice_finance_batch', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    payment_run_id = db.Column(
        db.Integer,
        db.ForeignKey('payment_runs.id', use_alter=True, name='fk_invoice_payment_run', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    unit_id = db.Column(
        db.Integer,
        db.ForeignKey('units.id', use_alter=True, name='fk_invoice_unit', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    company = db.relationship('Company', back_populates='invoices', overlaps="related_invoices")

    # 📄 Invoice Metadata
    invoice_number = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    tax_rate = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(10), default="EUR")
    invoice_date = db.Column(db.Date, default=datetime.utcnow)
    due_date = db.Column(db.Date, nullable=True)
    days_overdue = db.Column(db.Integer, default=0)
    arrears_category = db.Column(db.String(50), nullable=True)
    file_url = db.Column(db.String(255))
    notes = db.Column(db.Text)

    # 🔄 Status Flags
    status = db.Column(db.String(50), default='Pending')
    submitted_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    rejected_reason = db.Column(db.Text)
    included_in_payment_run = db.Column(db.Boolean, default=False)
    paid_at = db.Column(db.DateTime)

    # 🔍 Source Clarity
    charge_type = db.Column(db.String(50), nullable=True)

    # 💸 Late Fees
    auto_applied_late_fee = db.Column(db.Numeric(10, 2), default=0)
    auto_applied_interest = db.Column(db.Numeric(10, 2), default=0)
    late_fee_waived = db.Column(db.Boolean, default=False)
    waiver_reason = db.Column(db.Text, nullable=True)

    # 🔌 3rd Party
    external_invoice_id = db.Column(db.String(100), nullable=True)
    integration_status = db.Column(db.String(50), nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🤖 AI Parsing
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Compliance
    gar_compliance_score = db.Column(db.Float, nullable=True)
    gar_risk_flag = db.Column(db.String(50), nullable=True)
    gar_justification_notes = db.Column(db.Text, nullable=True)
    is_flagged_for_audit = db.Column(db.Boolean, default=False)
    validated_by_gar = db.Column(db.Boolean, default=False)

    # 💬 GAR Chat
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🔐 Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔁 Relationships
    work_order = db.relationship('WorkOrder', backref=db.backref('invoice', uselist=False))
    service_charge = db.relationship('ServiceCharge', back_populates='invoice', overlaps="service_charge_ref,invoices")
    levy = db.relationship('Levy', backref='invoices')
    contractor = db.relationship('User', foreign_keys=[contractor_id], backref='submitted_invoices')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='approved_invoices')
    unit = db.relationship('Unit', backref='invoices')
    finance_batch = db.relationship('FinanceBatch', back_populates='invoices')
    payment_run = db.relationship('PaymentRun', back_populates='invoices')

    late_fee_logs = db.relationship(
        'LateFeeTransactionLog',
        back_populates='invoice',
        lazy='dynamic',
        foreign_keys='LateFeeTransactionLog.invoice_id'
    )

    def __repr__(self):
        return f"<Invoice {self.invoice_number} | Type: {self.charge_type} | Status: {self.status}>"

