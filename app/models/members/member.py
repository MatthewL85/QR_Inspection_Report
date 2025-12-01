# app/models/members/member.py

from app.extensions import db
from datetime import datetime

member_units = db.Table(
    "member_units",
    db.Column("member_id", db.Integer, db.ForeignKey("members.id"), primary_key=True),
    db.Column("unit_id", db.Integer, db.ForeignKey("units.id"), primary_key=True),
    db.Column("ownership_percentage", db.Float, nullable=True),
)


class Member(db.Model):
    """
    Legal owner / member of an Owners Management Company (OMC).

    This model underpins:
      - Members Logix (owner portal, communications, voting)
      - Director Logix (visibility of shareholders / members)
      - Finance Logix (owner vs unit responsibility)
      - GAR (governance risk & trust scoring)
    """
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core governance linkage
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)

    # One-to-one link to core User record (if they have a portal login)
    user = db.relationship("User", backref=db.backref("member_profile", uselist=False))

    # Identity / contact
    salutation = db.Column(db.String(50), nullable=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    alternate_phone = db.Column(db.String(50), nullable=True)

    # Postal / correspondence address
    postal_address_line1 = db.Column(db.String(255), nullable=True)
    postal_address_line2 = db.Column(db.String(255), nullable=True)
    postal_city = db.Column(db.String(100), nullable=True)
    postal_region = db.Column(db.String(100), nullable=True)
    postal_postcode = db.Column(db.String(20), nullable=True)
    postal_country = db.Column(db.String(100), nullable=True)

    # Roles / flags
    is_owner = db.Column(db.Boolean, default=True)
    is_director = db.Column(db.Boolean, default=False)
    is_company_representative = db.Column(db.Boolean, default=False)
    is_owner_occupier = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    # Communication & GDPR
    contact_consent = db.Column(db.Boolean, default=True)
    data_sharing_opt_in = db.Column(db.Boolean, default=False)
    share_profile_with_directors = db.Column(db.Boolean, default=False)
    preferred_contact_method = db.Column(db.String(50), nullable=True)  # email, phone, post, portal

    # External integration hooks
    external_reference = db.Column(db.String(100), nullable=True)       # legacy ID, CRM reference, etc.
    source_system = db.Column(db.String(50), nullable=True)
    is_external = db.Column(db.Boolean, default=False)

    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ---------------------------------
    # 🔁 Relationships
    # ---------------------------------
    # Legal ownership – many-to-many via member_units
    units = db.relationship(
        "Unit",
        secondary="member_units",
        back_populates="members",
        lazy="dynamic",
    )

    # AGM / governance approvals (defined in governance/voting models)
    approvals = db.relationship(
        "MemberApproval",
        back_populates="member",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # ---------------------------------
    # 🤖 AI / GAR Profile Intelligence
    # ---------------------------------
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default="pending")  # pending, completed, failed
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)  # Prevent re-parsing after manual review

    # ⚖️ GAR Trust & Governance Scoring
    gar_risk_flags = db.Column(db.Text, nullable=True)
    gar_alignment_score = db.Column(db.Float, nullable=True)
    gar_trust_score = db.Column(db.Float, nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🕒 Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Member id={self.id} user_id={self.user_id} client_id={self.client_id}>"