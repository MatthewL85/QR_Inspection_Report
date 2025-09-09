# app/models/contractor_feedback.py

from app.extensions import db
from datetime import datetime

class ContractorFeedback(db.Model):
    __tablename__ = 'contractor_feedback'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Foreign Keys
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractors.id'), nullable=False)
    given_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    work_order = db.relationship('WorkOrder', back_populates='feedback', uselist=False)
    contractor = db.relationship('Contractor', backref='feedback_entries')
    given_by = db.relationship('User', backref='submitted_feedback')

    # ⭐ Feedback Scores
    overall_rating = db.Column(db.Float, nullable=False)             # 1.0 to 5.0
    punctuality = db.Column(db.Float, nullable=True)
    quality_of_work = db.Column(db.Float, nullable=True)
    communication = db.Column(db.Float, nullable=True)
    professionalism = db.Column(db.Float, nullable=True)

    # 💬 Feedback Notes
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_anonymous = db.Column(db.Boolean, default=False)
    visibility_scope = db.Column(db.String(100), default='Admin,PM')
    consent_verified = db.Column(db.Boolean, default=False)
    feedback_source = db.Column(db.String(50), default='manual')  # manual, survey, auto-inferred

    # 🔌 External/API Sync
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    is_external = db.Column(db.Boolean, default=False)

    # 🤖 AI / GAR Integration
    parsed_summary = db.Column(db.Text, nullable=True)
    gar_sentiment_score = db.Column(db.Float)
    gar_flagged_language = db.Column(db.Boolean, default=False)
    gar_recommendation = db.Column(db.String(255))
    gar_explanation = db.Column(db.Text, nullable=True)  # AI reasoning for any flags
    tone_classification = db.Column(db.String(50))       # Positive, Neutral, Negative
    feedback_quality_score = db.Column(db.Float)         # 0.0–1.0 — clarity, relevance, detail
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    parsed_at = db.Column(db.DateTime, nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)

    # 💬 GAR Chat & Feedback Loop
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return (
            f"<ContractorFeedback contractor_id={self.contractor_id} "
            f"work_order_id={self.work_order_id} rating={self.overall_rating}>"
        )
