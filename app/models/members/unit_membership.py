# app/models/members/unit_membership.py

from datetime import datetime

from app.extensions import db


class UnitMembership(db.Model):
    """
    Enterprise join model between Unit and Member.

    - One row = one relationship between a specific Member and a specific Unit.
    - Works for owners, residents, directors, etc. via `role`.
    - Stores ownership and tenancy timelines so GAR can reason about history.
    """

    __tablename__ = "unit_memberships"

    id = db.Column(db.Integer, primary_key=True)

    # Foreign keys
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=False, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    # Role in relation to this unit
    # e.g. "owner", "resident", "landlord", "director", "guarantor"
    role = db.Column(db.String(32), nullable=False, default="owner", index=True)
    status = db.Column(db.String(32), nullable=False, default="active", index=True)
    access_start = db.Column(db.Date, nullable=True)
    access_end = db.Column(db.Date, nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)

    # ---- Ownership timeline (for owners / landlords) -----------------------
    ownership_start_date = db.Column(db.Date, nullable=True)  # purchase date
    ownership_end_date = db.Column(db.Date, nullable=True)    # sale date / transfer date

    # ---- Tenancy timeline (for residents / tenants) ------------------------
    tenancy_start_date = db.Column(db.Date, nullable=True)    # tenancy start
    tenancy_end_date = db.Column(db.Date, nullable=True)      # tenancy end / vacate

    # ---- Flags -------------------------------------------------------------
    is_primary = db.Column(db.Boolean, default=True)          # primary owner / main tenant
    is_current = db.Column(db.Boolean, default=True, index=True)

    # ---- Governance / notes / AI hooks ------------------------------------
    notes = db.Column(db.Text, nullable=True)

    gar_flags = db.Column(db.Text, nullable=True)             # JSON / text of risk flags
    gar_score = db.Column(db.Float, nullable=True)            # overall GAR score for this relationship
    gar_summary = db.Column(db.Text, nullable=True)           # AI summary of relationship history

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # ORM relationships (linked in Member and Unit in Step 1b)
    unit = db.relationship("Unit", back_populates="membership_links")
    member = db.relationship("Member", back_populates="unit_links")
    client = db.relationship("Client")
    user = db.relationship("User")

    # ------------------------------------------------------------------ #
    # Convenience helpers
    # ------------------------------------------------------------------ #
    @property
    def is_owner(self) -> bool:
        return self.role.lower() == "owner"

    @property
    def is_resident(self) -> bool:
        return self.role.lower() in ("resident", "tenant")

    @property
    def is_active_ownership(self) -> bool:
        return self.is_owner and self.ownership_end_date is None

    @property
    def is_active_tenancy(self) -> bool:
        return self.is_resident and self.tenancy_end_date is None

    def __repr__(self) -> str:
        return (
            f"<UnitMembership id={self.id} unit_id={self.unit_id} "
            f"member_id={self.member_id} role={self.role}>"
        )
