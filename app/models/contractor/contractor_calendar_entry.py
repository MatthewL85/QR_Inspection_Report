from datetime import datetime

from app.extensions import db


class ContractorCalendarEntry(db.Model):
    __tablename__ = "contractor_calendar_entries"

    id = db.Column(db.Integer, primary_key=True)
    job_docket_id = db.Column(db.Integer, db.ForeignKey("job_dockets.id", ondelete="CASCADE"), nullable=False, index=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    contractor_id = db.Column(db.Integer, db.ForeignKey("contractors.id"), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=True, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=True, index=True)

    assigned_engineer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    assigned_engineer_ids = db.Column(db.JSON, nullable=True)
    assigned_team_id = db.Column(db.Integer, db.ForeignKey("contractor_teams.id"), nullable=True, index=True)

    title = db.Column(db.String(180), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    estimated_duration_minutes = db.Column(db.Integer, nullable=True)
    calendar_status = db.Column(db.String(60), nullable=False, default="Scheduled", index=True)
    priority = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    ics_uid = db.Column(db.String(120), unique=True, nullable=True, index=True)

    gar_chat_ready = db.Column(db.Boolean, nullable=False, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    job_docket = db.relationship("JobDocket", back_populates="calendar_entries")
    work_order = db.relationship("WorkOrder")
    contractor = db.relationship("Contractor", backref="calendar_entries")
    company = db.relationship("Company")
    client = db.relationship("Client")
    unit = db.relationship("Unit")
    assigned_engineer = db.relationship("User", foreign_keys=[assigned_engineer_id])
    assigned_team = db.relationship("ContractorTeam", foreign_keys=[assigned_team_id])
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    updated_by = db.relationship("User", foreign_keys=[updated_by_id])

    __table_args__ = (
        db.Index("ix_contractor_calendar_contractor_date", "contractor_id", "scheduled_date"),
        db.Index("ix_contractor_calendar_engineer_date", "assigned_engineer_id", "scheduled_date"),
    )

    def __repr__(self):
        return f"<ContractorCalendarEntry docket={self.job_docket_id} date={self.scheduled_date}>"
