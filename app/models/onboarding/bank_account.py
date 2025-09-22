from __future__ import annotations

from datetime import datetime
from sqlalchemy import Index, Enum, text
from app.extensions import db

# SQLAlchemy Enum (the actual CREATE TYPE happens in your Alembic migration)
BankOwnerType = Enum(
    "company", "client", "omc", "contractor", name="bank_owner_type_enum"
)

class BankAccount(db.Model):
    __tablename__ = "bank_accounts"

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Generic owner (polymorphic)
    owner_type = db.Column(BankOwnerType, nullable=False, index=True, default="company")
    owner_id   = db.Column(db.Integer, nullable=False, index=True)

    # (Legacy/compat) Keep company_id for now; drop in a later migration once everything uses (owner_type, owner_id)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)

    # 💳 Account fields
    nickname         = db.Column(db.String(64))
    account_name     = db.Column(db.String(255))
    bank_name        = db.Column(db.String(255))
    iban             = db.Column(db.String(34))
    bic_swift        = db.Column(db.String(11))
    remittance_email = db.Column(db.String(255))

    currency       = db.Column(db.String(10))   # e.g., 'EUR', 'GBP'
    account_type   = db.Column(db.String(50))   # e.g., 'operating', 'client_money'
    active         = db.Column(db.Boolean, default=True, nullable=False)

    is_default     = db.Column(db.Boolean, default=False, nullable=False)

    # ⏱️ Timestamps (useful for audit/history)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Convenience backref (valid when owner_type='company'); avoids importing Company here
    company = db.relationship("Company", back_populates="bank_accounts", foreign_keys=[company_id])

    __table_args__ = (
        # Allow many accounts per owner, but at most one default (enforced via a partial unique index)
        Index(
            "uq_bank_accounts_one_default_per_owner",
            "owner_type", "owner_id",
            unique=True,
            postgresql_where=text("is_default = TRUE")
        ),
        # Fast lookups for an owner's accounts
        Index("ix_bank_accounts_owner", "owner_type", "owner_id"),
    )

    def __repr__(self):
        who = f"{self.owner_type}:{self.owner_id}"
        return f"<BankAccount {self.nickname or self.account_name} owner={who} default={self.is_default}>"

    # 🔒 Helper for safe display
    @property
    def masked_iban(self) -> str | None:
        """
        Return IBAN masked except last 4 chars, e.g., 'IE** **** **** **** **1234'.
        """
        if not self.iban:
            return None
        s = self.iban.replace(" ", "")
        if len(s) <= 4:
            return s
        return f"{s[:2]}** **** **** **** **{s[-4:]}"
