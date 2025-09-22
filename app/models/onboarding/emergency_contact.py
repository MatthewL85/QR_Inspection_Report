from __future__ import annotations
from datetime import datetime, time, date
from sqlalchemy import Enum, Index, text
from app.extensions import db

CoverageType = Enum(
    "24x7",
    "weeknights",   # e.g., Mon–Fri 18:00–08:00
    "weekends",     # Sat–Sun 24h
    "holidays",     # public holidays
    "custom",       # use start_time/end_time and days_of_week
    name="emergency_coverage_type_enum",
)

class EmergencyContact(db.Model):
    __tablename__ = "emergency_contacts"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True)

    # Who
    label        = db.Column(db.String(120), nullable=False)  # e.g., "On-Call Engineer", "Lift Contractor"
    provider     = db.Column(db.String(255), nullable=True)   # (optional) external provider name
    phone        = db.Column(db.String(50), nullable=False)
    alt_phone    = db.Column(db.String(50), nullable=True)
    email        = db.Column(db.String(255), nullable=True)
    notes        = db.Column(db.Text, nullable=True)

    # What (service category) — free text for flexibility or constrain later via enum/table
    service_type = db.Column(db.String(120), nullable=True)   # e.g., "Plumbing", "Electrical", "Lift", "General"

    # When (coverage)
    coverage     = db.Column(CoverageType, nullable=False, default="24x7")
    days_of_week = db.Column(db.String(20), nullable=True)    # csv like "0,1,2,3,4,5,6" (Mon=0) for custom
    start_time   = db.Column(db.Time, nullable=True)          # for custom/weeknights
    end_time     = db.Column(db.Time, nullable=True)

    # Routing
    priority     = db.Column(db.Integer, nullable=False, default=1)  # lower number = earlier in escalation
    active       = db.Column(db.Boolean, nullable=False, default=True)
    is_default   = db.Column(db.Boolean, nullable=False, default=False)  # one default per service_type (optional)

    # Validity window (if rotating schedules)
    valid_from   = db.Column(db.Date, nullable=True)
    valid_to     = db.Column(db.Date, nullable=True)

    created_at   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, onupdate=datetime.utcnow)

    company = db.relationship("Company", back_populates="emergency_contacts")

    __table_args__ = (
        Index("ix_emergency_contacts_company_service", "company_id", "service_type"),
        # Optional: enforce one default per (company_id, service_type)
        # Create as a partial unique index in Alembic:
        # UNIQUE (company_id, service_type) WHERE is_default = TRUE
    )

    def __repr__(self):
        return f"<EmergencyContact {self.label} {self.service_type} prio={self.priority} company={self.company_id}>"
