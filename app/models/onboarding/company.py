from __future__ import annotations

from datetime import datetime
import re
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import validates
from app.extensions import db

# Only for type hints
if TYPE_CHECKING:  # pragma: no cover
    from .bank_account import BankAccount


class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    organisation_uid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid4()), index=True)

    # 🔖 Basic Identity
    name = db.Column(db.String(255), nullable=False)
    registration_number = db.Column(db.String(100), nullable=True)
    vat_number = db.Column(db.String(100), nullable=True)
    tax_identifier = db.Column(db.String(100), nullable=True)
    company_type = db.Column(db.String(100), nullable=True)  # e.g., Property Mgmt, Contractor
    industry = db.Column(db.String(100), nullable=True)

    # 🌍 Jurisdictional Details
    country = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    currency = db.Column(db.String(10), default='EUR')
    timezone = db.Column(db.String(100), default='Europe/Dublin')
    preferred_language = db.Column(db.String(50), default='en')

    # 📞 Contact Info
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    website = db.Column(db.String(255), nullable=True)

    # 🏢 Address Info
    address_line1 = db.Column(db.String(255), nullable=True)
    address_line2 = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(50), nullable=True)

    # ✅ Company lifecycle / plan
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    onboarding_completed = db.Column(db.Boolean, default=False, nullable=False)
    onboarding_step = db.Column(db.String(50), nullable=True)
    subdomain = db.Column(db.String(100), unique=True, index=True)
    plan = db.Column(db.String(50), default="trial")

    # 🧾 Compliance & Settings
    data_protection_compliant = db.Column(db.Boolean, default=False)
    terms_agreed = db.Column(db.Boolean, default=False)
    consent_to_communicate = db.Column(db.Boolean, default=False)
    default_settings = db.Column(JSON, nullable=True)

    # 🎨 Branding
    logo_path = db.Column(db.String(255), nullable=True)
    brand_color = db.Column(db.String(20), nullable=True)
    brand_primary_color = db.Column(db.String(20), nullable=True)
    brand_secondary_color = db.Column(db.String(20), nullable=True)

    # 🌐 Public Profile / Microsite
    is_public_profile_enabled = db.Column(db.Boolean, default=False, nullable=False)
    public_slug = db.Column(db.String(120), unique=True, index=True)
    public_about_md = db.Column(db.Text, nullable=True)
    public_services_json = db.Column(db.Text, nullable=True)
    public_show_contact_form = db.Column(db.Boolean, default=True, nullable=False)
    work_order_prefix = db.Column(db.String(12), unique=True, nullable=True, index=True)

    # 🤖 AI & GAR Fields
    ai_behavior_profile = db.Column(JSON, nullable=True)
    gar_access_enabled = db.Column(db.Boolean, default=True)
    gar_training_data = db.Column(JSON, nullable=True)
    gar_internal_score = db.Column(db.String(20), nullable=True)
    ai_notes = db.Column(db.Text, nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 📅 Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 👥 Relationships
    users = db.relationship('User', back_populates='company', lazy=True)
    clients = db.relationship('Client', back_populates='company', lazy=True, overlaps="related_clients")

    units = db.relationship(
        'Unit',
        back_populates='company',
        cascade='all, delete-orphan',
        lazy=True
    )

    work_orders = db.relationship(
        'WorkOrder',
        back_populates='company',
        foreign_keys='WorkOrder.company_id',
        lazy=True
    )

    invoices = db.relationship(
        'Invoice',
        back_populates='company',
        foreign_keys='Invoice.company_id',
        lazy=True
    )

    # ⭐ NEW — REQUIRED to fix current SQLAlchemy error
    blocks = db.relationship(
        "Block",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # 💳 Banking
    bank_accounts = db.relationship(
        'BankAccount',
        back_populates='company',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    insurance_policies = db.relationship(
        "InsurancePolicy",
        back_populates="company",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    emergency_contacts = db.relationship(
        "EmergencyContact",
        back_populates="company",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    licenses = db.relationship(
        "CompanyLicense",
        back_populates="company",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    # ⚖️ Integrations
    module_subscriptions = db.relationship(
        "ModuleSubscription",
        back_populates="company",
        lazy="dynamic",
        cascade="all, delete-orphan",
        foreign_keys="ModuleSubscription.company_id",
    )

    sent_connection_invites = db.relationship(
        "OrganisationConnectionInvite",
        back_populates="source_company",
        lazy="dynamic",
        foreign_keys="OrganisationConnectionInvite.source_company_id",
    )

    received_connection_invites = db.relationship(
        "OrganisationConnectionInvite",
        back_populates="target_company",
        lazy="dynamic",
        foreign_keys="OrganisationConnectionInvite.target_company_id",
    )

    outgoing_organisation_connections = db.relationship(
        "OrganisationConnection",
        back_populates="source_company",
        lazy="dynamic",
        foreign_keys="OrganisationConnection.source_company_id",
    )

    incoming_organisation_connections = db.relationship(
        "OrganisationConnection",
        back_populates="target_company",
        lazy="dynamic",
        foreign_keys="OrganisationConnection.target_company_id",
    )

    integrations = db.Column(JSON, nullable=True)
    sync_status = db.Column(db.String(50), nullable=True)

    # ---------- Helpers ----------
    def __repr__(self):
        return f"<Company {self.name} | Type: {self.company_type} | Country: {self.country}>"

    @property
    def theme_primary(self) -> str:
        return self.brand_primary_color or self.brand_color or "#3f51b5"

    @property
    def theme_secondary(self) -> str:
        return self.brand_secondary_color or "#9fa8da"

    @property
    def display_name(self) -> str:
        return self.name

    def address_block(self) -> str:
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country,
        ]
        return ", ".join([p for p in parts if p])

    @property
    def work_order_code(self) -> str:
        return self._normalise_work_order_prefix(self.work_order_prefix) or self._derive_work_order_prefix()

    @staticmethod
    def _normalise_work_order_prefix(value: Optional[str]) -> str:
        return re.sub(r"[^A-Z0-9]", "", (value or "").upper())[:8]

    def _derive_work_order_prefix(self) -> str:
        ignored = {
            "APARTMENT",
            "BLOCK",
            "CLG",
            "COMPANY",
            "ESTATE",
            "LIMITED",
            "LTD",
            "MANAGEMENT",
            "PROPERTY",
            "PROPERTIES",
            "SERVICES",
            "THE",
        }
        words = re.findall(r"[A-Za-z0-9]+", self.name or self.subdomain or "")
        meaningful_words = [word for word in words if word.upper() not in ignored]
        if len(meaningful_words) == 1:
            return self._normalise_work_order_prefix(meaningful_words[0][:3]) or f"C{self.id or ''}"
        initials = "".join(word[0] for word in meaningful_words[:4])
        return self._normalise_work_order_prefix(initials) or f"C{self.id or ''}"

    @validates("public_services_json")
    def _validate_public_services_json(self, key: str, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        s = str(value).strip()
        return s or None
