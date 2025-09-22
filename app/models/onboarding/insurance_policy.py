from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Index, Enum, text
from app.extensions import db

PolicyType = Enum(
    "Public Liability",
    "Employers Liability",
    "Professional Indemnity",
    "Contractors All Risks",
    name="insurance_policy_type_enum",
)

class InsurancePolicy(db.Model):
    __tablename__ = "insurance_policies"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True)

    # Core
    policy_type    = db.Column(PolicyType, nullable=False, index=True)
    provider       = db.Column(db.String(255), nullable=True)
    policy_number  = db.Column(db.String(100), nullable=True, index=True)
    coverage_amount = db.Column(db.Numeric(18, 2), nullable=True)  # e.g., 6500000.00
    currency       = db.Column(db.String(10), nullable=True)       # e.g., 'EUR'

    start_date     = db.Column(db.Date, nullable=True)
    expiry_date    = db.Column(db.Date, nullable=True, index=True)

    # Management
    is_default     = db.Column(db.Boolean, default=False, nullable=False)  # one default per (company, policy_type)
    active         = db.Column(db.Boolean, default=True, nullable=False)

    # Stored document (optional)
    document_path  = db.Column(db.String(255), nullable=True)
    document_mime  = db.Column(db.String(100), nullable=True)
    file_size      = db.Column(db.Integer, nullable=True)  # bytes

    # Timestamps
    created_at     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at     = db.Column(db.DateTime, onupdate=datetime.utcnow)

    company = db.relationship("Company", back_populates="insurance_policies")

    __table_args__ = (
        # Fast queries by owner/type/status
        Index("ix_ins_policies_company_type", "company_id", "policy_type"),
        # One default per (company, policy_type)
        # (enforced in Postgres via partial unique index created in migration)
    )

    def __repr__(self):
        return f"<InsurancePolicy {self.policy_type} #{self.policy_number} company={self.company_id}>"

    @property
    def is_expired(self) -> bool:
        return bool(self.expiry_date and self.expiry_date < date.today())
