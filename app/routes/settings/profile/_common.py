# app/routes/settings/profile/_common.py
from __future__ import annotations
from datetime import datetime

from flask import request
from flask_login import current_user
from app.extensions import db
from app.models.onboarding.company import Company


def attach_company_to_user(company: Company) -> None:
    """Link company <-> user if your schema supports it."""
    for fld in ("created_by_id", "owner_user_id", "user_id"):
        if hasattr(company, fld) and getattr(company, fld) in (None, 0):
            setattr(company, fld, getattr(current_user, "id", None))

    if hasattr(current_user, "company_id") and (getattr(current_user, "company_id", None) in (None, 0)):
        current_user.company_id = company.id


def resolve_company_for_settings() -> Company:
    """
    Load the company in a consistent order:
      1) ?id=<int>
      2) current_user.company_id
      3) last created by me (if created_by_id exists)
      4) create a new linked record
    """
    qid = request.args.get("id", type=int)
    if qid:
        obj = Company.query.get(qid)
        if obj:
            return obj

    if hasattr(current_user, "company_id") and current_user.company_id:
        obj = Company.query.get(current_user.company_id)
        if obj:
            return obj

    if hasattr(Company, "created_by_id"):
        obj = Company.query.filter_by(created_by_id=getattr(current_user, "id", None))\
                           .order_by(Company.id.desc()).first()
        if obj:
            return obj

    # Create a minimal company so the page is never empty
    obj = Company()
    if hasattr(obj, "name") and not obj.name:
        obj.name = "New Company"
    if hasattr(obj, "created_at"):
        obj.created_at = datetime.utcnow()
    db.session.add(obj)
    db.session.flush()
    attach_company_to_user(obj)
    db.session.commit()
    return obj


# The fields we map from the form (used in edit view)
PROFILE_FIELDS = (
    "name", "registration_number", "vat_number", "tax_identifier",
    "company_type", "industry",
    "email", "phone", "website",
    "address_line1", "address_line2", "city", "state", "postal_code", "country",
    "currency", "timezone", "preferred_language",
)
