# app/models/pm_review_by_director.py

from datetime import datetime
from app.extensions import db

class PMReviewByDirector(db.Model):
    __tablename__ = 'pm_reviews_by_director'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    property_manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    director_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    property_manager = db.relationship("User", foreign_keys=[property_manager_id], backref="pm_reviews_received")
    director = db.relationship("User", foreign_keys=[director_id], backref="pm_reviews_submitted")
    client = db.relationship("Client", backref="pm_reviews")

    # 📅 Review Meta
    review_period = db.Column(db.String(20))                      # e.g., Q1-2025
    rating = db.Column(db.Integer)                                # 1–10
    strengths = db.Column(db.Text)
    areas_for_improvement = db.Column(db.Text)
    overall_comment = db.Column(db.Text)
    review_channel = db.Column(db.String(50), nullable=True)      # Portal, Form, Call
    reviewed_in_meeting = db.Column(db.Boolean, default=False)
    review_file_url = db.Column(db.String(255), nullable=True)

    # 🔐 Privacy & Access
    visibility_scope = db.Column(db.String(100), default='Admin,Director')
    is_private = db.Column(db.Boolean, default=True)
    shared_with_pm = db.Column(db.Boolean, default=False)
    consent_verified = db.Column(db.Boolean, default=False)

    # 🔌 External/API Sync
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')
    is_external = db.Column(db.Boolean, default=False)

    # 🤖 AI Parsing Fields
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_confidence_score = db.Column(db.Float, nullable=True)
    ai_profile_locked = db.Column(db.Boolean, default=False)
    flagged_sections = db.Column(db.JSON, nullable=True)          # {"tone": "hostile", "bias": "possible"}
    review_category = db.Column(db.String(100), nullable=True)    # e.g., End of Quarter, Performance Dispute

    # ⚖️ GAR Governance
    gar_alignment_score = db.Column(db.Float, nullable=True)
    gar_red_flags = db.Column(db.Text, nullable=True)
    is_gar_reviewed = db.Column(db.Boolean, default=False)
    recommended_action = db.Column(db.String(200), nullable=True)

    # 📅 Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<PMReviewByDirector PM={self.property_manager_id} Client={self.client_id} Rating={self.rating}>"

