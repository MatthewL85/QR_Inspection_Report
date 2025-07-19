# app/models/performance_review.py

from datetime import datetime
from app.extensions import db

class PerformanceReview(db.Model):
    __tablename__ = 'performance_reviews'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    linked_contract_id = db.Column(db.Integer, nullable=True)  # Optional contract link

    user = db.relationship("User", foreign_keys=[user_id], backref="performance_reviews")
    reviewer = db.relationship("User", foreign_keys=[reviewer_id], backref="reviews_given")

    # 🗓️ Core Review Fields
    review_date = db.Column(db.Date, default=datetime.utcnow)
    review_period = db.Column(db.String(50), nullable=True)           # Q1 2025
    review_type = db.Column(db.String(50), default="Annual")          # Annual, Quarterly, etc.
    score = db.Column(db.Integer)                                     # Total score
    feedback = db.Column(db.Text)
    goals_set = db.Column(db.Text)
    is_finalized = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ Optional Breakdown
    communication_score = db.Column(db.Integer, nullable=True)
    punctuality_score = db.Column(db.Integer, nullable=True)
    quality_score = db.Column(db.Integer, nullable=True)
    leadership_score = db.Column(db.Integer, nullable=True)
    initiative_score = db.Column(db.Integer, nullable=True)

    # 🔐 Visibility & Consent
    visibility_scope = db.Column(db.String(100), default='Admin,HR')
    is_private = db.Column(db.Boolean, default=True)
    shared_with_director = db.Column(db.Boolean, default=False)
    consent_verified = db.Column(db.Boolean, default=False)

    # 🔌 External / API Sync
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')
    is_external = db.Column(db.Boolean, default=False)

    # 📋 Additional Review Context
    review_category = db.Column(db.String(50), nullable=True)         # Performance, Promotion, Probation
    review_channel = db.Column(db.String(50), nullable=True)          # Portal, Meeting, Form
    review_notes = db.Column(db.Text, nullable=True)
    review_file_url = db.Column(db.String(255), nullable=True)

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
    flagged_sections = db.Column(db.JSON, nullable=True)              # {"goals": "incomplete", "feedback": "vague"}

    # 🧠 GAR Evaluation
    gar_score = db.Column(db.Float, nullable=True)                    # 0.0–1.0
    gar_rank = db.Column(db.String(10), nullable=True)                # A, B, C
    gar_flagged_areas = db.Column(db.Text, nullable=True)
    reason_for_rank = db.Column(db.Text, nullable=True)
    requires_manual_review = db.Column(db.Boolean, default=False)
    last_reviewed_at = db.Column(db.DateTime, nullable=True)

    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)


    def __repr__(self):
        return f"<PerformanceReview user_id={self.user_id} score={self.score} type={self.review_type}>"

