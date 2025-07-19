from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB


class PaymentRun(db.Model):
    __tablename__ = 'payment_runs'

    id = db.Column(db.Integer, primary_key=True)
    run_name = db.Column(db.String(100), nullable=False)

    # 🔗 Core Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 📅 Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    run_date = db.Column(db.Date, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ AI Phase 1: Parsing & Data Extraction
    parsed_summary = db.Column(db.Text, nullable=True)                     # AI-generated description of run
    extracted_data = db.Column(JSONB, nullable=True)                       # Parsed invoice metadata
    parsing_status = db.Column(db.String(50), default='Pending')           # Pending, Completed, Failed
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)               # csv_upload, API, email, manual
    is_ai_processed = db.Column(db.Boolean, default=False)

    # ✅ GAR Phase 1: Governance AI Score & Integrity Flags
    gar_compliance_score = db.Column(db.Float, nullable=True)             # 0.0 – 1.0
    gar_flags = db.Column(db.Text, nullable=True)                         # Notes on potential issues (e.g., duplicate invoice)
    gar_justification_notes = db.Column(db.Text, nullable=True)
    approved_by_gar = db.Column(db.Boolean, default=False)
    requires_human_review = db.Column(db.Boolean, default=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔐 Compliance Metadata (GDPR-aware)
    lawful_basis = db.Column(db.String(100), nullable=True)               # Optional: Contract, Legitimate Interest, etc.
    retention_period_days = db.Column(db.Integer, default=365)            # Optional: soft-delete / archive logic

    # 🔁 Reconciliation Status
    reconciliation_status = db.Column(db.String(50), default='Unreconciled')  # e.g., Unreconciled, Partial, Complete
    reconciliation_notes = db.Column(db.Text, nullable=True)

    # 📎 Linking & Export Tracking
    export_reference = db.Column(db.String(100), nullable=True)           # Optional reference for ERP/accounting sync
    synced_at = db.Column(db.DateTime, nullable=True)

    # 🔗 Relationships
    client = db.relationship('Client', backref='payment_runs')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    invoices = db.relationship('Invoice', backref='payment_run', lazy=True)

    def __repr__(self):
        return f"<PaymentRun {self.run_name} | Client ID: {self.client_id}>"

