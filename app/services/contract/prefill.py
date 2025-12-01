from __future__ import annotations 
from typing import Dict, Any, Optional

# ✨ NEW: extra typing used by the UI sanitizer (kept separate so we don't remove anything above)
from typing import Mapping, MutableMapping

# --- Company model import (consistent with the rest of your app) ---
try:
    from app.models.onboarding.company import Company  # preferred path
except Exception:
    # Fallback if your model path differs locally
    from app.models.onboarding import Company  # type: ignore

# --- External blocks (bank/insurance/licenses) ---
# Keep your existing services; signatures here are inferred from your snippet.
from app.services.banking import build_bank_block
from app.services.insurance import build_insurance_block
from app.services.licenses import build_license_block

# Emergency contacts may not exist yet; degrade gracefully.
try:
    from app.services.emergency import build_emergency_block  # type: ignore
except Exception:
    def build_emergency_block(company_id: int) -> list[dict]:
        """Fallback: no emergency service yet."""
        return []

# ---------- helpers ----------
def _g(obj: Any, name: str, default: Any = None) -> Any:
    """Null-safe getattr."""
    return getattr(obj, name, default)

def _bool(value: Any) -> bool:
    return bool(value) and str(value).lower() not in {"false", "0", "none", "null"}

# ---------- public API ----------
def build_issuer_defaults_for_contract(
    company: Company,
    client_country: Optional[str] = None,
    client_region: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Issuer (the management/contractor org) defaults to stamp into a contract body.
    This is *not* the UI form prefill; it's the reusable issuer block.
    """
    # choose license country: client country wins, else company country
    license_country = client_country or _g(company, "country")

    issuer_brand = {
        "primary_color": _g(company, "theme_primary"),
        "secondary_color": _g(company, "theme_secondary"),
        "brand_color": _g(company, "brand_color"),
        "logo_url": _g(company, "logo_url") or _g(company, "logo_path"),
    }

    issuer_contact = {
        "email": _g(company, "email"),
        "phone": _g(company, "phone"),
        "website": _g(company, "website"),
    }

    issuer_address = {
        "line1": _g(company, "address_line1") or _g(company, "address"),
        "line2": _g(company, "address_line2"),
        "city": _g(company, "city"),
        "state": _g(company, "state"),
        "postal_code": _g(company, "postal_code"),
        "country": _g(company, "country"),
    }

    return {
        "issuer_name": _g(company, "legal_name") or _g(company, "name") or _g(company, "trading_name"),
        "issuer_registration_number": _g(company, "registration_number"),
        "issuer_vat_number": _g(company, "vat_number"),
        "issuer_tax_identifier": _g(company, "tax_identifier"),
        "issuer_type": _g(company, "company_type"),
        "issuer_industry": _g(company, "industry"),
        "issuer_contact": issuer_contact,
        "issuer_address": issuer_address,
        "issuer_brand": issuer_brand,
        "issuer_bank": build_bank_block(owner_type="company", owner_id=_g(company, "id")),
        "issuer_insurance": build_insurance_block(_g(company, "id")),             # list of active policies
        "issuer_emergency_contacts": build_emergency_block(_g(company, "id")),    # list (may be empty)
        "issuer_license": build_license_block(
            _g(company, "id"),
            license_country,
            client_region,
        ),
    }

def build_initial_contract_fields(company: Company) -> Dict[str, Any]:
    """
    Minimal, UI-facing prefill for a new Contract form.
    """
    contact_name  = _g(company, "contact_name")
    contact_email = _g(company, "contact_email")
    contact_phone = _g(company, "contact_phone")

    # Default PPM by business type (extend as needed)
    business_type = (_g(company, "business_type") or "").strip()
    ppm_default_map = {
        "Fire Alarm": "Quarterly",
        "Emergency Lighting": "Bi-Annual",
        "Lift": "Monthly",
    }
    ppm_default = ppm_default_map.get(business_type, "Monthly")

    legal_or_trade = _g(company, "legal_name") or _g(company, "trading_name") or _g(company, "name") or "Service Agreement"

    return {
        "contract_title": f"{legal_or_trade} — Property Management Agreement",
        "currency": _g(company, "currency") or "EUR",
        "ppm_schedule": ppm_default,
        "primary_contact_name": contact_name,
        "primary_contact_email": contact_email,
        "primary_contact_phone": contact_phone,
    }

def build_profile_snapshot(company: Company) -> Dict[str, Any]:
    """
    Immutable snapshot stored on Contract.profile_snapshot at creation.
    Keep this succinct and non-sensitive (no secrets).
    """
    return {
        "company": {
            "id": _g(company, "id"),
            "legal_name": _g(company, "legal_name"),
            "trading_name": _g(company, "trading_name"),
            "registration_number": _g(company, "registration_number"),
            "vat_number": _g(company, "vat_number"),
            "address": _g(company, "address") or _g(company, "address_line1"),
            "country": _g(company, "country"),
            "currency": _g(company, "currency") or "EUR",
            "business_type": _g(company, "business_type"),
            "branding": {
                "logo_url": _g(company, "logo_url") or _g(company, "logo_path"),
                "brand_color": _g(company, "brand_color") or _g(company, "theme_primary"),
            },
        },
        "contacts": {
            "primary": {
                "name": _g(company, "contact_name"),
                "email": _g(company, "contact_email"),
                "phone": _g(company, "contact_phone"),
            }
        }
    }

def build_ai_seed_context(company: Company) -> Dict[str, Any]:
    """
    Optional AI/GAR provenance context; attach to Contract.ai_context on create.
    """
    return {
        "source": "contract_prefill_v1",
        "company_id": _g(company, "id"),
        "company_business_type": _g(company, "business_type"),
        "defaults_applied": {
            "ppm_schedule": True,
            "currency": _bool(_g(company, "currency")),
            "branding": any([
                _g(company, "theme_primary"),
                _g(company, "theme_secondary"),
                _g(company, "brand_color"),
                _g(company, "logo_url"),
                _g(company, "logo_path"),
            ]),
        },
    }

def build_full_prefill_payload(
    company: Company,
    client_country: Optional[str] = None,
    client_region: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience method if you want *everything* at once:
    - issuer_* block (for clauses/templates)
    - initial contract UI fields
    - profile snapshot
    - AI seed context
    """
    return {
        "issuer_defaults": build_issuer_defaults_for_contract(company, client_country, client_region),
        "contract_fields": build_initial_contract_fields(company),
        "profile_snapshot": build_profile_snapshot(company),
        "ai_context": build_ai_seed_context(company),
    }

# ======================================================================
# 🔽 NEW: UI Sanitation helpers — ensure String/TextArea fields get strings
# ======================================================================

def _looks_like_address(d: Mapping[str, Any]) -> bool:
    keys = {k.lower() for k in d.keys()}
    return any(k in keys for k in (
        "line1","line_1","address1","address_1","street",
        "line2","line_2","address2","address_2",
        "city","town","county","state","region","province",
        "postal_code","postcode","zip","country",
    ))

def _address_to_str(d: Mapping[str, Any]) -> str:
    def take(*names):
        for n in names:
            if n in d and d[n]:
                return str(d[n])
        return ""
    parts = [
        take("line1","line_1","address1","address_1","street"),
        take("line2","line_2","address2","address_2"),
        take("city","town"),
        take("county","state","region","province"),
        take("postal_code","postcode","zip"),
        take("country"),
    ]
    return ", ".join([p for p in parts if p]).strip(", ")

def _coerce_by_fieldname(value: Any, field_name: str) -> str:
    """
    Heuristic coercion used for WTForms/String/TextArea defaults.
    Prevents dict/list reprs from showing in inputs.
    """
    if value is None or value == "null":
        return ""

    # primitives
    if isinstance(value, (int, float, str)):
        return str(value)

    # dicts
    if isinstance(value, Mapping):
        lname = (field_name or "").lower()

        # Addressy fields
        if "address" in lname or lname.endswith("_addr") or lname.endswith("_address"):
            if _looks_like_address(value):
                return _address_to_str(value)

        # Role
        if "role" in lname:
            for k in value.keys():
                if k.lower() == "role" and value[k]:
                    return str(value[k])

        # Name-ish fields
        if "name" in lname or lname in {"display_name","legal_name","trading_as","client_name","agent_name"}:
            for key in ("display_name","legal_name","name","issuer_name","client_name","agent_name","full_name","contact_name"):
                for k in value.keys():
                    if k.lower() == key and value[k]:
                        return str(value[k])

        # Contacts (best effort)
        if "contact" in lname:
            email = next((value[k] for k in value if k.lower() in {"email","e_mail"} and value[k]), None)
            phone = next((value[k] for k in value if k.lower() in {"phone","mobile","tel"} and value[k]), None)
            if email and phone:
                return f"{email} • {phone}"
            if email or phone:
                return str(email or phone)

        # Fallback obvious fields
        for key in ("name","title","label","id"):
            for k in value.keys():
                if k.lower() == key and value[k]:
                    return str(value[k])

        # Unwrap common nest like {"issuer": {...}}
        for wrap in ("issuer","agent","client","authorised_person","authorized_person"):
            if wrap in value and isinstance(value[wrap], Mapping):
                return _coerce_by_fieldname(value[wrap], field_name)

        return ""

    # lists/tuples
    if isinstance(value, (list, tuple)):
        flat = [_coerce_by_fieldname(v, field_name) for v in value]
        flat = [s for s in flat if s]
        return ", ".join(flat)

    # anything else
    try:
        return str(value)
    except Exception:
        return ""

def sanitize_contract_form_defaults(form_or_dict: Any) -> Any:
    """
    Mutates a WTForms form OR a dict-of-defaults in-place, coercing nested values
    into clean strings so your StringField/TextAreaField render nicely.

    Usage in route (step==2), AFTER populating form/defaults but BEFORE render:
        sanitize_contract_form_defaults(form)
        sanitize_contract_form_defaults(defaults_dict)
    """
    # WTForms (optional import; avoid hard dependency)
    try:
        from wtforms.form import Form as WTForm  # type: ignore
    except Exception:  # pragma: no cover
        WTForm = None  # type: ignore

    if WTForm is not None and isinstance(form_or_dict, WTForm):
        for name, field in getattr(form_or_dict, "_fields", {}).items():
            if not isinstance(field.data, (type(None), str, int, float)):
                field.data = _coerce_by_fieldname(field.data, name)
        return form_or_dict

    if isinstance(form_or_dict, MutableMapping):
        for k, v in list(form_or_dict.items()):
            if not isinstance(v, (type(None), str, int, float)):
                form_or_dict[k] = _coerce_by_fieldname(v, k)
        return form_or_dict

    return form_or_dict

# Convenience: produce a flat one-line address from the issuer_defaults block
def issuer_address_str(issuer_defaults: Dict[str, Any]) -> str:
    addr = issuer_defaults.get("issuer_address") if isinstance(issuer_defaults, dict) else None
    if isinstance(addr, Mapping) and _looks_like_address(addr):
        return _address_to_str(addr)
    return ""

# Convenience: produce a simple contact string from issuer_defaults
def issuer_contact_str(issuer_defaults: Dict[str, Any]) -> str:
    contact = issuer_defaults.get("issuer_contact") if isinstance(issuer_defaults, dict) else None
    if isinstance(contact, Mapping):
        email = contact.get("email") or ""
        phone = contact.get("phone") or ""
        if email and phone:
            return f"{email} • {phone}"
        return email or phone or ""
    return ""
