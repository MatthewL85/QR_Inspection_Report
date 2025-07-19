from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates

class JournalBatch(db.Model):
    __tablename__ = 'journal_batches'

    id = db.Column(db.Integer, primary_key=True)

    # 📁 Metadata
    batch_name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    period = db.Column(db.String(20), nullable=True, index=True)  # e.g., "Q2 2025", "2025-07"
    journal_date = db.Column(db.Date, default=datetime.utcnow, index=True)

    # 🔐 Security / Ownership
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    locked = db.Column(db.Boolean, default=False)

    # 📅 Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    modified_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🤖 AI / GAR Smart Insights
    parsed_text = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    gar_notes = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)

    # 🔌 3rd-Party Integration
    external_reference = db.Column(db.String(100), nullable=True)
    external_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Failed, Manual
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🔗 Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])

    def __repr__(self):
        return f"<JournalBatch {self.batch_name} ({self.period})>"

