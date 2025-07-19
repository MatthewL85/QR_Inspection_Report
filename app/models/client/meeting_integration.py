from app.extensions import db
from datetime import datetime

class MeetingIntegration(db.Model):
    __tablename__ = 'meeting_integrations'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Linked Entities
    board_meeting_id = db.Column(db.Integer, db.ForeignKey('board_meetings.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 📞 Core Integration Details
    provider = db.Column(db.String(100), nullable=False)   # Zoom, Teams, Google Meet, etc.
    meeting_url = db.Column(db.String(500), nullable=False)
    join_link = db.Column(db.String(500), nullable=True)   # if different from meeting_url
    dial_in_number = db.Column(db.String(100), nullable=True)
    meeting_id = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=True)

    # 📅 Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🧠 Optional Future Enhancements (AI / API Integration Ready)
    api_integration_id = db.Column(db.String(100), nullable=True)           # External ref from Zoom/Teams API
    oauth_token = db.Column(db.String(255), nullable=True)                  # Encrypted token for automation
    expires_at = db.Column(db.DateTime, nullable=True)                      # Token/session expiry
    is_recording_enabled = db.Column(db.Boolean, default=False)
    recording_url = db.Column(db.String(500), nullable=True)                # Link to meeting recording

    # 🔁 Relationships
    board_meeting = db.relationship('BoardMeeting', backref='integrations')
    created_by = db.relationship('User')

    def __repr__(self):
        return f"<MeetingIntegration {self.provider} for meeting {self.board_meeting_id}>"

