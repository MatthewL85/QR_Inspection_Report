from __future__ import annotations

from app.models.contractor.contractor import Contractor


CONTRACTOR_PORTAL_ROLES = {"Contractor", "Admin Contractor"}
PROPERTY_MANAGEMENT_COMPANY_TYPES = {
    "management",
    "management company",
    "property management",
    "property management company",
    "block management",
    "block management company",
    "estate management",
    "managing agent",
    "omc",
    "owners management company",
}


def role_name_for_user(user) -> str:
    role = getattr(user, "role", None)
    return getattr(role, "name", None) or getattr(user, "role_name", None) or ""


def normalise_company_type(value: str | None) -> str:
    return " ".join((value or "").strip().lower().replace("_", " ").replace("-", " ").split())


def is_property_management_company_type(value: str | None) -> bool:
    return normalise_company_type(value) in PROPERTY_MANAGEMENT_COMPANY_TYPES


def contractor_portal_denial_reason(user) -> str | None:
    if not user:
        return "missing_user"

    if role_name_for_user(user) not in CONTRACTOR_PORTAL_ROLES:
        return "not_contractor_role"

    company = getattr(user, "company", None)
    if is_property_management_company_type(getattr(company, "company_type", None)):
        return "property_management_company"

    contractor_id = getattr(user, "contractor_id", None)
    if not contractor_id:
        return "missing_contractor_profile"

    contractor = getattr(user, "contractor", None)
    if contractor is None:
        contractor = Contractor.query.get(contractor_id)
    if not contractor or not getattr(contractor, "is_active", True):
        return "inactive_contractor_profile"

    return None


def can_access_contractor_portal(user) -> bool:
    return contractor_portal_denial_reason(user) is None
