from __future__ import annotations
from datetime import datetime, date
from sqlalchemy import Enum, Index, text
from app.extensions import db

LicenseStatus = Enum("active", "suspended", "expired", "pending", name="company_license_status_enum")

class CompanyLicense(db.Model):
    __tablename__ = "company_licenses"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True)

    # Jurisdiction targeting (mirror your client jurisdiction fields)
    country = db.Column(db.String(100), nullable=False)     # e.g., "Ireland"
    region  = db.Column(db.String(100), nullable=True)      # e.g., "Dublin"
    city    = db.Column(db.String(100), nullable=True)      # optional

    # Regulator & licence
    regulator_name  = db.Column(db.String(255), nullable=False)  # e.g., "RTB", "PSRA", "RECI/Safe Electric"
    license_type    = db.Column(db.String(120), nullable=True)   # e.g., "PSRA Category D"
    license_number  = db.Column(db.String(120), nullable=False)
    scope_json      = db.Column(db.Text, nullable=True)          # JSON list of permitted services/categories
    status          = db.Column(LicenseStatus, nullable=False, server_default="active")

    valid_from      = db.Column(db.Date, nullable=True)
    expiry_date     = db.Column(db.Date, nullable=True, index=True)
    is_default      = db.Column(db.Boolean, default=False, nullable=False)  # default for this (company, country, region)
    active          = db.Column(db.Boolean, default=True, nullable=False)

    document_path   = db.Column(db.String(255), nullable=True)  # uploaded cert
    created_at      = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at      = db.Column(db.DateTime, onupdate=datetime.utcnow)

    company = db.relationship("Company", back_populates="licenses")

    __table_args__ = (
        Index("ix_company_licenses_company_loc", "company_id", "country", "region"),
        # One default per company per (country, region) — PostgreSQL partial unique index (set in migration)
        # UNIQUE (company_id, country, region) WHERE is_default = TRUE
    )

    def __repr__(self):
        j = ", ".join([p for p in [self.city, self.region, self.country] if p])
        return f"<CompanyLicense {self.regulator_name} #{self.license_number} [{j}]>"
