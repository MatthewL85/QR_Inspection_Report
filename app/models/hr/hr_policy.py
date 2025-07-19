from datetime import datetime
from app.extensions import db

class HRPolicy(db.Model):
    __tablename__ = 'hr_policies'

    id = db.Column(db.Integer, primary_key=True)

    # 📘 Core Policy Info
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100))  # e.g., Leave, Remote Work, Dress Code
    description = db.Column(db.Text, nullable=True)  # Human-readable overview
    document_url = db.Column(db.String(255), nullable=True)  # Optional file (PDF/Doc)
    version = db.Column(db.String(20), default='1.0')
    effective_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date, nullable=True)

    # 👤 Ownership & Audit
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    created_by = db.relationship("User", foreign_keys=[created_by_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])

    # ✅ AI/GAR Parsing
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)  # {"notice_period": "30 days"}
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Policy Intelligence
    gar_flags = db.Column(db.Text, nullable=True)         # e.g., "ambiguous maternity clause"
    gar_compliance_score = db.Column(db.Float)            # 0.0 – 1.0
    gar_recommendation = db.Column(db.Text, nullable=True)
    is_governance_approved = db.Column(db.Boolean, default=False)

    # 💬 GAR Interaction
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<HRPolicy title='{self.title}' version={self.version}>"
