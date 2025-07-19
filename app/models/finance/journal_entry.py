from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates

class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Link to Journal Batch
    batch_id = db.Column(db.Integer, db.ForeignKey('journal_batches.id'), nullable=False, index=True)

    # 📌 Entry Data
    entry_date = db.Column(db.Date, default=datetime.utcnow, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    account_code = db.Column(db.String(50), nullable=False, index=True)
    debit = db.Column(db.Numeric(precision=12, scale=2), default=0, nullable=False)
    credit = db.Column(db.Numeric(precision=12, scale=2), default=0, nullable=False)

    # 🏢 Contextual Linkages
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # ✅ AI / GAR Features
    parsed_text = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    ai_confidence_score = db.Column(db.Float, nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔌 External Sync Info
    external_reference = db.Column(db.String(100), nullable=True)
    external_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Failed, Manual
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🧾 Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔗 Relationships
    batch = db.relationship('JournalBatch', backref=db.backref('entries', lazy=True))
    client = db.relationship('Client', backref='journal_entries')
    unit = db.relationship('Unit', backref='journal_entries')
    user = db.relationship('User', backref='created_journal_entries')

    def __repr__(self):
        return f"<JournalEntry account_code={self.account_code} debit={self.debit} credit={self.credit}>"
