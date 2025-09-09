from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class FinanceBatch(db.Model):
    __tablename__ = 'finance_batches'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Links
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    last_modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 🧾 Batch Metadata
    batch_name = db.Column(db.String(150), nullable=False, index=True)  # e.g. "Q1 Service Charge 2025"
    batch_type = db.Column(db.String(50), nullable=False, index=True)   # invoice, payment_run, levy, refund
    status = db.Column(db.String(50), default='draft', index=True)      # draft, approved, posted, locked
    period_start = db.Column(db.Date, nullable=False, index=True)
    period_end = db.Column(db.Date, nullable=False, index=True)
    posted_at = db.Column(db.DateTime, nullable=True)

    # 🧠 AI & GAR Integration
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    is_ai_flagged = db.Column(db.Boolean, default=False)
    gar_notes = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)

    # 🔌 3rd-Party Integration
    external_reference = db.Column(db.String(100), nullable=True)
    external_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Failed, Manual
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🔍 Auditing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 🔁 Relationships
    client = db.relationship("Client", backref="finance_batches")
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    last_modified_by = db.relationship("User", foreign_keys=[last_modified_by_id])
    invoices = db.relationship("Invoice", back_populates="finance_batch", lazy='dynamic')
    linked_accounts = db.relationship("Account", back_populates="finance_batch", lazy='dynamic')

    def __repr__(self):
        return f"<FinanceBatch {self.batch_name} [{self.status}]>"

