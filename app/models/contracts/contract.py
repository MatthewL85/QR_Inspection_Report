from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, ForeignKey,
    Numeric, Enum, Boolean, Text, Index, text
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship, validates
from app.extensions import db

# ── Status helper (kept for readability; field below still uses SQL Enum of strings) ──
class ContractStatus(enum.Enum):
    DRAFT = "Draft"
    IN_REVIEW = "In Review"
    ACTIVE = "Active"
    EXPIRED = "Expired"
    TERMINATED = "Terminated"
    ARCHIVED = "Archived"  # ← NEW

class Contract(db.Model):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    company = relationship("Company", backref="contracts")

    profile_snapshot = Column(JSONB, nullable=False, default=dict)

    # ---- core fields ----
    contract_title = Column(String(255), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    currency = Column(String(8), default="EUR")
    contract_value = Column(Numeric(12, 2), default=0)
    ppm_schedule = Column(String(255), nullable=True)
    primary_contact_name = Column(String(255), nullable=True)
    primary_contact_email = Column(String(255), nullable=True)
    primary_contact_phone = Column(String(64), nullable=True)

    # include "Archived" in SQL Enum set
    status = Column(
        Enum(
            "Draft", "In Review", "Active", "Expired", "Terminated", "Archived",
            name="contract_status_enum"
        ),
        default="Draft",
        nullable=False
    )

    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_edited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    activated_at = Column(DateTime, nullable=True)

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_edited_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # soft-delete flag (kept)
    is_deleted = Column(Boolean, default=False, nullable=False, server_default=text("false"))

    # ---- NEW: archive metadata (soft-archive over hard delete) ----
    archived_at = Column(DateTime, nullable=True)                           # when archived
    archived_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    archived_reason = Column(String(255), nullable=True)

    archived_by = relationship("User", foreign_keys=[archived_by_user_id])

    # ---------- GAR / AI readiness ----------
    ai_parsed_text = Column(Text, nullable=True)
    ai_parsed_summary = Column(Text, nullable=True)
    ai_extracted_data = Column(JSONB, nullable=True, default=dict)
    ai_scorecard = Column(JSONB, nullable=True, default=dict)
    ai_rank = Column(Integer, nullable=True)
    ai_is_preferred = Column(Boolean, default=False, nullable=False, server_default=text("false"))
    ai_reason_for_recommendation = Column(Text, nullable=True)
    ai_recommendations = Column(JSONB, nullable=True, default=list)
    ai_notes = Column(Text, nullable=True)
    ai_model_name = Column(String(128), nullable=True)
    ai_model_version = Column(String(64), nullable=True)
    ai_policy_version = Column(String(64), nullable=True)
    ai_last_parsed_at = Column(DateTime, nullable=True)
    ai_last_scored_at = Column(DateTime, nullable=True)
    ai_visibility = Column(JSONB, nullable=True, default=lambda: {
        "super_admin": True, "admin": True, "property_manager": True, "contractor": False, "director": True
    })
    ai_embedding = Column(ARRAY(db.Float), nullable=True)
    ai_context = Column(JSONB, nullable=True, default=dict)
    ai_errors = Column(JSONB, nullable=True, default=list)

    # ---- conveniences ----
    @property
    def is_editable(self) -> bool:
        return (self.status or "") in {"Draft", "In Review"}

    @property
    def is_archived(self) -> bool:
        # Treat either explicit status or presence of archived_at as archived
        return (self.status or "") == "Archived" or self.archived_at is not None

    @validates("end_date")
    def validate_dates(self, key, value):
        if value and self.start_date and value < self.start_date:
            raise ValueError("End date cannot be before start date.")
        return value

# Helpful GIN indexes for JSON queries
Index("ix_contract_ai_extracted_gin", Contract.ai_extracted_data, postgresql_using="gin")
Index("ix_contract_ai_scorecard_gin", Contract.ai_scorecard, postgresql_using="gin")
