from datetime import datetime

from app.extensions import db


class CoreDocumentTemplate(db.Model):
    __tablename__ = "core_document_templates"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True, index=True)

    module_key = db.Column(db.String(80), nullable=False, index=True)
    document_type = db.Column(db.String(80), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(40), nullable=False, default="Active", index=True)
    version_label = db.Column(db.String(40), nullable=False, default="v1")
    template_format = db.Column(db.String(40), nullable=False, default="html")

    html_body = db.Column(db.Text, nullable=True)
    terms_body = db.Column(db.Text, nullable=True)
    footer_body = db.Column(db.Text, nullable=True)

    logo_mode = db.Column(db.String(40), nullable=False, default="company")
    primary_brand_source = db.Column(db.String(40), nullable=False, default="company")
    include_signature_block = db.Column(db.Boolean, nullable=False, default=False)
    include_terms = db.Column(db.Boolean, nullable=False, default=True)

    number_prefix = db.Column(db.String(30), nullable=True)
    sequence_padding = db.Column(db.Integer, nullable=False, default=5)
    supported_output_formats = db.Column(db.JSON, nullable=True)
    required_context_keys = db.Column(db.JSON, nullable=True)
    default_context = db.Column(db.JSON, nullable=True)
    visibility_scope = db.Column(db.String(80), nullable=False, default="company")
    is_locked = db.Column(db.Boolean, nullable=False, default=False)

    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = db.relationship("Company", backref=db.backref("document_templates", lazy=True))
    created_by = db.relationship("User", foreign_keys=[created_by_id], backref="created_document_templates")
    updated_by = db.relationship("User", foreign_keys=[updated_by_id], backref="updated_document_templates")

    __table_args__ = (
        db.UniqueConstraint(
            "company_id",
            "module_key",
            "document_type",
            "version_label",
            name="uq_core_document_template_scope_version",
        ),
    )

    @property
    def is_active(self):
        return (self.status or "").lower() == "active"

    @property
    def scope_label(self):
        return "Global" if self.company_id is None else "Company"

    def __repr__(self):
        return f"<CoreDocumentTemplate {self.module_key}:{self.document_type} {self.version_label}>"
