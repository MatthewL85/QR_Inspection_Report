from app.extensions import db
from datetime import datetime
import json

class ClientComplianceDocument(db.Model):
    __tablename__ = 'client_compliance_documents'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 📄 Document Metadata
    document_name = db.Column(db.String(255), nullable=False)
    document_type = db.Column(db.String(100), nullable=True)  # e.g., Fire Cert, Lift Inspection
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    version = db.Column(db.Integer, default=1)

    # 🤖 AI & GAR Integration
    parsed_text = db.Column(db.Text, nullable=True)                  # Full OCR or text extract
    parsed_summary = db.Column(db.Text, nullable=True)               # Short GAR/AI summary
    extracted_data = db.Column(db.Text, nullable=True)               # JSON structured data
    ai_confidence_score = db.Column(db.Float, nullable=True)
    reviewed_by_ai = db.Column(db.Boolean, default=False)
    ai_parsed_at = db.Column(db.DateTime, nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)         # e.g., 'PDF', 'Scan', 'Email'

    # 🧠 GAR Chat & Feedback Loop
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)
    gar_last_message_at = db.Column(db.DateTime, nullable=True)
    gar_resolution_status = db.Column(db.String(50), default='Open')  # Open, In Progress, Resolved

    # 📋 Status & Compliance Tracking
    status = db.Column(db.String(50), default='active')              # active, expired, archived
    reviewed_by_human = db.Column(db.Boolean, default=False)
    last_reviewed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(255), nullable=True)                  # e.g., Fire, Insurance, Safety

    # 🔒 Access Control
    visibility_roles = db.Column(
        db.String(255),
        default='Super Admin,Admin,Property Manager,Director'
    )  # Could expand with "Owner" if compliance is visible to members

    # 🔁 Relationships
    client = db.relationship('Client', backref='compliance_documents')
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id], backref='uploaded_client_documents')

    def get_extracted_data(self):
        try:
            return json.loads(self.extracted_data) if self.extracted_data else {}
        except json.JSONDecodeError:
            return {}

    def __repr__(self):
        return f"<ClientComplianceDocument {self.document_name} for Client {self.client_id}>"

