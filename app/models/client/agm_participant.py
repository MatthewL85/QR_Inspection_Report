from app.extensions import db
from datetime import datetime
import json

class AGMParticipant(db.Model):
    __tablename__ = 'agm_participants'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    agm_id = db.Column(db.Integer, db.ForeignKey('agms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)          # Person named on record
    represented_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Proxy holder

    # 📋 Attendance & Representation
    attended = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(50), default='Member')   # Member, Director, Proxy, PM, Guest
    attendance_status = db.Column(db.String(50), default='Invited')  # Invited, Present, Proxy, Absent

    # 🗳️ Voting Record
    vote_cast = db.Column(db.JSON, nullable=True)       # {"motion_1": "yes", "motion_2": "abstain"}
    vote_timestamp = db.Column(db.DateTime, nullable=True)

    # 🤖 AI / GAR Integration
    gar_flagged_issues = db.Column(db.Text, nullable=True)  # e.g., "Proxy not authorized"
    gar_confidence_score = db.Column(db.Float, nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)
    gar_resolution_status = db.Column(db.String(50), default='Open')

    # 🔐 Visibility & Metadata
    visibility_roles = db.Column(db.String(255), default='Super Admin,Admin,Property Manager,Director')
    tags = db.Column(db.String(255), nullable=True)     # e.g., "Proxy,Owner,First-time"

    # 🧾 Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    # 🔁 Relationships
    agm = db.relationship('AGM', backref='participants')
    user = db.relationship('User', foreign_keys=[user_id])
    represented_by = db.relationship('User', foreign_keys=[represented_by_id])

    def get_vote_cast(self):
        try:
            return json.loads(self.vote_cast) if self.vote_cast else {}
        except json.JSONDecodeError:
            return {}

    def __repr__(self):
        return f"<AGMParticipant user={self.user_id} agm={self.agm_id} role={self.role}>"
