# app/models/audit/contract_audit.py
from __future__ import annotations

from datetime import datetime  # noqa: F401 (parity with other models)
from typing import Any, Dict, Optional
import json

from sqlalchemy.sql import func
from sqlalchemy.orm import validates, synonym as sa_synonym

from app.extensions import db

# Optional helper: prefer your central JSON helpers if available
try:
    from app.utils.json_helpers import ensure_json_string  # type: ignore
except Exception:  # pragma: no cover
    def ensure_json_string(value: Any) -> Optional[str]:
        """
        Fallback: convert dict/list -> JSON string; pass through str/None; empty '' -> None.
        """
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        s = str(value).strip()
        return s or None


class ContractAudit(db.Model):
    __tablename__ = "contract_audits"

    id = db.Column(db.Integer, primary_key=True)

    # The contract this audit row belongs to
    contract_id = db.Column(
        db.Integer,
        db.ForeignKey("client_contracts.id"),
        nullable=False,
        index=True,
    )

    # Optional: who performed the action (if available)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    # Accept "actor_id" in services/routes as an alias of user_id
    actor_id = sa_synonym("user_id")

    # action: e.g. "create_draft" | "inline_update" | "apply_update" | "renewal" | ...
    action = db.Column(db.String(64), nullable=False)

    # WHEN the audited thing actually happened (distinct from created_at insert time)
    happened_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # JSON string with details (changed fields, accepted sections, etc.)
    detail_json = db.Column(db.Text, nullable=True)

    # ⬇️ Common service payloads
    # Snapshots before/after (stored as JSON strings)
    before_data = db.Column(db.Text, nullable=True)
    after_data = db.Column(db.Text, nullable=True)
    # Optional compact diff/changeset if you compute one
    change_set = db.Column(db.Text, nullable=True)

    # Free-text notes (services pass notes=...)
    notes = db.Column(db.Text, nullable=True)

    # --- AI parsing (Phase 1) ---
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.Text, nullable=True)   # JSON string

    # --- GAR scoring fields ---
    ai_scorecard = db.Column(db.Text, nullable=True)     # JSON string
    ai_rank = db.Column(db.Integer, nullable=True)
    is_ai_preferred = db.Column(db.Boolean, nullable=True)
    reason_for_recommendation = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    contract = db.relationship(
        "ClientContract",
        backref=db.backref("audits", lazy="dynamic", cascade="all, delete-orphan"),
    )
    performed_by = db.relationship("User", foreign_keys=[user_id], lazy="joined")

    __table_args__ = (
        # Fast list views & timelines
        db.Index("ix_contract_audits_contract_happened_at", "contract_id", "happened_at"),
    )

    # -------------------------
    # Validators / conveniences
    # -------------------------
    @validates("detail_json", "extracted_data", "ai_scorecard", "before_data", "after_data", "change_set")
    def _validate_jsonish(self, key: str, value: Any) -> Optional[str]:
        return ensure_json_string(value)

    # Convenience accessors (read parsed dicts safely in code/Jinja)
    @property
    def detail(self) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(self.detail_json) if self.detail_json else None
        except Exception:
            return None

    @property
    def before(self) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(self.before_data) if self.before_data else None
        except Exception:
            return None

    @property
    def after(self) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(self.after_data) if self.after_data else None
        except Exception:
            return None

    @property
    def changes(self) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(self.change_set) if self.change_set else None
        except Exception:
            return None

    @property
    def extracted(self) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(self.extracted_data) if self.extracted_data else None
        except Exception:
            return None

    @property
    def scorecard(self) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(self.ai_scorecard) if self.ai_scorecard else None
        except Exception:
            return None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ContractAudit id={self.id} contract_id={self.contract_id} action={self.action} happened_at={self.happened_at}>"
