from app.extensions import db
from datetime import datetime
import json


class ContractTemplateVersion(db.Model):
    __tablename__ = "contract_template_versions"

    id          = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey("contract_templates.id"), nullable=False)

    version_label  = db.Column(db.String(64), nullable=False)  # e.g., "v2025.09-PSRA"
    effective_from = db.Column(db.Date, nullable=True)
    source_url     = db.Column(db.String(500), nullable=True)  # official source if scraped
    checksum       = db.Column(db.String(128), nullable=True)  # to detect upstream changes

    # Store renderable contract **HTML** with Jinja placeholders (render -> PDF)
    html_template = db.Column(db.Text, nullable=False)

    # NEW: JSON schema that describes what fields to ask for in the UI
    form_schema   = db.Column(db.Text, nullable=True)

    # AI & GAR metadata
    ai_summary    = db.Column(db.Text, nullable=True)
    ai_clause_map = db.Column(db.Text, nullable=True)  # JSON: {"termination_notice_days": 30, ...}
    ai_status     = db.Column(db.String(32), default="Published")  # Draft | Needs Review | Published

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Helpers
    def clause_map(self) -> dict:
        try:
            return json.loads(self.ai_clause_map) if self.ai_clause_map else {}
        except Exception:
            return {}

    def __repr__(self) -> str:
        return f"<ContractTemplateVersion {self.version_label} of tpl:{self.template_id}>"
