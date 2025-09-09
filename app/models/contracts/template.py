from app.extensions import db
from datetime import datetime

class ContractTemplate(db.Model):
    __tablename__ = "contract_templates"

    id = db.Column(db.Integer, primary_key=True)

    # Multi-tenant scoping (None = global template usable by all tenants)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)

    # Jurisdictional scoping
    jurisdiction = db.Column(db.String(16), nullable=False)   # e.g., "IE", "UK"
    authority    = db.Column(db.String(128), nullable=True)   # e.g., "PSRA"

    name        = db.Column(db.String(255), nullable=False, default="Management Agreement")
    description = db.Column(db.Text, nullable=True)
    is_active   = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    versions = db.relationship(
        "ContractTemplateVersion",
        backref="template",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="ContractTemplateVersion.created_at.desc()",
    )

    def latest_version(self):
        return self.versions.first()

    def __repr__(self) -> str:
        scope = "global" if self.company_id is None else f"company:{self.company_id}"
        return f"<ContractTemplate {self.jurisdiction}/{self.authority or '-'} {self.name} ({scope})>"
