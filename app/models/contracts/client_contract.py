from app.extensions import db
from datetime import datetime, date
import json
from typing import Any, Dict, Optional


class ClientContract(db.Model):
    __tablename__ = "client_contracts"

    id         = db.Column(db.Integer, primary_key=True)
    client_id  = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    template_version_id = db.Column(db.Integer, db.ForeignKey("contract_template_versions.id"), nullable=False)

    # Commercial terms
    start_date        = db.Column(db.Date, nullable=False)
    end_date          = db.Column(db.Date, nullable=False)
    contract_value    = db.Column(db.Numeric(12, 2), nullable=False)
    currency          = db.Column(db.String(10), default="EUR")
    next_fee_increase_date = db.Column(db.Date, nullable=True)

    # Flexible extras (e.g., Company Secretary, Out of Hours, etc.)
    additional_fees   = db.Column(db.Text, nullable=True)  # JSON map
    def fees_dict(self) -> dict:
        try:
            return json.loads(self.additional_fees) if self.additional_fees else {}
        except Exception:
            return {}

    # NEW: generic JSON payload for all template-driven fields (parties, fees, bank, insurer, schedules, signatures, branding)
    data_json         = db.Column(db.JSON, nullable=True)

    # Generated artifacts + e-sign
    generated_html_path = db.Column(db.String(500), nullable=True)
    generated_pdf_path  = db.Column(db.String(500), nullable=True)
    esign_provider     = db.Column(db.String(32), nullable=True)   # "docusign"|"adobe"|"hellosign"
    esign_envelope_id  = db.Column(db.String(128), nullable=True)
    sign_status        = db.Column(db.String(32), default="Draft") # Draft|Sent|Viewed|Signed|Declined

    # AI/GAR (post-sign parse or validation summary)
    ai_extract          = db.Column(db.Text, nullable=True)         # JSON of extracted key data
    ai_confidence_score = db.Column(db.Float, nullable=True)
    reviewed_by_ai      = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    client           = db.relationship("Client", backref="contracts")
    template_version = db.relationship("ContractTemplateVersion", backref="client_contracts")

    # ---- Convenience helpers ----
    def days_to_expiry(self) -> Optional[int]:
        return (self.end_date - date.today()).days if self.end_date else None

    def get_json(self, path: str, default: Any = None) -> Any:
        """
        Read a dotted path from data_json, e.g. get_json('fees.base_ex_vat').
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

    def __repr__(self) -> str:
        return f"<ClientContract client:{self.client_id} tv:{self.template_version_id} {self.start_date}->{self.end_date}>"

