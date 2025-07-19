# models/members/member_approval.py

from app.extensions import db
from datetime import datetime

class MemberApproval(db.Model):
    __tablename__ = 'member_approvals'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    resident_request_id = db.Column(db.Integer, db.ForeignKey('resident_requests.id'), nullable=False)

    # ✅ Approval Details
    approved = db.Column(db.Boolean, nullable=False)
    message = db.Column(db.Text, nullable=True)
    approved_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🧠 AI/GAR Parsing & Recommendation
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')  # Pending, Completed, Failed
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)

    # ⚖️ GAR Governance
    gar_flagged = db.Column(db.Boolean, default=False)
    gar_reason_flagged = db.Column(db.Text, nullable=True)
    gar_confidence_score = db.Column(db.Float, nullable=True)
    gar_alignment_score = db.Column(db.Float, nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)

    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🔁 Relationships
    member = db.relationship('member', backref='approvals')
    resident_request = db.relationship('ResidentRequest', backref='member_approvals')

    def __repr__(self):
        return f"<memberApproval member_id={self.member_id} approved={self.approved}>"
