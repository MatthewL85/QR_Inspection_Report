# app/models/communication/external_email_log.py

from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from app.extensions import db

class ExternalEmailLog(db.Model):
    __tablename__ = 'external_email_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Email Info
    message_id = db.Column(db.String(255), unique=True, nullable=True)    # Email system ID (for threading)
    in_reply_to = db.Column(db.String(255), nullable=True)                # Used for threading
    thread_id = db.Column(db.String(255), nullable=True)                  # Gmail/Outlook thread tracking
    sender = db.Column(db.String(255), nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    cc = db.Column(db.Text, nullable=True)
    bcc = db.Column(db.Text, nullable=True)
    subject = db.Column(db.String(512), nullable=False)
    body_plain = db.Column(db.Text)
    body_html = db.Column(db.Text)

    # 📎 Attachments & Metadata
    attachments = db.relationship('EmailAttachment', backref='email', cascade='all, delete-orphan')
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    email_source = db.Column(db.String(50), default='mailgun')            # mailgun, gmail, outlook, api-upload

    # 🧠 AI & GAR Enhancements (optional, parsed post-ingest)
    parsed_summary = db.Column(db.Text, nullable=True)                    # Human-readable summary
    extracted_data = db.Column(JSONB, nullable=True)                      # Structured JSON (e.g. {'quote_amount': 2000})
    parsed_keywords = db.Column(db.ARRAY(db.String), nullable=True)       # For smart search (e.g. ['quote', 'approval'])
    learning_signals = db.Column(JSONB, nullable=True)                    # Used for self-learning GAR logic (e.g. {'approved': True})
    gar_context_tag = db.Column(db.String(100), nullable=True)            # e.g. 'capex', 'contractor_response', etc.
    gar_chat_visible = db.Column(db.Boolean, default=False)               # Flag for GAR Chat integration

    # 🔁 Linking to System Modules (flexible)
    related_module = db.Column(db.String(100), nullable=True)             # e.g. 'WorkOrder', 'CapexRequest', etc.
    related_id = db.Column(db.Integer, nullable=True)                     # FK handled dynamically in code

    # 🔒 Audit & Tracking
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    source_ip = db.Column(db.String(50), nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    is_flagged = db.Column(db.Boolean, default=False)
    flag_reason = db.Column(db.Text)

    # 🕓 Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ExternalEmailLog id={self.id} subject='{self.subject[:30]}' sender={self.sender}>"
