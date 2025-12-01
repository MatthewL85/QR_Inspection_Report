# app/models/contracts/client_contract.py
from __future__ import annotations

import json
from datetime import datetime, date
from typing import Any, Dict, Optional

from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.extensions import db


class ClientContract(db.Model):
    __tablename__ = "client_contracts"

    # ---- core identity / foreign keys ----
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    template_version_id = db.Column(db.Integer, db.ForeignKey("contract_template_versions.id"), nullable=False)

    # ---- commercial terms ----
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    contract_value = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), default="EUR")
    next_fee_increase_date = db.Column(db.Date, nullable=True)

    # ---- extras (legacy JSON map as text) ----
    additional_fees = db.Column(db.Text, nullable=True)  # JSON map

    # ---- template-driven full payload (parties, fees, bank, insurer, schedules, signatures, branding) ----
    # Prefer JSONB on Postgres for indexing/perf
    data_json = db.Column(JSONB, nullable=True)

    # ---- generated artifacts + e-sign ----
    generated_html_path = db.Column(db.String(500), nullable=True)
    generated_pdf_path = db.Column(db.String(500), nullable=True)
    esign_provider = db.Column(db.String(32), nullable=True)   # "docusign"|"adobe"|"hellosign"|...
    esign_envelope_id = db.Column(db.String(128), nullable=True)
    sign_status = db.Column(db.String(32), default="Draft")    # Draft|Sent|Viewed|Signed|Declined|Expired

    # =========================
    # Governance (unifies governed + simple/SOW/PO/Variation)
    # =========================
    contract_kind = db.Column(db.String(32), nullable=True)        # "Governed"|"SOW"|"PO"|"Variation"|"Simple"
    governance_level = db.Column(db.String(16), nullable=True)     # "governed"|"simple"
    parent_contract_id = db.Column(db.Integer, db.ForeignKey("client_contracts.id"), nullable=True)
    compliance_status = db.Column(db.String(16), nullable=True)    # "ok"|"warn"|"block"
    compliance_message = db.Column(db.Text, nullable=True)

    # self-referential relationship for master/child (e.g., governed master → SOW/PO)
    parent_contract = relationship("ClientContract", remote_side=[id], backref="child_contracts", lazy="joined")

    # =========================
    # GAR / AI readiness
    # =========================

    # Immutable profile snapshot at creation (issuer/company summary — keep it light, no secrets)
    profile_snapshot = db.Column(JSONB, nullable=True)

    # Parsed content & structured extraction
    ai_parsed_text = db.Column(db.Text, nullable=True)                  # plain text of the contract
    ai_parsed_summary = db.Column(db.Text, nullable=True)               # human-readable summary
    ai_extracted_data = db.Column(JSONB, nullable=True)                 # key facts/clauses (term, notice, ppm, etc.)

    # Scoring / recommendation
    ai_scorecard = db.Column(JSONB, nullable=True)                      # rubric -> scores
    ai_rank = db.Column(db.Integer, nullable=True)                      # 1 = best in comparison set
    ai_is_preferred = db.Column(db.Boolean, default=False, nullable=False)
    ai_reason_for_recommendation = db.Column(db.Text, nullable=True)
    ai_recommendations = db.Column(JSONB, nullable=True)                # list of suggested clause edits
    ai_notes = db.Column(db.Text, nullable=True)                        # freeform reviewer/AI notes

    # Provenance / timestamps
    ai_model_name = db.Column(db.String(128), nullable=True)
    ai_model_version = db.Column(db.String(64), nullable=True)
    ai_policy_version = db.Column(db.String(64), nullable=True)
    ai_last_parsed_at = db.Column(db.DateTime, nullable=True)
    ai_last_scored_at = db.Column(db.DateTime, nullable=True)

    # Visibility / context / errors
    ai_visibility = db.Column(JSONB, nullable=True)                     # role-gated visibility flags
    ai_context = db.Column(JSONB, nullable=True)                        # inputs, prompt ids, feature flags
    ai_errors = db.Column(JSONB, nullable=True)                         # previous run errors for audit/debug

    # Optional semantic embedding (store as float array now; can migrate to pgvector later)
    ai_embedding = db.Column(ARRAY(db.Float), nullable=True)

    # ---- legacy/simple AI fields (kept for back-compat; prefer ai_* above) ----
    ai_extract = db.Column(db.Text, nullable=True)          # legacy: JSON of extracted key data
    ai_confidence_score = db.Column(db.Float, nullable=True)
    reviewed_by_ai = db.Column(db.Boolean, default=False)

    # ---- audit ----
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ---- relationships ----
    client = relationship("Client", backref="contracts")
    template_version = relationship("ContractTemplateVersion", backref="client_contracts")

    # ---- indexes (Postgres JSONB GIN for speed on common queries) ----
    __table_args__ = (
        Index("ix_client_contract_ai_extracted_gin", ai_extracted_data, postgresql_using="gin"),
        Index("ix_client_contract_ai_scorecard_gin", ai_scorecard, postgresql_using="gin"),
    )

    # =========================
    # Convenience helpers
    # =========================

    def fees_dict(self) -> dict:
        """Parse legacy additional_fees JSON text safely."""
        try:
            return json.loads(self.additional_fees) if self.additional_fees else {}
        except Exception:
            return {}

    def days_to_expiry(self) -> Optional[int]:
        return (self.end_date - date.today()).days if self.end_date else None

    def get_json(self, path: str, default: Any = None) -> Any:
        """
        Read a dotted path from data_json, e.g. 'fees.base_ex_vat'.
        """
        obj = self.data_json or {}
        cur = obj
        for key in path.split("."):
            if not isinstance(cur, dict) or key not in cur:
                return default
            cur = cur[key]
        return cur

    def set_json(self, path: str, value: Any) -> None:
        """
        Write a dotted path into data_json, creating nested dicts as needed.
        """
        obj = self.data_json or {}
        cur = obj
        keys = path.split(".")
        for key in keys[:-1]:
            cur = cur.setdefault(key, {})
        cur[keys[-1]] = value
        self.data_json = obj

    # Readability flags
    @property
    def is_draft(self) -> bool:
        return (self.sign_status or "Draft") == "Draft"

    @property
    def is_governed(self) -> bool:
        return (self.governance_level or "").lower() == "governed"

    @property
    def is_simple(self) -> bool:
        return (self.governance_level or "").lower() == "simple"

    def __repr__(self) -> str:
        return (
            f"<ClientContract id:{self.id} client:{self.client_id} tv:{self.template_version_id} "
            f"{self.start_date}->{self.end_date} status:{self.sign_status} kind:{self.contract_kind or '-'}>"
        )
