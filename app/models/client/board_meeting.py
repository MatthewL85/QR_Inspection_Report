from app.extensions import db
from datetime import datetime
import json

class BoardMeeting(db.Model):
    __tablename__ = 'board_meetings'

    id = db.Column(db.Integer, primary_key=True)

    # 🏢 Linked Entities
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    related_agm_id = db.Column(db.Integer, db.ForeignKey('agms.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 📄 Meeting Metadata
    title = db.Column(db.String(255), nullable=False)
    meeting_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255), nullable=True)

    meeting_type = db.Column(db.String(100), default='Board')   # e.g., Board, Emergency, Strategy, Legal
    meeting_category = db.Column(db.String(50), default='Board')  # AGM, EGM, Board

    status = db.Column(db.String(50), default='scheduled')      # scheduled, held, cancelled, postponed
    minimum_quorum_required = db.Column(db.Integer, nullable=True)  # e.g., 3 for Board, 10 for AGM

    # 🗂️ Agenda
    agenda_json = db.Column(db.Text, nullable=True)  # Editable agenda stored as JSON

    # 📎 Files / Documents
    board_pack_file = db.Column(db.String(500), nullable=True)
    minutes_file = db.Column(db.String(500), nullable=True)
    resolution_file = db.Column(db.String(500), nullable=True)

    # 🤖 AI & GAR Integration
    parsed_text = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.Text, nullable=True)  # JSON: motions, votes, actions
    ai_confidence_score = db.Column(db.Float, nullable=True)
    reviewed_by_ai = db.Column(db.Boolean, default=False)
    ai_parsed_at = db.Column(db.DateTime, nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)

    # 💬 GAR Chat & Feedback
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)
    gar_last_message_at = db.Column(db.DateTime, nullable=True)
    gar_resolution_status = db.Column(db.String(50), default='Open')  # Open, In Progress, Escalated, Closed

    # 🧾 Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by_human = db.Column(db.Boolean, default=False)
    last_reviewed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # 🔐 Access & Tags
    visibility_roles = db.Column(db.String(255), default='Super Admin,Admin,Property Manager,Director')
    tags = db.Column(db.String(255), nullable=True)  # e.g., "Finance, Legal, Emergency"

    # 🔁 Relationships
    client = db.relationship('Client', backref='board_meetings')
    related_agm = db.relationship('AGM', backref='board_meetings')
    created_by = db.relationship('User', backref='created_board_meetings', foreign_keys=[created_by_id])
   

    # 🔍 Extracted JSON safely
    def get_extracted_data(self):
        try:
            return json.loads(self.extracted_data) if self.extracted_data else {}
        except json.JSONDecodeError:
            return {}

    # 📝 Future Enhancements (Optional, for later use)
    # default_agenda_template_id = db.Column(db.Integer, db.ForeignKey('agenda_templates.id'), nullable=True)
    # auto_generate_resolution_file = db.Column(db.Boolean, default=False)
    # discussion_summary_json = db.Column(db.Text, nullable=True)  # For meeting discussion key points

    def __repr__(self):
        return f"<BoardMeeting '{self.title}' on {self.meeting_date}>"
