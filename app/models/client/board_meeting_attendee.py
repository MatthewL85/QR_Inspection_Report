from app.extensions import db
from datetime import datetime

class BoardMeetingAttendee(db.Model):
    __tablename__ = 'board_meeting_attendees'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    board_meeting_id = db.Column(db.Integer, db.ForeignKey('board_meetings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 🕓 Attendance Metadata
    join_time = db.Column(db.DateTime, nullable=True)
    leave_time = db.Column(db.DateTime, nullable=True)
    is_virtual = db.Column(db.Boolean, default=True)
    role_in_meeting = db.Column(db.String(100), nullable=True)  # Chairperson, Secretary, Director, Observer, Guest
    attendance_status = db.Column(db.String(50), default='invited')  # invited, attended, absent, excused

    # 🗳️ Voting Participation
    voted = db.Column(db.Boolean, default=False)
    voting_method = db.Column(db.String(50), nullable=True)  # in-person, online, proxy
    vote_record = db.Column(db.Text, nullable=True)  # Optional JSON string of votes cast

    # 🤖 AI & GAR Future-Proofing
    engagement_score = db.Column(db.Float, nullable=True)  # Optional AI metric for participation
    gar_flagged_participation = db.Column(db.Text, nullable=True)  # AI anomaly flags e.g. "no join time", "missing vote"
    reviewed_by_gar = db.Column(db.Boolean, default=False)
    gar_notes = db.Column(db.Text, nullable=True)
    meeting_feedback = db.Column(db.Text, nullable=True)  # Post-meeting feedback
    ai_presence_tracking_data = db.Column(db.JSON, nullable=True)  # Facial/audio match scores (for future AI modules)

    # 📎 Attachments
    attendance_file = db.Column(db.String(500), nullable=True)  # Upload of signed attendance sheet or screenshot

    # 🧾 Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
 
    # 🔁 Relationships
    board_meeting = db.relationship('BoardMeeting', backref='attendee_logs')
    user = db.relationship('User', backref='meeting_participation')
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<BoardMeetingAttendee user_id={self.user_id} meeting_id={self.board_meeting_id}>"
