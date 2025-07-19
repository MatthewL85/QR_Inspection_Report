from app.extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    profile_photo = db.Column(db.String(255))  # 📷 Path to uploaded profile image

    # 🔗 Relationships
    role_id = db.Column(
        db.Integer,
        db.ForeignKey('roles.id', use_alter=True, name='fk_user_role', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    role = db.relationship('Role', back_populates='users')

    company_id = db.Column(
        db.Integer,
        db.ForeignKey('clients.id', use_alter=True, name='fk_user_client', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    company = db.relationship('Client', foreign_keys=[company_id], backref='users')

    contractor_id = db.Column(
        db.Integer,
        db.ForeignKey('contractors.id', use_alter=True, name='fk_user_contractor', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    contractor = db.relationship('Contractor', backref='users')

    submitted_quotes = db.relationship('QuoteResponse', backref='submitted_by', foreign_keys='QuoteResponse.submitted_by_id')
    received_quote_invites = db.relationship('QuoteRecipient', backref='contractor', foreign_keys='QuoteRecipient.contractor_id')
    sent_quote_invites = db.relationship('QuoteRecipient', backref='invited_by', foreign_keys='QuoteRecipient.invited_by_id')

    # 🧩 Platform Access
    pin = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔐 GDPR & Consent Fields
    consent_to_contact = db.Column(db.Boolean, default=False)
    data_sharing_opt_in = db.Column(db.Boolean, default=False)
    share_profile_with_directors = db.Column(db.Boolean, default=False)

    # 🏠 Occupancy Role Flags
    is_owner = db.Column(db.Boolean, default=False)
    is_resident = db.Column(db.Boolean, default=False)
    is_tenant = db.Column(db.Boolean, default=False)

    # 🤖 AI / GAR Profile Parsing
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)

    # ⚖️ GAR Governance & Trust Evaluation
    gar_risk_flags = db.Column(db.Text, nullable=True)
    gar_alignment_score = db.Column(db.Float, nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)

    # 🌐 Role-Based Smart Visibility
    role_visibility_scope = db.Column(db.String(100), default="Admin,Director")

    # 🧠 Phase 2 – AI Profile Completion / Recommendations
    ai_profile_completeness = db.Column(db.Float, nullable=True)
    ai_suggested_fields_to_add = db.Column(db.JSON, nullable=True)

    # 💬 GAR Chat Q&A Support
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # ✅ Helper
    @property
    def role_name(self):
        return self.role.name if self.role else "Unassigned"

    def __repr__(self):
        return f"<User {self.full_name} ({self.role_name})>"

