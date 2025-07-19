# app/models/finance/budget_approval.py

from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB


class BudgetApproval(db.Model):
    __tablename__ = 'budget_approvals'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core References
    budget_id = db.Column(db.Integer, db.ForeignKey('budgets.id'), nullable=False)
    director_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Must have Director role

    # ✅ Approval Data
    approved = db.Column(db.Boolean, default=False)
    approval_date = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.Column(db.Text, nullable=True)

    # 🧠 AI & GAR Enhancements
    ai_confidence_score = db.Column(db.Float, nullable=True)  # e.g., 0.92 means 92% AI confidence
    gar_rationale = db.Column(db.Text, nullable=True)         # GAR's reasoning for acceptance or flag
    ai_recommendation_summary = db.Column(db.Text, nullable=True)  # Concise summary of AI analysis
    gar_flags = db.Column(JSONB, default={})  # e.g., {"overbudget": true, "insufficient_breakdown": true}

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🕵️ Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)        # Optional: for future security audits
    user_agent = db.Column(db.String(255), nullable=True)

    # 🔁 Relationships
    budget = db.relationship('Budget', backref='approvals')
    director = db.relationship('User', backref='budget_approvals', foreign_keys=[director_id])

    def __repr__(self):
        return (
            f"<BudgetApproval Budget={self.budget_id} "
            f"Director={self.director_id} Approved={self.approved}>"
        )

