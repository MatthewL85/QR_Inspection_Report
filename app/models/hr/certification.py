from datetime import datetime
from app.extensions import db

class Certification(db.Model):
    __tablename__ = 'certifications'

    id = db.Column(db.Integer, primary_key=True)

    # 📌 Core Info
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    issuer = db.Column(db.String(100), nullable=True)
    issued_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    renewal_required = db.Column(db.Boolean, default=False)
    reminder_sent = db.Column(db.Boolean, default=False)
    renewal_window_days = db.Column(db.Integer, default=30)  # Reminder threshold
    uploaded_document_id = db.Column(db.Integer, db.ForeignKey('documents.id'))

    # 🔐 Privacy & API Metadata
    access_scope = db.Column(db.String(100), default='HR,Owner')  # Role-limited view
    external_reference = db.Column(db.String(100), nullable=True)  # LMS or training system ID
    synced_with_provider = db.Column(db.Boolean, default=False)

    # 🤖 AI Parsing Support (Phase 1)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Evaluation (Phase 2+)
    gar_score = db.Column(db.Float, nullable=True)  # 0.00 to 1.00
    gar_validated = db.Column(db.Boolean, default=False)
    gar_flagged_issues = db.Column(db.Text, nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🕒 Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    # 🔗 Relationships
    user = db.relationship("User", foreign_keys=[user_id], backref="certifications")
    document = db.relationship("Document", foreign_keys=[uploaded_document_id], backref="linked_certification")

    def __repr__(self):
        return f"<Certification {self.name} for User {self.user_id}>"
