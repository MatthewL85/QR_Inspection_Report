from datetime import datetime
from app.extensions import db

class ManagementCompanyReview(db.Model): 
    __tablename__ = 'management_company_reviews'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Entity References
    company_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)   # Management company reviewed
    director_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)     # Reviewer
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)     # Site under management

    review_period = db.Column(db.String(20))  # e.g., Q2-2025, 2025-H1

    # ⭐ Human Ratings (1–5)
    communication_rating = db.Column(db.Integer)
    responsiveness_rating = db.Column(db.Integer)
    financial_transparency_rating = db.Column(db.Integer)
    value_rating = db.Column(db.Integer)
    overall_satisfaction_rating = db.Column(db.Integer)
    comments = db.Column(db.Text)

    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🤖 AI Parsing Support
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')      # Pending, Completed, Failed
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)          # 'form', 'survey', 'email', etc.
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Review Enhancements
    gar_alignment_score = db.Column(db.Float, nullable=True)          # KPI fit / governance match
    gar_red_flags = db.Column(db.Text, nullable=True)                 # e.g., "multiple poor scores in Qs"
    gar_confidence_rating = db.Column(db.Float, nullable=True)       # Confidence in reliability of review
    is_gar_reviewed = db.Column(db.Boolean, default=False)
    recommended_action = db.Column(db.String(200), nullable=True)    # "Escalate to review panel", etc.

    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)


    # 🔁 Relationships
    director = db.relationship("User", foreign_keys=[director_id])
    company = db.relationship("Client", foreign_keys=[company_id], backref="reviews_as_company")
    client = db.relationship("Client", foreign_keys=[client_id], backref="reviews_as_client")
