from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB


class Arrears(db.Model):
    __tablename__ = 'arrears'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    finance_batch_id = db.Column(db.Integer, db.ForeignKey('finance_batches.id'), nullable=True)

    # 💰 Financial Obligations
    amount_due = db.Column(db.Numeric(12, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    days_overdue = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), default='Unpaid')  # Unpaid, Partially Paid, Paid, Written Off

    # 📈 Penalties & Late Fees
    late_fee_accrued = db.Column(db.Numeric(12, 2), default=0.00)
    interest_accrued = db.Column(db.Numeric(12, 2), default=0.00)
    interest_waived = db.Column(db.Boolean, default=False)
    waiver_reason = db.Column(db.Text, nullable=True)
    penalty_policy_applied = db.Column(db.String(100), nullable=True)  # e.g., "Default Interest Policy A"

    # 🔍 AI & GAR Metadata
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)  # normalized smart structure
    flagged_by_ai = db.Column(db.Boolean, default=False)
    reason_for_flag = db.Column(db.String(255), nullable=True)
    gar_compliance_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    gar_risk_flag = db.Column(db.String(50), nullable=True)  # e.g., "High Risk", "Potential Dispute"
    validated_by_gar = db.Column(db.Boolean, default=False)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🌐 External Integration & Evidence
    source_document = db.Column(db.String(255), nullable=True)  # file path or URL
    external_collection_ref = db.Column(db.String(100), nullable=True)  # 3rd-party API ref if sent to collection agency
    arrears_type = db.Column(db.String(50), default='Service Charge')  # e.g., Service Charge, Levy, Utility

    # 📝 Notes & Context
    notes = db.Column(db.Text, nullable=True)

    # 🔐 Audit & Change Tracking
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 🔁 Relationships
    unit = db.relationship("Unit", backref="arrears")
    client = db.relationship("Client", backref="arrears")
    invoice = db.relationship("Invoice", backref="arrears", lazy='joined')
    finance_batch = db.relationship("FinanceBatch", backref="arrears")
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    # ⏱ Late Fee / Penalty Log
    late_fee_logs = db.relationship(
        'LateFeeTransactionLog',
        back_populates="arrears",
        lazy='dynamic',
        foreign_keys='LateFeeTransactionLog.arrears_id'
    )

    def __repr__(self):
        return f"<Arrears unit={self.unit_id} due €{self.amount_due} on {self.due_date}>"
