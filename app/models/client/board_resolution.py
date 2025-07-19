from app.extensions import db
from datetime import datetime
import json

class BoardResolution(db.Model):
    __tablename__ = 'board_resolutions'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    board_meeting_id = db.Column(db.Integer, db.ForeignKey('board_meetings.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    related_agm_id = db.Column(db.Integer, db.ForeignKey('agms.id'), nullable=True)  # 🧩 Optional if tied to AGM

    # 📄 Resolution Metadata
    title = db.Column(db.String(255), nullable=False)
    resolution_text = db.Column(db.Text, nullable=False)
    resolution_type = db.Column(db.String(100), nullable=True)  # Policy, Budget, Legal, Compliance, Other
    status = db.Column(db.String(50), default='proposed')        # proposed, passed, rejected, withdrawn
    resolution_file = db.Column(db.String(500), nullable=True)

    # 🗳️ Voting Results
    vote_summary = db.Column(db.JSON, nullable=True)             # {"yes": 5, "no": 2, "abstain": 1}
    voter_ids = db.Column(db.JSON, nullable=True)                # {"yes": [1,2], "no": [3], "abstain": [4]}

    # 🤖 AI & GAR Analysis
    parsed_summary = db.Column(db.Text, nullable=True)
    gar_flagged_issues = db.Column(db.Text)
    gar_compliance_score = db.Column(db.Float)
    gar_recommendation = db.Column(db.String(255))
    is_gar_reviewed = db.Column(db.Boolean, default=False)

    # 🧠 Optional AI JSON extraction (future)
    extracted_data = db.Column(db.Text, nullable=True)  # JSON: keywords, referenced laws, impacts
    ai_confidence_score = db.Column(db.Float, nullable=True)

    # 💬 GAR Chat
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)
    gar_last_message_at = db.Column(db.DateTime, nullable=True)
    gar_resolution_status = db.Column(db.String(50), default='Open')  # Open, Resolved, Escalated

    # 📅 Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by_human = db.Column(db.Boolean, default=False)
    last_reviewed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # 🔐 Access & Tagging
    visibility_roles = db.Column(db.String(255), default='Super Admin,Admin,Property Manager,Director')
    tags = db.Column(db.String(255), nullable=True)  # e.g., "Governance, Legal, Risk"

    # 🔁 Relationships
    board_meeting = db.relationship('BoardMeeting', backref='resolutions')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    related_agm = db.relationship('AGM', backref='board_resolutions')  # Optional

    # 🧩 Safe JSON loader
    def get_vote_summary(self):
        try:
            return json.loads(self.vote_summary) if self.vote_summary else {}
        except json.JSONDecodeError:
            return {}

    def __repr__(self):
        return f"<BoardResolution '{self.title}' ({self.status})>"
