from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB


class AgedDebtor(db.Model):
    __tablename__ = 'aged_debtors'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    unit = db.relationship('Unit', backref='aged_debtors')
    client = db.relationship('Client', backref='aged_debtors')

    # 🗓️ Reporting Context
    report_date = db.Column(db.Date, nullable=False)
    financial_year = db.Column(db.String(10), nullable=True)
    snapshot_label = db.Column(db.String(100), nullable=True)  # Optional tag (e.g. "Quarter End")

    # 💰 Age Bucketed Breakdown
    current_due = db.Column(db.Numeric(12, 2), default=0)
    due_30_days = db.Column(db.Numeric(12, 2), default=0)
    due_60_days = db.Column(db.Numeric(12, 2), default=0)
    due_90_days = db.Column(db.Numeric(12, 2), default=0)
    due_120_days_plus = db.Column(db.Numeric(12, 2), default=0)
    total_outstanding = db.Column(db.Numeric(12, 2), nullable=False)

    # 📌 Source Traceability
    arrears_ids = db.Column(JSONB, nullable=True)  # List of arrears.id in this snapshot
    service_charge_ids = db.Column(JSONB, nullable=True)
    levy_ids = db.Column(JSONB, nullable=True)
    external_ref = db.Column(db.String(100), nullable=True)  # Optional ID from third-party system

    # 🤖 AI + GAR Fields
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    flagged_by_ai = db.Column(db.Boolean, default=False)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    gar_risk_score = db.Column(db.Float, nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)
    ai_notes = db.Column(db.Text, nullable=True)
    is_gar_verified = db.Column(db.Boolean, default=False)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 📌 Flags & Status
    is_disputed = db.Column(db.Boolean, default=False)
    dispute_reason = db.Column(db.Text, nullable=True)
    is_reconciled = db.Column(db.Boolean, default=False)
    reconciliation_reference = db.Column(db.String(100), nullable=True)

    # 🧾 Audit & Ownership
    generated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    generated_by = db.relationship('User', backref='aged_debtor_reports')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AgedDebtor Unit={self.unit_id} Total={self.total_outstanding} on {self.report_date}>"

