# app/models/client/key_info.py
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.extensions import db

# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────

KeyInfoStatus = Enum("active", "archived", name="key_info_status")
ChangeStatus = Enum("pending", "approved", "rejected", name="key_info_change_status")

# ──────────────────────────────────────────────────────────────────────────────
# Small JSON helpers (robust defaults for AI/GAR fields)
# ──────────────────────────────────────────────────────────────────────────────

def _ensure_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (set, tuple)):
        return list(value)
    return [value]

def _ensure_dict(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return dict(value)
    except Exception:
        return {"_raw": value}

# ──────────────────────────────────────────────────────────────────────────────
# Models
# ──────────────────────────────────────────────────────────────────────────────

class ClientKeyInfo(db.Model):
    """
    Published ("live") Key Site Information for a client.
    One row per section (e.g., GATES, LIFTS, ELECTRICAL).
    Edits flow through ClientKeyInfoChange and are applied on approval.
    """
    __tablename__ = "client_key_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # tenant scope
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # section
    title: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(KeyInfoStatus, default="active", nullable=False)

    # approvals & audit
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_submitted_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # AI/GAR (live snapshot)
    ai_parsed_text: Mapped[Optional[str]] = mapped_column(Text)
    ai_parsed_summary: Mapped[Optional[str]] = mapped_column(String(1000))
    ai_extracted_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    ai_tags: Mapped[list] = mapped_column(JSONB, default=list)
    ai_redaction_hints: Mapped[dict] = mapped_column(JSONB, default=dict)
    ai_visibility_flags: Mapped[dict] = mapped_column(JSONB, default=dict)
    ai_scorecard: Mapped[dict] = mapped_column(JSONB, default=dict)
    ai_rank: Mapped[Optional[int]] = mapped_column(Integer)

    # relationships
    shares: Mapped[List["ClientKeyInfoShare"]] = relationship(
        "ClientKeyInfoShare",
        back_populates="key_info",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    changes: Mapped[List["ClientKeyInfoChange"]] = relationship(
        "ClientKeyInfoChange",
        back_populates="key_info",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("client_id", "title", name="uq_client_key_info_client_title"),
        Index("ix_client_key_info_client_status", "client_id", "status"),
    )

    # JSON validators
    @validates("ai_extracted_data", "ai_redaction_hints", "ai_visibility_flags", "ai_scorecard")
    def _v_dict(self, key: str, value: Any) -> dict:
        return _ensure_dict(value)

    @validates("ai_tags")
    def _v_list(self, key: str, value: Any) -> list:
        return _ensure_list(value)

    def __repr__(self) -> str:
        return f"<ClientKeyInfo id={self.id} client={self.client_id} title={self.title!r} status={self.status}>"

class ClientKeyInfoChange(db.Model):
    """
    Proposed changes (or new sections) awaiting approval.
    - Created by Admin/PM/Financial Controller/Super Admin
      (and optionally by Contractors when enabled)
    - Approved/Rejected by Property Manager or Super Admin
    """
    __tablename__ = "client_key_info_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # If editing an existing section; None when proposing a brand-new section
    key_info_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("client_key_info.id", ondelete="CASCADE"), index=True
    )
    key_info: Mapped[Optional[ClientKeyInfo]] = relationship(
        "ClientKeyInfo", back_populates="changes", lazy="selectin"
    )

    # proposed content
    proposed_title: Mapped[str] = mapped_column(String(160), nullable=False)
    proposed_content: Mapped[str] = mapped_column(Text, nullable=False)

    # explicit per-contractor visibility to apply on approval
    proposed_contractor_ids: Mapped[list] = mapped_column(JSONB, default=list)

    # contractor professional attestation (optional)
    pro_attested_by_contractor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pro_attestation_note: Mapped[Optional[str]] = mapped_column(String(500))

    # submitter + decision
    submitted_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    status: Mapped[str] = mapped_column(ChangeStatus, default="pending", index=True, nullable=False)
    decided_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    decision_reason: Mapped[Optional[str]] = mapped_column(String(300))

    # AI/GAR (proposed snapshot)
    ai_parsed_text: Mapped[Optional[str]] = mapped_column(Text)
    ai_parsed_summary: Mapped[Optional[str]] = mapped_column(String(1000))
    ai_extracted_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    ai_tags: Mapped[list] = mapped_column(JSONB, default=list)
    ai_redaction_hints: Mapped[dict] = mapped_column(JSONB, default=dict)
    ai_visibility_flags: Mapped[dict] = mapped_column(JSONB, default=dict)
    ai_scorecard: Mapped[dict] = mapped_column(JSONB, default=dict)
    ai_rank: Mapped[Optional[int]] = mapped_column(Integer)

    __table_args__ = (
        Index("ix_key_info_changes_client_status", "client_id", "status"),
        CheckConstraint(
            "status IN ('pending','approved','rejected')",
            name="ck_key_info_changes_status_valid",
        ),
    )

    # validators
    @validates("proposed_contractor_ids")
    def _v_contractor_ids(self, key: str, value: Any) -> list:
        ids = _ensure_list(value)
        out: list[int] = []
        for v in ids:
            try:
                out.append(int(v))
            except Exception:
                continue
        return out

    @validates("ai_extracted_data", "ai_redaction_hints", "ai_visibility_flags", "ai_scorecard")
    def _v_dict(self, key: str, value: Any) -> dict:
        return _ensure_dict(value)

    @validates("ai_tags")
    def _v_list(self, key: str, value: Any) -> list:
        return _ensure_list(value)

    def __repr__(self) -> str:
        return f"<ClientKeyInfoChange id={self.id} client={self.client_id} status={self.status}>"

class ClientKeyInfoShare(db.Model):
    """
    Explicit per-contractor visibility mapping for a published Key Info section.
    Only sections with a share row are visible to that contractor.
    """
    __tablename__ = "client_key_info_shares"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    key_info_id: Mapped[int] = mapped_column(
        ForeignKey("client_key_info.id", ondelete="CASCADE"), index=True, nullable=False
    )
    key_info: Mapped[ClientKeyInfo] = relationship(
        "ClientKeyInfo", back_populates="shares", lazy="selectin"
    )

    # NOTE: If your table is named differently (e.g., "contractor"), adjust the FK string.
    contractor_id: Mapped[int] = mapped_column(
        ForeignKey("contractors.id", ondelete="CASCADE"), index=True, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("key_info_id", "contractor_id", name="uq_key_info_share_unique"),
        Index("ix_key_info_share_key_info_contractor", "key_info_id", "contractor_id"),
    )

    def __repr__(self) -> str:
        return f"<ClientKeyInfoShare key_info={self.key_info_id} contractor={self.contractor_id}>"
