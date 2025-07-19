from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class AgedCreditorSummary(db.Model):
    __tablename__ = 'aged_creditor_summaries'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # FK to Contractor (User)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    contractor = db.relationship("User", foreign_keys=[contractor_id])
    client = db.relationship("Client", backref="aged_creditor_summaries")

    # 💰 Aged Payables Buckets
    current = db.Column(db.Numeric(12, 2), default=0.00)
    days_30 = db.Column(db.Numeric(12, 2), default=0.00)
    days_60 = db.Column(db.Numeric(12, 2), default=0.00)
    days_90 = db.Column(db.Numeric(12, 2), default=0.00)
    days_120_plus = db.Column(db.Numeric(12, 2), default=0.00)
    total_outstanding = db.Column(db.Numeric(12, 2), default=0.00)

    # 🧠 AI & GAR Fields
    flagged_by_gar = db.Column(db.Boolean, default=False)
    gar_risk_rating = db.Column(db.String(50), nullable=True)       # Low, Medium, High, Escalate
    gar_notes = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)
    ai_notes = db.Column(db.Text, nullable=True)
    ai_flagged = db.Column(db.Boolean, default=False)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 📎 3rd Party Integration (Optional)
    external_reference_id = db.Column(db.String(100), nullable=True)  # For linking to accounting systems
    sync_status = db.Column(db.String(50), nullable=True)             # Synced, Pending, Failed
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🕒 Audit Trail
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by = db.relationship("User", foreign_keys=[updated_by_id])

    def __repr__(self):
        return f"<AgedCreditorSummary contractor_id={self.contractor_id} total={self.total_outstanding}>"
