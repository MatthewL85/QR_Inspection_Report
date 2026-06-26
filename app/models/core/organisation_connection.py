from __future__ import annotations

from datetime import datetime, timedelta
from secrets import token_urlsafe

from app.extensions import db


def _connection_code() -> str:
    return token_urlsafe(18).replace("-", "").replace("_", "")[:24].upper()


class ModuleSubscription(db.Model):
    """Enabled Logix module for one organisation/company tenant."""

    __tablename__ = "module_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True)
    module_key = db.Column(db.String(80), nullable=False, index=True)
    status = db.Column(db.String(40), nullable=False, default="active", index=True)
    plan = db.Column(db.String(80), nullable=True)
    enabled_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    disabled_at = db.Column(db.DateTime, nullable=True)
    config_json = db.Column(db.JSON, nullable=True)
    source_module = db.Column(db.String(80), nullable=False, default="Core Platform")
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = db.relationship("Company", back_populates="module_subscriptions", foreign_keys=[company_id])
    created_by = db.relationship("User", foreign_keys=[created_by_user_id])

    __table_args__ = (
        db.UniqueConstraint("company_id", "module_key", name="uq_module_subscription_company_module"),
    )

    @property
    def is_active(self) -> bool:
        return self.status == "active" and not self.disabled_at

    def __repr__(self) -> str:
        return f"<ModuleSubscription company_id={self.company_id} module={self.module_key} status={self.status}>"


class OrganisationConnectionInvite(db.Model):
    """One-time auditable code used to connect two organisations."""

    __tablename__ = "organisation_connection_invites"

    id = db.Column(db.Integer, primary_key=True)
    invite_code = db.Column(db.String(32), nullable=False, unique=True, index=True, default=_connection_code)
    source_company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True)
    target_company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True, index=True)
    target_email = db.Column(db.String(255), nullable=True, index=True)
    connection_type = db.Column(db.String(80), nullable=False, default="management_contractor", index=True)
    status = db.Column(db.String(40), nullable=False, default="pending", index=True)
    allowed_modules_json = db.Column(db.JSON, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(days=30), index=True)
    accepted_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    accepted_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    source_company = db.relationship("Company", back_populates="sent_connection_invites", foreign_keys=[source_company_id])
    target_company = db.relationship("Company", back_populates="received_connection_invites", foreign_keys=[target_company_id])
    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
    accepted_by = db.relationship("User", foreign_keys=[accepted_by_user_id])

    @property
    def is_pending(self) -> bool:
        return self.status == "pending" and self.expires_at >= datetime.utcnow()

    def __repr__(self) -> str:
        return f"<OrganisationConnectionInvite source={self.source_company_id} status={self.status}>"


class OrganisationConnection(db.Model):
    """Approved relationship allowing modules to share governed records."""

    __tablename__ = "organisation_connections"

    id = db.Column(db.Integer, primary_key=True)
    source_company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True)
    target_company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True)
    connection_type = db.Column(db.String(80), nullable=False, default="management_contractor", index=True)
    status = db.Column(db.String(40), nullable=False, default="active", index=True)
    source_invite_id = db.Column(db.Integer, db.ForeignKey("organisation_connection_invites.id"), nullable=True, index=True)
    permissions_json = db.Column(db.JSON, nullable=True)
    gar_visibility_scope = db.Column(db.String(120), nullable=False, default="connected_records_only")
    accepted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    accepted_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    source_company = db.relationship("Company", back_populates="outgoing_organisation_connections", foreign_keys=[source_company_id])
    target_company = db.relationship("Company", back_populates="incoming_organisation_connections", foreign_keys=[target_company_id])
    source_invite = db.relationship("OrganisationConnectionInvite", foreign_keys=[source_invite_id])
    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
    accepted_by = db.relationship("User", foreign_keys=[accepted_by_user_id])

    __table_args__ = (
        db.UniqueConstraint(
            "source_company_id",
            "target_company_id",
            "connection_type",
            name="uq_organisation_connection_pair_type",
        ),
    )

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    def links_company(self, company_id: int) -> bool:
        return company_id in {self.source_company_id, self.target_company_id}

    def other_company_id(self, company_id: int) -> int | None:
        if company_id == self.source_company_id:
            return self.target_company_id
        if company_id == self.target_company_id:
            return self.source_company_id
        return None

    def __repr__(self) -> str:
        return (
            f"<OrganisationConnection {self.source_company_id}->{self.target_company_id} "
            f"type={self.connection_type} status={self.status}>"
        )
