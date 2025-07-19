from datetime import datetime
from app.extensions import db

class TeamMessage(db.Model):
    __tablename__ = 'team_messages'

    id = db.Column(db.Integer, primary_key=True)

    contractor_id = db.Column(db.Integer, db.ForeignKey('contractors.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('contractor_teams.id'), nullable=True)      # Null = global/broadcast
    recipient_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)       # Null = all team members

    message_body = db.Column(db.Text, nullable=False)
    is_urgent = db.Column(db.Boolean, default=False)
    attachment_url = db.Column(db.String(255), nullable=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🧠 AI/GAR Summary & Alerting
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    parsed_at = db.Column(db.DateTime, nullable=True)
    gar_sensitivity_flag = db.Column(db.Boolean, default=False)
    gar_communication_risk = db.Column(db.Text, nullable=True)

    # 🧠 GAR Chat Layer
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🔗 Relationships
    contractor = db.relationship('Contractor', backref='team_messages')
    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient_user = db.relationship('User', foreign_keys=[recipient_user_id])
    team = db.relationship('ContractorTeam', backref='messages')

    def __repr__(self):
        return f"<TeamMessage id={self.id} to_team={self.team_id} urgent={self.is_urgent}>"
