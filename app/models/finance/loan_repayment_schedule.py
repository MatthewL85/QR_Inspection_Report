from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class LoanRepaymentSchedule(db.Model):
    __tablename__ = 'loan_repayment_schedules'

    id = db.Column(db.Integer, primary_key=True)

    # 🔐 Multi-Tenant Context
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)

    # 🔁 Loan Reference
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)

    # 📅 Repayment Details
    due_date = db.Column(db.Date, nullable=False)
    payment_amount = db.Column(db.Numeric(12, 2), nullable=False)
    paid_amount = db.Column(db.Numeric(12, 2), default=0.00)
    paid_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), default='Pending')  # Pending, Paid, Partial, Overdue, Reversed

    # 🔄 Late Fee / Interest Handling
    is_overdue = db.Column(db.Boolean, default=False)
    late_fee_applied = db.Column(db.Numeric(10, 2), default=0.00)
    interest_penalty = db.Column(db.Numeric(10, 2), default=0.00)
    waived = db.Column(db.Boolean, default=False)
    waiver_reason = db.Column(db.String(255), nullable=True)

    # 💳 3rd-Party Gateway Integration
    payment_gateway = db.Column(db.String(100), nullable=True)  # Stripe, GoCardless, etc.
    external_payment_id = db.Column(db.String(255), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Failed, Retrying
    synced_at = db.Column(db.DateTime, nullable=True)

    # 🧠 AI & GAR Fields
    ai_prediction_flag = db.Column(db.Boolean, default=False)
    gar_risk_flag = db.Column(db.Boolean, default=False)
    parsed_notes = db.Column(db.Text, nullable=True)
    extracted_terms = db.Column(JSONB, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)

    # 📄 Meta
    payment_reference = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    last_modified_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    last_modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ip_logged_from = db.Column(db.String(45), nullable=True)

    # 🔗 Relationships
    loan = db.relationship('Loan', backref='repayment_schedule')
    company = db.relationship('Company', backref='loan_repayments')
    client = db.relationship('Client', backref='loan_repayments')
    unit = db.relationship('Unit', backref='loan_repayments')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    last_modified_by = db.relationship('User', foreign_keys=[last_modified_by_id])

    def __repr__(self):
        return f"<LoanRepaymentSchedule LoanID={self.loan_id} Due={self.due_date} Amount={self.payment_amount}>"
