from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class ServiceCharge(db.Model):
    __tablename__ = 'service_charges'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)

    client = db.relationship('Client', backref='service_charges')
    unit = db.relationship('Unit', backref='service_charges')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    payment = db.relationship('Payment', backref='service_charges')

    # 📅 Billing Information
    year = db.Column(db.Integer, nullable=False)
    billing_period = db.Column(db.String(50), default='Annual')  # Monthly, Quarterly, Annual, etc.
    charge_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.Date, nullable=False)
    charge_cycle_code = db.Column(db.String(50), nullable=True)  # Optional: internal code for recurring cycles

    # 💰 Financials
    amount_due = db.Column(db.Numeric(12, 2), nullable=False)
    amount_paid = db.Column(db.Numeric(12, 2), default=0)
    currency = db.Column(db.String(10), default='EUR')
    status = db.Column(db.String(50), default='Unpaid')  # Paid, Partially Paid, Overdue, Unpaid

    # 🔖 Identifiers & Description
    reference = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(255), nullable=True)

    # 🧠 AI / GAR Fields
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)  # e.g., breakdowns, match confidence
    ai_recommendation = db.Column(db.String(255), nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    flagged_by_ai = db.Column(db.Boolean, default=False)
    ai_notes = db.Column(db.Text, nullable=True)
    gar_compliance_score = db.Column(db.Float, nullable=True)
    approved_by_gar = db.Column(db.Boolean, default=False)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🧾 Invoice Integration
    invoice = db.relationship(
        'Invoice',
        backref='service_charge_ref',
        uselist=False,
        primaryjoin="ServiceCharge.id==Invoice.service_charge_id"
    )

    # 🔍 Status / Reconciliation
    is_finalised = db.Column(db.Boolean, default=False)
    is_reconciled = db.Column(db.Boolean, default=False)
    reconciliation_batch_id = db.Column(db.Integer, db.ForeignKey('reconciliation_batches.id'), nullable=True)

    # 🔐 Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    # 🔁 Relationships
    reconciliation_batch = db.relationship('ReconciliationBatch', backref='linked_service_charges')

    def __repr__(self):
        return f"<ServiceCharge {self.id} | Unit: {self.unit_id} | {self.amount_due} {self.currency} | Status: {self.status}>"
