from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class EmailLog(db.Model):
    __tablename__ = 'email_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 User Reference (nullable for system-wide emails or failed auth attempts)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # 📬 Message Metadata
    email_type = db.Column(db.String(100), nullable=False)  # e.g., 'password_change_alert', '2FA_enabled'
    recipient = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 📤 Delivery Info
    delivery_status = db.Column(db.String(50), default='sent')  # sent, failed, pending
    delivery_response = db.Column(db.Text, nullable=True)       # optional raw API response from email provider

    # 🌍 Context
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    context_data = db.Column(JSON, nullable=True)  # AI/GAR-Ready: store structured metadata like login_id, related action, etc.

    # 🧠 AI & GAR Chat Integration
    gar_summary = db.Column(db.Text, nullable=True)             # Short parsed summary
    ai_extracted_entities = db.Column(JSON, nullable=True)      # AI: extracted fields (e.g., name, date, type)
    is_gar_relevant = db.Column(db.Boolean, default=False)      # Flag for compliance insights

    # 🔐 Governance
    audit_notes = db.Column(db.Text, nullable=True)             # Admin or AI-written contextual notes
    reviewed_by_admin = db.Column(db.Boolean, default=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    # 🔄 Relationship to user (optional)
    user = db.relationship('User', backref='email_logs', lazy=True)
