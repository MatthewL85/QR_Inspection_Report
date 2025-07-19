from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class AgedDebtorSummary(db.Model):
    __tablename__ = 'aged_debtor_summaries'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)

    client = db.relationship("Client", backref="aged_debtor_summaries")
    unit = db.relationship("Unit", backref="aged_debtor_summaries")

    # 📊 Aged Balances Snapshot
    current = db.Column(db.Numeric(12, 2), default=0.00)
    days_30 = db.Column(db.Numeric(12, 2), default=0.00)
    days_60 = db.Column(db.Numeric(12, 2), default=0.00)
    days_90 = db.Column(db.Numeric(12, 2), default=0.00)
    days_120_plus = db.Column(db.Numeric(12, 2), default=0.00)
    total_outstanding = db.Column(db.Numeric(12, 2), default=0.00)

    # 🤖 AI + GAR Fields
    flagged_by_gar = db.Column(db.Boolean, default=False)
    gar_risk_rating = db.Column(db.String(50), nullable=True)  # e.g., Low, Medium, High
    gar_context_reference = db.Column(db.String(100), nullable=True)
    gar_notes = db.Column(db.Text, nullable=True)
    ai_notes = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    is_gar_verified = db.Column(db.Boolean, default=False)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔄 3rd Party Integration Fields
    external_contact_id = db.Column(db.String(100), nullable=True)  # Xero/QuickBooks ID
    integration_status = db.Column(db.String(50), nullable=True)    # Synced, Pending, Failed
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🔐 Audit Trail
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by = db.relationship("User", foreign_keys=[updated_by_id])
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AgedDebtorSummary unit_id={self.unit_id} total={self.total_outstanding}>"
