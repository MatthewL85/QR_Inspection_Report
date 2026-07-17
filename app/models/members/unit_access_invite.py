# app/models/members/unit_access_invite.py

from datetime import datetime, timedelta

from app.extensions import db


class UnitAccessInvite(db.Model):
    """
    Controlled member-facing access code for linking one account to one unit.

    The Unit.unit_uid remains an internal permanent identifier. This invite is
    the short-lived, auditable workflow that members can safely use.
    """

    __tablename__ = "unit_access_invites"

    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True)

    claim_code = db.Column(db.String(32), nullable=False, unique=True, index=True)
    role = db.Column(db.String(32), nullable=False, default="owner", index=True)
    email = db.Column(db.String(255), nullable=True, index=True)
    status = db.Column(db.String(32), nullable=False, default="pending", index=True)
    expires_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(days=30))
    delivery_status = db.Column(db.String(32), nullable=False, default="not_sent", index=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    send_count = db.Column(db.Integer, nullable=False, default=0)
    last_delivery_error = db.Column(db.Text, nullable=True)

    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    claimed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    claimed_by_member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=True)
    claimed_at = db.Column(db.DateTime, nullable=True)

    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    unit = db.relationship("Unit")
    client = db.relationship("Client")
    company = db.relationship("Company")
    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
    claimed_by_user = db.relationship("User", foreign_keys=[claimed_by_user_id])
    claimed_by_member = db.relationship("Member")

    @property
    def is_pending(self) -> bool:
        return self.status == "pending" and self.expires_at >= datetime.utcnow()

    def __repr__(self) -> str:
        return f"<UnitAccessInvite unit_id={self.unit_id} role={self.role} status={self.status}>"
