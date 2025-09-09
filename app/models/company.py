from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)

    # 🔖 Basic Identity
    name = db.Column(db.String(255), nullable=False)
    registration_number = db.Column(db.String(100), nullable=True)
    vat_number = db.Column(db.String(100), nullable=True)
    tax_identifier = db.Column(db.String(100), nullable=True)
    company_type = db.Column(db.String(100), nullable=True)  # e.g., "Property Management", "Contractor", "OMC", "Director Group"
    industry = db.Column(db.String(100), nullable=True)  # e.g., Electrical, Property, Plumbing

    # 🌍 Jurisdictional Details
    country = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    currency = db.Column(db.String(10), default='EUR')  # ISO 4217 code
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

    # Add to Company
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    onboarding_completed = db.Column(db.Boolean, default=False, nullable=False)
    subdomain = db.Column(db.String(100), unique=True, index=True)   # optional now, useful later
    plan = db.Column(db.String(50), default="trial")                  # optional, for billing

    # 🧾 Compliance & Settings
    data_protection_compliant = db.Column(db.Boolean, default=False)
    terms_agreed = db.Column(db.Boolean, default=False)
    consent_to_communicate = db.Column(db.Boolean, default=False)
    default_settings = db.Column(JSON, nullable=True)  # Future config storage (AI, features, etc.)

    # 🎨 Branding
    logo_path = db.Column(db.String(255), nullable=True)
    brand_color = db.Column(db.String(20), nullable=True)  # HEX (e.g., #0099ff)



    # 🤖 AI & GAR Fields
    ai_behavior_profile = db.Column(JSON, nullable=True)  # AI settings per company
    gar_access_enabled = db.Column(db.Boolean, default=True)
    gar_training_data = db.Column(JSON, nullable=True)  # Optional scoped knowledge
    gar_internal_score = db.Column(db.String(20), nullable=True)
    ai_notes = db.Column(db.Text, nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 📅 Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 👥 Relationships (explicit + back_populates)
    users = db.relationship('User', back_populates='company', lazy=True)
    clients = db.relationship('Client', back_populates='company', lazy=True, overlaps="related_clients")
    units = db.relationship('Unit', back_populates='company', cascade='all, delete-orphan', lazy=True)
    work_orders = db.relationship('WorkOrder', back_populates='company', foreign_keys='WorkOrder.company_id', lazy=True)
    invoices = db.relationship('Invoice', back_populates='company', foreign_keys='Invoice.company_id', lazy=True)

    # ⚖️ 3rd-Party Integration Info
    integrations = db.Column(JSON, nullable=True)  # e.g., {'xero': {...}, 'quickbooks': {...}}
    sync_status = db.Column(db.String(50), nullable=True)

    onboarding_completed = db.Column(db.Boolean, nullable=False, default=False)
    onboarding_step      = db.Column(db.String(50), nullable=True)  # e.g. 'details', 'branding', 'billing

    def __repr__(self):
        return f"<Company {self.name} | Type: {self.company_type} | Country: {self.country}>"
