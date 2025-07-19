from datetime import datetime
from app.extensions import db

class TeamSchedule(db.Model):
    __tablename__ = 'team_schedules'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('contractor_teams.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)

    shift_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # 🧠 AI & GAR
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    gar_conflict_flag = db.Column(db.Boolean, default=False)
    gar_coverage_score = db.Column(db.Float, nullable=True)
    gar_scheduling_notes = db.Column(db.Text, nullable=True)

    # 📎 Metadata
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    team = db.relationship('ContractorTeam', backref='schedules')
    unit = db.relationship('Unit', backref='team_schedules')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    updated_by = db.relationship('User', foreign_keys=[updated_by_id])

    def __repr__(self):
        return f"<TeamSchedule team_id={self.team_id} shift_date={self.shift_date}>"
