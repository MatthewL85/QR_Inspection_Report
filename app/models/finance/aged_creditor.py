from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class AgedCreditor(db.Model):
    __tablename__ = 'aged_creditors'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Must be a contractor user
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    finance_batch_id = db.Column(db.Integer, db.ForeignKey('finance_batches.id'), nullable=True)

    contractor = db.relationship('User', backref='aged_creditors', foreign_keys=[contractor_id])
    client = db.relationship('Client', backref='aged_creditors')
    finance_batch = db.relationship('FinanceBatch', backref='aged_creditors')

    # 📅 Reporting Context
    report_date = db.Column(db.Date, nullable=False)
    financial_year = db.Column(db.String(10), nullable=True)  # e.g., "2024/25"
    notes = db.Column(db.Text, nullable=True)

    # 💰 Aged Amounts Breakdown
    current_due = db.Column(db.Numeric(12, 2), default=0)
    due_30_days = db.Column(db.Numeric(12, 2), default=0)
    due_60_days = db.Column(db.Numeric(12, 2), default=0)
    due_90_days = db.Column(db.Numeric(12, 2), default=0)
    due_120_days_plus = db.Column(db.Numeric(12, 2), default=0)
    total_outstanding = db.Column(db.Numeric(12, 2), nullable=False)

    # 📎 Invoice & Work Order Links
    invoice_ids = db.Column(JSONB, nullable=True)     # List of invoice primary keys
    work_order_ids = db.Column(JSONB, nullable=True)  # List of associated WO IDs, optional

    # 🤖 AI & GAR Integration
    flagged_by_ai = db.Column(db.Boolean, default=False)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    gar_risk_score = db.Column(db.Float, nullable=True)  # 0.00 to 1.00
    gar_recommendation = db.Column(db.String(255), nullable=True)
    ai_notes = db.Column(db.Text, nullable=True)
    is_gar_verified = db.Column(db.Boolean, default=False)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # ⚠️ Status Flags
    is_disputed = db.Column(db.Boolean, default=False)
    is_reconciled = db.Column(db.Boolean, default=False)

    # 🕓 Audit Trail
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    generated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    generated_by = db.relationship('User', backref='aged_creditor_reports', foreign_keys=[generated_by_id])

    def __repr__(self):
        return f"<AgedCreditor Contractor={self.contractor_id} Total={self.total_outstanding} on {self.report_date}>"

