# app/models/inspection_schedule.py

from datetime import datetime
from app.extensions import db

class InspectionSchedule(db.Model):
    __tablename__ = 'inspection_schedules'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Contractor or PM

    equipment = db.relationship('Equipment', backref='inspection_schedules')
    assigned_to = db.relationship('User', backref='inspection_schedules')

    # 📅 Core Scheduling
    frequency = db.Column(db.String(50), nullable=False)                     # Weekly, Monthly, Quarterly, Annually
    start_date = db.Column(db.Date, nullable=False)
    next_due_date = db.Column(db.Date, nullable=True)
    last_inspection_date = db.Column(db.Date, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    # 🧠 AI/GAR Fields
    ai_parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)                       # {"cycle_length_days": 90}
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    parsed_at = db.Column(db.DateTime, nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)

    ai_scheduling_risk = db.Column(db.Text, nullable=True)                   # e.g., “Too infrequent for asset type”
    ai_recommended_frequency = db.Column(db.String(50), nullable=True)       # Suggested frequency
    ai_alignment_score = db.Column(db.Float, nullable=True)                  # 0.0–1.0 confidence in match
    gar_notes = db.Column(db.Text, nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)


    # 🔐 Security & Integration
    visibility_scope = db.Column(db.String(100), default='Admin,PM,Contractor')
    is_private = db.Column(db.Boolean, default=False)
    shared_with_director = db.Column(db.Boolean, default=False)
    consent_verified = db.Column(db.Boolean, default=False)

    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    is_external = db.Column(db.Boolean, default=False)
    sync_status = db.Column(db.String(50), default='Pending')  # Pending, Synced, Failed

    def __repr__(self):
        return f"<InspectionSchedule id={self.id} frequency={self.frequency} next_due={self.next_due_date}>"
