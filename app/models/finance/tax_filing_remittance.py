from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class TaxFilingRemittance(db.Model):
    __tablename__ = 'tax_filing_remittances'

    id = db.Column(db.Integer, primary_key=True)

    # 🌍 Jurisdiction
    country = db.Column(db.String(100), nullable=False)

    # 📅 Filing Period
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)

    # 💰 Tax Totals
    total_tax_collected = db.Column(db.Numeric(12, 2), nullable=False)
    total_tax_remitted = db.Column(db.Numeric(12, 2), nullable=True)
    status = db.Column(db.String(50), default='Draft')  # Draft, Submitted, Paid, Reconciled, Rejected

    # 🧾 Metadata
    filing_reference_number = db.Column(db.String(100), nullable=True)  # e.g. Revenue or VAT ID
    remittance_date = db.Column(db.DateTime, nullable=True)
    supporting_documents_url = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # 🧠 AI + GAR Integration
    flagged_by_gar = db.Column(db.Boolean, default=False)
    gar_notes = db.Column(db.Text, nullable=True)
    gar_score = db.Column(db.Float, nullable=True)
    gar_decision_reason = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)  # e.g., {"vat_due": 3400, "anomalies": ["discrepancy in Q2"]}

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔐 Audit + Governance
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    # 🧮 Optional Reconciliation/Workflow Linkage
    reconciliation_batch_id = db.Column(db.Integer, db.ForeignKey('reconciliation_batches.id'), nullable=True)
    reconciliation_batch = db.relationship('ReconciliationBatch', backref='tax_filings')

    def __repr__(self):
        return f"<TaxFilingRemittance {self.country} | {self.period_start} - {self.period_end} | Status: {self.status}>"

