from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class Loan(db.Model):
    __tablename__ = 'loans'

    id = db.Column(db.Integer, primary_key=True)

    # 🔐 Ownership & Context
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)

    # 💰 Loan Terms
    lender_name = db.Column(db.String(255), nullable=False)
    loan_amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), default='EUR')
    interest_rate = db.Column(db.Float, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    repayment_frequency = db.Column(db.String(50), nullable=True)
    repayment_method = db.Column(db.String(50), nullable=True)
    is_interest_only = db.Column(db.Boolean, default=False)
    balloon_payment_due = db.Column(db.Boolean, default=False)
    grace_period_months = db.Column(db.Integer, nullable=True)

    # 📄 Contract & Compliance
    contract_reference = db.Column(db.String(100), nullable=True)
    supporting_document_url = db.Column(db.String(255), nullable=True)
    terms_summary = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # 🤖 AI / GAR
    ai_tag = db.Column(db.String(100), nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    gar_risk_flag = db.Column(db.Boolean, default=False)
    gar_risk_rating = db.Column(db.String(50), nullable=True)  # Low, Medium, High
    gar_recommendations = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)

    # 🔌 3rd-Party Integration
    external_loan_id = db.Column(db.String(100), nullable=True)  # e.g., for banking sync
    external_provider = db.Column(db.String(100), nullable=True)  # e.g., Revolut, Stripe Capital, Bank of Ireland
    integration_status = db.Column(db.String(50), default='Not Synced')  # Synced, Failed, Pending
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🔐 Audit
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    ip_created_from = db.Column(db.String(45), nullable=True)

    # 🔁 Relationships
    company = db.relationship('Company', backref='loans')
    client = db.relationship('Client', backref='loans')
    unit = db.relationship('Unit', backref='loans')
    created_by = db.relationship('User', backref='created_loans', foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<Loan {self.loan_amount} {self.currency} from {self.lender_name} ({self.start_date})>"
