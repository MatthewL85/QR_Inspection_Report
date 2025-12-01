from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import validates
from app.extensions import db

# Only for type hints
if TYPE_CHECKING:  # pragma: no cover
    from .bank_account import BankAccount


class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)

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

    @validates("public_services_json")
    def _validate_public_services_json(self, key: str, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        s = str(value).strip()
        return s or None
