from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class OutstandingBalance(db.Model):
    __tablename__ = 'outstanding_balances'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Entity Relationships
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    service_charge_id = db.Column(db.Integer, db.ForeignKey('service_charges.id'), nullable=True)
    levy_id = db.Column(db.Integer, db.ForeignKey('levies.id'), nullable=True)
    arrears_id = db.Column(db.Integer, db.ForeignKey('arrears.id'), nullable=True)

    unit = db.relationship("Unit", backref="outstanding_balances")
    client = db.relationship("Client", backref="outstanding_balances")
    invoice = db.relationship("Invoice", backref="outstanding_balance", uselist=False)
    service_charge = db.relationship("ServiceCharge", backref="outstanding_balance", uselist=False)
    levy = db.relationship("Levy", backref="outstanding_balance", uselist=False)
    arrears = db.relationship("Arrears", backref="outstanding_balance", uselist=False)

    # 💸 Core Financials
    original_amount = db.Column(db.Numeric(12, 2), nullable=False)
    outstanding_amount = db.Column(db.Numeric(12, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    last_payment_date = db.Column(db.Date, nullable=True)
    is_overdue = db.Column(db.Boolean, default=False)
    days_overdue = db.Column(db.Integer, nullable=True)

    # 📊 Status & Lifecycle
    status = db.Column(db.String(50), default="Unpaid")  # Unpaid, Partially Paid, Paid, Written Off
    reference_source = db.Column(db.String(50), nullable=True)  # invoice, levy, service_charge, arrears
    is_finalised = db.Column(db.Boolean, default=False)
    is_flagged_for_escalation = db.Column(db.Boolean, default=False)
    escalation_reason = db.Column(db.Text, nullable=True)

    # 🧠 AI / GAR Smart Fields
    ai_prediction = db.Column(db.String(100), nullable=True)       # e.g., "Likely to default"
    ai_score = db.Column(db.Float, nullable=True)                  # Confidence score
    gar_flagged = db.Column(db.Boolean, default=False)
    gar_notes = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    gar_risk_score = db.Column(db.Float, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)
    anomaly_detected = db.Column(db.Boolean, default=False)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🕒 Audit Trail
    first_recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<OutstandingBalance unit_id={self.unit_id} amount={self.outstanding_amount} overdue={self.is_overdue}>"

