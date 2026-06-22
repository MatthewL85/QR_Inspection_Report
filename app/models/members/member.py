# app/models/members/member.py

from app.extensions import db
from datetime import datetime

# ------------------------------------------------------------
# 🔗 Association Table (Ownership + Tenancy Metadata)
# ------------------------------------------------------------
member_units = db.Table(
    "member_units",
    db.Column("member_id", db.Integer, db.ForeignKey("members.id"), primary_key=True),
    db.Column("unit_id", db.Integer, db.ForeignKey("units.id"), primary_key=True),

    # Ownership metadata
    db.Column("ownership_percentage", db.Float, nullable=True),
    db.Column("ownership_type", db.String(50), nullable=True),  # individual, joint, corporate, receiver
    db.Column("purchase_date", db.Date, nullable=True),
    db.Column("sale_date", db.Date, nullable=True),

    # Tenancy metadata
    db.Column("tenancy_start_date", db.Date, nullable=True),
    db.Column("tenancy_end_date", db.Date, nullable=True),
    db.Column("tenancy_status", db.String(50), nullable=True),  # active, notice, ended

    # Future-proofing hooks
    db.Column("is_primary_residence", db.Boolean, default=False),
    db.Column("is_landlord", db.Boolean, default=False),
)


# ------------------------------------------------------------
# MEMBER MODEL
# ------------------------------------------------------------
class Member(db.Model):
    """
    Legal owner / member of an OMC, with GAR-ready intelligence,
    tenancy/ownership lifecycle, governance role flags,
    and deep integration with Members Logix & Director Logix.
    """

    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)

    # ---------------------------------
    # 🔗 Governance / Company Linkage
    # ---------------------------------
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)

    user = db.relationship("User", backref=db.backref("member_profile", uselist=False, overlaps="memberships"))

    # ---------------------------------
    # Identity / Contact
    # ---------------------------------
    salutation = db.Column(db.String(50), nullable=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    alternate_phone = db.Column(db.String(50), nullable=True)

    # Postal Address
    postal_address_line1 = db.Column(db.String(255))
    postal_address_line2 = db.Column(db.String(255))
    postal_city = db.Column(db.String(100))
    postal_region = db.Column(db.String(100))
    postal_postcode = db.Column(db.String(20))
    postal_country = db.Column(db.String(100))

    # ---------------------------------
    # Flags / Roles
    # ---------------------------------
    is_owner = db.Column(db.Boolean, default=True)
    is_director = db.Column(db.Boolean, default=False)
    is_company_representative = db.Column(db.Boolean, default=False)
    is_owner_occupier = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    # Communication & GDPR
    contact_consent = db.Column(db.Boolean, default=True)
    data_sharing_opt_in = db.Column(db.Boolean, default=False)
    share_profile_with_directors = db.Column(db.Boolean, default=False)
    preferred_contact_method = db.Column(db.String(50))  # email, phone, post, portal

    # External Integration
    external_reference = db.Column(db.String(100))
    source_system = db.Column(db.String(50))
    is_external = db.Column(db.Boolean, default=False)

    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ---------------------------------
    # 🔁 Multi-Unit Relationship
    # ---------------------------------
    units = db.relationship(
        "Unit",
        secondary="member_units",
        back_populates="members",
        lazy="dynamic",
    )

    approvals = db.relationship(
        "MemberApproval",
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    unit_links = db.relationship(
        "UnitMembership",
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # ---------------------------------
    # 🤖 AI / GAR Intelligence
    # ---------------------------------
    parsed_summary = db.Column(db.Text)
    extracted_data = db.Column(db.JSON)  # structured field for leases, IDs, docs
    parsing_status = db.Column(db.String(50), default="pending")
    parsed_at = db.Column(db.DateTime)
    parsed_by_ai_version = db.Column(db.String(50))
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)

    gar_risk_flags = db.Column(db.Text)
    gar_alignment_score = db.Column(db.Float)
    gar_trust_score = db.Column(db.Float)
    gar_recommendation = db.Column(db.String(255))
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text)

    # ---------------------------------
    # 🕒 Audit
    # ---------------------------------
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ---------------------------------
    # Debug
    # ---------------------------------
    @property
    def full_name(self):
        parts = [self.first_name, self.last_name]
        name = " ".join(part for part in parts if part).strip()
        return name or self.email or f"Member #{self.id}"

    @property
    def correspondence_address(self):
        parts = [
            self.postal_address_line1,
            self.postal_address_line2,
            self.postal_city,
            self.postal_region,
            self.postal_postcode,
            self.postal_country,
        ]
        return ", ".join(part for part in parts if part)

    @property
    def country(self):
        return self.correspondence_address or self.postal_country

    def __repr__(self):
        return f"<Member {self.first_name} {self.last_name} id={self.id}>"
