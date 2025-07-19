# app/models/document.py

from datetime import datetime
from app.extensions import db

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)

    # 📁 Basic Info
    file_name = db.Column(db.String(255))
    file_type = db.Column(db.String(50))                   # pdf, jpg, docx, etc.
    file_path = db.Column(db.String(255))                  # Relative or cloud path
    category = db.Column(db.String(100))                   # Lease, Contract, Invoice, Compliance, etc.
    description = db.Column(db.Text)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔗 Linking & Traceability
    linked_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    linked_client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    source_reference = db.Column(db.String(100), nullable=True)  # Optional external reference (e.g., WorkOrder-123)

    # 🔄 Versioning
    version = db.Column(db.String(20), default='1.0')
    is_current_version = db.Column(db.Boolean, default=True)
    access_scope = db.Column(db.String(50), default='private')  # private, client_only, director_viewable, public

    # 📅 Compliance / Expiry
    expires_at = db.Column(db.DateTime, nullable=True)
    renewal_required = db.Column(db.Boolean, default=False)
    renewal_notified = db.Column(db.Boolean, default=False)
    compliance_category = db.Column(db.String(100), nullable=True)  # Insurance, Fire Cert, H&S, etc.

    # 🤖 AI Parsing Fields (Phase 1)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')    # Pending, Completed, Failed
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)        # 'pdf', 'scanned_image', etc.
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Intelligence Fields (Phase 2)
    gar_flags = db.Column(db.Text, nullable=True)                   # e.g. “Missing Signature”
    gar_score = db.Column(db.Float, nullable=True)                  # Confidence/compliance score (0–1)
    gar_comments = db.Column(db.Text, nullable=True)
    requires_manual_review = db.Column(db.Boolean, default=False)
    last_reviewed_at = db.Column(db.DateTime, nullable=True)

    # 💬 GAR Chat & Feedback Loop
    gar_chat_ready = db.Column(db.Boolean, default=False)           # AI summary complete + feedback enabled
    gar_feedback = db.Column(db.Text, nullable=True)                # Human or AI remarks

    # 🔗 Relationships
    uploaded_by_user = db.relationship("User", foreign_keys=[uploaded_by], backref="uploaded_documents")
    user = db.relationship("User", foreign_keys=[linked_user_id], backref="linked_documents")
    client = db.relationship("Client", foreign_keys=[linked_client_id], backref="documents")

    def __repr__(self):
        return f"<Document {self.file_name} for client={self.linked_client_id}>"
