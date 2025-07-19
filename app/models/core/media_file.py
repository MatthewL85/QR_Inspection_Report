from datetime import datetime
from app.extensions import db

class MediaFile(db.Model):
    __tablename__ = 'media_files'

    id = db.Column(db.Integer, primary_key=True)

    # 📎 File Metadata
    filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(250), nullable=False)
    file_type = db.Column(db.String(50))                               # image, video, pdf, etc.
    description = db.Column(db.String(255), nullable=True)

    # 👤 Uploaded By
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploader = db.relationship('User', backref='uploaded_media')

    # 🔗 Polymorphic Linking
    related_table = db.Column(db.String(50), nullable=False)           # e.g., 'inspection', 'equipment'
    related_id = db.Column(db.Integer, nullable=False)

    # 📅 Timestamps & Visibility
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    visibility = db.Column(db.String(20), default='private')           # private, public, internal
    expires_at = db.Column(db.DateTime, nullable=True)

    # 🤖 AI Parsing Fields (Phase 1)
    parsed_summary = db.Column(db.Text, nullable=True)                 # Summary of content
    extracted_data = db.Column(db.JSON, nullable=True)                 # JSON-formatted details
    parsing_status = db.Column(db.String(50), default='Pending')       # Pending / Completed / Failed
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)           # image, scan, pdf, etc.
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 AI Enhancements (GAR-ready)
    ai_classification = db.Column(db.String(100), nullable=True)       # invoice, hazard_photo, etc.
    ai_confidence_score = db.Column(db.Float, nullable=True)           # 0.0 – 1.0
    ai_detected_issues = db.Column(db.Text, nullable=True)             # e.g., "Crack detected"
    ai_recommendations = db.Column(db.Text, nullable=True)             # e.g., "Follow-up needed"

    # 🧠 GAR Governance Phase
    ai_scorecard = db.Column(db.JSON, nullable=True)                   # {"risk": 0.6, "impact": 0.8}
    ai_rank = db.Column(db.String(20), nullable=True)                  # A, B, C
    is_ai_preferred = db.Column(db.Boolean, default=False)
    reason_for_recommendation = db.Column(db.Text, nullable=True)

    # 🏷️ Tags & Role Filtering
    tags = db.Column(db.String(255), nullable=True)                    # e.g., fire, inspection, compliance
    role_visibility = db.Column(db.String(100), default='Admin,Property Manager')

    def __repr__(self):
        return f"<MediaFile {self.filename} ({self.related_table} ID: {self.related_id})>"

