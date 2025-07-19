from app.extensions import db
from datetime import datetime
import json

class AGM(db.Model):
    __tablename__ = 'agms'

    id = db.Column(db.Integer, primary_key=True)

    # 📍 Core Metadata
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    block_name = db.Column(db.String(100), nullable=True)
    meeting_title = db.Column(db.String(255), nullable=False)
    meeting_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(255), nullable=True)
    called_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 📄 Attachments
    agenda_file = db.Column(db.String(500), nullable=True)
    minutes_file = db.Column(db.String(500), nullable=True)
    resolutions_file = db.Column(db.String(500), nullable=True)

    # 🤖 AI & GAR Integration
    parsed_text = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.Text, nullable=True)             # JSON: motions, votes, roles, proxies
    ai_confidence_score = db.Column(db.Float, nullable=True)
    reviewed_by_ai = db.Column(db.Boolean, default=False)
    ai_parsed_at = db.Column(db.DateTime, nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)

    # 💬 GAR Chat & Feedback
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)
    gar_last_message_at = db.Column(db.DateTime, nullable=True)
    gar_resolution_status = db.Column(db.String(50), default='Open')  # Open, Reviewed, Escalated, Closed

    # 📋 Audit & Workflow
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by_human = db.Column(db.Boolean, default=False)
    last_reviewed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # 🔐 Access & Tags
    visibility_roles = db.Column(db.String(255), default='Super Admin,Admin,Property Manager,Director')
    tags = db.Column(db.String(255), nullable=True)  # e.g. "AGM,Finance,Voting"

    # 🔁 Relationships
    client = db.relationship('Client', backref='agms')
    called_by = db.relationship('User', backref='called_agms', foreign_keys=[called_by_id])

    def get_extracted_data(self):
        try:
            return json.loads(self.extracted_data) if self.extracted_data else {}
        except json.JSONDecodeError:
            return {}

    def __repr__(self):
        return f"<AGM {self.meeting_title} on {self.meeting_date}>"

