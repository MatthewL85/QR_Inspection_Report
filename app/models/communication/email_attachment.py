# app/models/communication/email_attachment.py

from app.extensions import db
from datetime import datetime

class EmailAttachment(db.Model):
    __tablename__ = 'email_attachments'

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('external_email_logs.id'))
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(255))                      # stored location on disk/cloud
    file_type = db.Column(db.String(50))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    extracted_text = db.Column(db.Text, nullable=True)         # Optional OCR/PDF text for AI parsing

    def __repr__(self):
        return f"<EmailAttachment id={self.id} file='{self.file_name}'>"
