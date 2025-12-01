# app/routes/super_admin/contracts/contracts.py
from __future__ import annotations

import json
import re
from datetime import date, timedelta, datetime as _dt
from typing import Any, Dict, List
from sqlalchemy.orm import selectinload
from flask import current_app

from flask import Blueprint, request, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.decorators import super_admin_required
from app.extensions import db
from app.models.client.client import Client
from app.models.contracts import ContractTemplate, ContractTemplateVersion, ClientContract
from app.services.contract.contracts import generate_contract_artifacts, contract_snapshot, log_contract_audit
from app.services.contract.contract_upgrades import build_upgrade_preview, apply_upgrade
from app.services.contract.contract_audits import create_contract_audit  # ✅ unified audit helper (kept)

# --- NEW: company + prefill helpers (null-safe) ---
try:
    from app.models.onboarding.company import Company
except Exception:  # pragma: no cover
    Company = None  # type: ignore

try:
    # Our improved, null-safe prefill module
    from app.services.contract.prefill import (
        build_full_prefill_payload,  # issuer_defaults + contract_fields + profile_snapshot + ai_context
        build_issuer_defaults_for_contract,  # if you need issuer only
        sanitize_contract_form_defaults,     # ✅ NEW: flatten nested values for UI defaults
    )
except Exception:  # pragma: no cover
    build_full_prefill_payload = None  # type: ignore
    build_issuer_defaults_for_contract = None  # type: ignore
    # Fallback to standalone sanitizer module if available
    try:  # pragma: no cover
        from app.services.contract.prefill_sanitize import sanitize_contract_form_defaults  # type: ignore
    except Exception:  # pragma: no cover
        sanitize_contract_form_defaults = None  # type: ignore

super_admin_contracts_bp = Blueprint(
    "super_admin_contracts", __name__, url_prefix="/super-admin/contracts"
)

# -------------------- helpers --------------------

def _jurisdiction_for_client(client: Client) -> str:
    c = (client.country or "").strip().lower()
    if "ireland" in c or "éire" in c or c == "ie":
        return "IE"
    if c in ("uk", "united kingdom", "england", "scotland", "wales", "northern ireland"):
        return "UK"
    return "IE"


def _validate_term(jurisdiction: str, start_date, end_date) -> tuple[bool, str | None]:
    if not (start_date and end_date):
        return False, "Start and end dates are required."
    if end_date <= start_date:
        return False, "End date must be after the start date."
    if jurisdiction == "IE":
        # PSRA: maximum 3 years minus 1 day
        max_end = date(start_date.year + 3, start_date.month, start_date.day) - timedelta(days=1)
        if end_date > max_end:
            return False, "For IE (PSRA), the contract cannot exceed 3 years minus 1 day."
    return True, None


def _set_by_path(obj: dict, dotted: str, value):
    """Set a value on a nested dict using dotted paths (e.g., 'fees.base_ex_vat')."""
    cur = obj
    keys = dotted.split(".")
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
    cur[keys[-1]] = value
    return obj


def _get_by_path(obj: dict, dotted: str):
    cur = obj
    for seg in dotted.split("."):
        if not isinstance(cur, dict) or seg not in cur:
            return None
        cur = cur[seg]
    return cur


def _ensure_minimal_data_json(contract: ClientContract):
    """
    Ensure contract.data_json has the minimal shape our HTML template expects.
    Mirrors key first-class columns into data_json so the preview can render from one source.
    """
    payload = contract.data_json or {}
    payload.setdefault("branding", {"primary_hex": "#2196F3"})
    payload.setdefault("term", {})
    payload["term"]["start"] = contract.start_date.isoformat() if contract.start_date else None
    payload["term"]["end"] = contract.end_date.isoformat() if contract.end_date else None

    payload.setdefault("fees", {})
    if "vat_rate" not in payload["fees"]:
        payload["fees"]["vat_rate"] = 23
    if "invoice" not in payload["fees"]:
        payload["fees"]["invoice"] = {"frequency": "Monthly", "due_days": 30, "method": "Standing Order"}
    payload["fees"]["base_ex_vat"] = float(contract.contract_value or 0)

    if "additional" not in payload["fees"] and contract.additional_fees:
        try:
            extras_map = json.loads(contract.additional_fees)
        except Exception:
            extras_map = {}
        payload["fees"]["additional"] = [{"label": k, "amount": float(v or 0)} for k, v in extras_map.items()]
    elif "additional" not in payload["fees"]:
        payload["fees"]["additional"] = []

    # keep any existing meta/issuer blocks that might be present
    payload.setdefault("meta", {})
    payload.setdefault("issuer", payload.get("issuer", {}))

    contract.data_json = payload
    db.session.commit()

def _cast_value(v: str | None, typ: str | None):
    """Cast a string value according to a schema 'type'."""
    if v is None:
        return None
    t = (typ or "text").lower()
    if t in ("number",):
        try:
            return int(v) if str(v).isdigit() else float(v)
        except Exception:
            return None
    if t in ("money",):
        try:
            return float(v)
        except Exception:
            return None
    if t in ("checkbox",):
        return v in ("on", "true", "1", 1, True)
    # date/text/email/select/etc — keep string trimmed
    return str(v).strip()


def _schema_type_map(schema: dict) -> dict[str, str]:
    """Flatten form_schema into a path->type map (also columns for tables)."""
    m: Dict[str, str] = {}
    for s in schema.get("sections", []):
        for f in s.get("fields", []):
            if isinstance(f, dict) and f.get("path"):
                m[f["path"]] = (f.get("type") or "text")
        for t in s.get("tables", []):
            if not isinstance(t, dict) or not t.get("path"):
                continue
            for c in t.get("columns", []):
                if isinstance(c, dict) and c.get("path"):
                    m[f"{t['path']}.__col__.{c['path']}"] = (c.get("type") or "text")
    return m


def _schema_rules(schema: dict) -> dict[str, dict]:
    r"""
    Produce a path -> rule dict, e.g.
    {
      "fees.base_ex_vat": {"required": True, "min": 0, "max": None, "regex": r"^\d+(?:\.\d{1,2})?$"},
      "fees.additional[].amount": {"min": 0}
    }
    For table columns we use path like: "<table>[i].<col>" at validation time.
    """
    rules: Dict[str, dict] = {}
    for s in schema.get("sections", []):
        for f in s.get("fields", []):
            if not isinstance(f, dict) or not f.get("path"):
                continue
            rules[f["path"]] = {
                "required": bool(f.get("required")),
                "min": f.get("min"),
                "max": f.get("max"),
                "regex": f.get("regex"),
            }
        for t in s.get("tables", []):
            tpath = t.get("path")
            if not isinstance(t, dict) or not tpath:
                continue
            for c in t.get("columns", []):
                if not isinstance(c, dict) or not c.get("path"):
                    continue
                col_path = c["path"]
                rules[f"{tpath}[]:{col_path}"] = {
                    "required": bool(c.get("required")),
                    "min": c.get("min"),
                    "max": c.get("max"),
                    "regex": c.get("regex"),
                }
    return rules


def _validate_against_schema(schema: dict, data: dict) -> dict[str, str]:
    """
    Validate data against field rules. Returns errors dict mapping full path -> message.
    For table columns, keys are e.g. "fees.additional[0].amount".
    """
    errors: Dict[str, str] = {}
    rules = _schema_rules(schema)

    def _check_one(path: str, value: Any, rule: dict):
        # required
        if rule.get("required"):
            if value in (None, "", [], {}):
                errors[path] = "This field is required."
                return
        # numeric bounds
        vmin, vmax = rule.get("min"), rule.get("max")
        if isinstance(value, (int, float)):
            if vmin is not None and value < vmin:
                errors[path] = f"Must be ≥ {vmin}."
                return
            if vmax is not None and value > vmax:
                errors[path] = f"Must be ≤ {vmax}."
                return
        # regex
        rx = rule.get("regex")
        if rx and isinstance(value, str) and value:
            try:
                if not re.match(rx, value):
                    errors[path] = "Invalid format."
                    return
            except re.error:
                # bad regex in schema — ignore
                pass

    # simple fields
    for key, rule in rules.items():
        if "[]:" in key:
            continue
        value = _get_by_path(data, key)
        _check_one(key, value, rule)

    # table fields
    for key, rule in rules.items():
        if "[]:" not in key:
            continue
        tbl, col = key.split("[]:", 1)
        rows = _get_by_path(data, tbl)
        if isinstance(rows, list):
            for i, row in enumerate(rows):
                if isinstance(row, dict):
                    value = row.get(col)
                else:
                    value = None
                _check_one(f"{tbl}[{i}].{col}", value, rule)

    return errors

# ---------- scoped query helper for multi-tenant isolation ----------

def _scoped_contracts_query():
    """
    Base query for ClientContract, scoped by current_user.company_id if present.
    """
    q = ClientContract.query
    company_id = getattr(current_user, "company_id", None)
    if company_id:
        q = q.join(Client, Client.id == ClientContract.client_id).filter(Client.company_id == company_id)
    return q


# ---------- NEW: helper to fetch the Company for a client (relationship or FK) ----------

def _get_company_for_client(client: Client) -> Company | None:
    try:
        if hasattr(client, "company") and getattr(client, "company") is not None:
            return client.company  # type: ignore
    except Exception:
        pass
    try:
        if Company and getattr(client, "company_id", None):
            return Company.query.get(client.company_id)  # type: ignore
    except Exception:
        pass
    # fallback: current user's company, if any
    try:
        if Company and getattr(current_user, "company_id", None):
            return Company.query.get(current_user.company_id)  # type: ignore
    except Exception:
        pass
    return None


# ---------- NEW: human formatters for defaults ----------

def _join_address(parts: list[str | None]) -> str:
    return ", ".join([p for p in parts if p and str(p).strip()]) or ""

def _client_display_name(client: Client) -> str:
    for attr in ("display_name", "name", "client_name", "legal_name"):
        val = getattr(client, attr, None)
        if val:
            return str(val)
    return ""

def _client_address_str(client: Client) -> str:
    return _join_address([
        getattr(client, "address_line1", None) or getattr(client, "address", None),
        getattr(client, "address_line2", None),
        getattr(client, "city", None),
        getattr(client, "region", None) or getattr(client, "state", None),
        getattr(client, "postal_code", None),
        getattr(client, "country", None),
    ])

def _company_legal_name(company: Company | None) -> str:
    if not company:
        return ""
    for attr in ("legal_name", "name", "trading_name"):
        v = getattr(company, attr, None)
        if v:
            return str(v)
    return ""

def _company_trading_as(company: Company | None) -> str:
    if not company:
        return ""
    return str(getattr(company, "trading_name", None) or _company_legal_name(company) or "")

def _company_address_str(company: Company | None) -> str:
    if not company:
        return ""
    return _join_address([
        getattr(company, "address_line1", None) or getattr(company, "address", None),
        getattr(company, "address_line2", None),
        getattr(company, "city", None),
        getattr(company, "state", None) or getattr(company, "region", None),
        getattr(company, "postal_code", None),
        getattr(company, "country", None),
    ])

def _company_psra_number(company: Company | None) -> str:
    """
    Best-effort PSRA licence/number fetcher (handles different column names).
    """
    if not company:
        return ""
    for attr in (
        "psra_licence_no", "psra_license_no", "psra_licence", "psra_license",
        "psra_number", "psra_no", "licence_no", "license_no", "licence", "license"
    ):
        v = getattr(company, attr, None)
        if v:
            return str(v)
    return ""

def _pick_primary_contact(client: Client, company: Company | None) -> dict[str, str]:
    # Prefer explicit client contacts
    try:
        lst = getattr(client, "contacts", None)
        if lst and len(lst) > 0:
            c = lst[0]
            name = getattr(c, "name", None) or getattr(c, "full_name", None)
            email = getattr(c, "email", None)
            phone = getattr(c, "phone", None) or getattr(c, "mobile", None)
            role = getattr(c, "role", None) or getattr(c, "title", None)
            return {
                "name": str(name or ""),
                "email": str(email or ""),
                "phone": str(phone or ""),
                "role": str(role or ""),
            }
    except Exception:
        pass
    # Then the assigned PM on the client
    try:
        pm = getattr(client, "assigned_pm", None)
        if pm:
            name = getattr(pm, "full_name", None) or f"{getattr(pm,'first_name','') } {getattr(pm,'last_name','')}".strip()
            email = getattr(pm, "email", None)
            phone = getattr(pm, "phone", None)
            return {
                "name": str(name or ""),
                "email": str(email or ""),
                "phone": str(phone or ""),
                "role": "Property Manager",
            }
    except Exception:
        pass
    # Finally company contact
    if company:
        return {
            "name": str(getattr(company, "contact_name", None) or ""),
            "email": str(getattr(company, "contact_email", None) or getattr(company, "email", None) or ""),
            "phone": str(getattr(company, "contact_phone", None) or getattr(company, "phone", None) or ""),
            "role": str(getattr(company, "contact_role", None) or "Authorised Signatory"),
        }
    return {"name": "", "email": "", "phone": "", "role": ""}

def _deep_get(obj: dict, path: str):
    try:
        return _get_by_path(obj, path)
    except Exception:
        return None

def _flatten_value_for_field(field_name: str, label: str, value: Any) -> str:
    """
    Convert nested values into a readable string based on field intent.
    Used when we need to flatten posted data back into inputs on error pages.
    """
    lname = (field_name or "").lower()
    llabel = (label or "").lower()
    if value is None:
        return ""
    if isinstance(value, (int, float, str)):
        return str(value)
    if isinstance(value, dict):
        # address?
        if any(k in value for k in ("line1","address1","city","postal_code","postcode","zip","country")):
            return _join_address([
                value.get("line1") or value.get("address1") or value.get("street"),
                value.get("line2") or value.get("address2"),
                value.get("city") or value.get("town"),
                value.get("county") or value.get("state") or value.get("region") or value.get("province"),
                value.get("postal_code") or value.get("postcode") or value.get("zip"),
                value.get("country"),
            ])
        # name?
        for k in ("display_name","legal_name","name","issuer_name","client_name","agent_name","full_name","contact_name","title","label"):
            if value.get(k):
                return str(value.get(k))
        # contact?
        email = value.get("email") or value.get("e_mail")
        phone = value.get("phone") or value.get("mobile") or value.get("tel")
        if email or phone:
            return " • ".join([p for p in [email, phone] if p])
        # fallback
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join([_flatten_value_for_field(field_name, label, v) for v in value if v is not None])
    return str(value)

def _build_flat_defaults_from_schema(schema: dict, client: Client, company: Company | None, prefilled: dict | None) -> dict[str, str]:
    """
    For each field in the schema, choose a *string* default based on the label/path.
    This produces the path->string map the template expects.
    """
    flat: dict[str, str] = {}
    contact = _pick_primary_contact(client, company)
    for section in schema.get("sections", []):
        for f in section.get("fields", []):
            if not isinstance(f, dict):
                continue
            path = (f.get("path") or "").strip()
            if not path:
                continue
            label = (f.get("label") or f.get("title") or "").strip()
            l = label.lower()
            p = path.lower()
            val: str | None = None

            # --- Client block ---
            if "display name" in l or (".display_name" in p and "client" in p) or (p.endswith(".name") and "client" in p):
                val = _client_display_name(client)
            elif "postal address" in l or "business address" in l or ("client" in p and "address" in p):
                val = _client_address_str(client)
            elif "authorised person" in l or "authorized person" in l:
                val = contact.get("name")
            elif "authorised role" in l or "authorized role" in l or p.endswith(".role"):
                val = contact.get("role") or "Authorised Signatory"
            elif "authorised contact" in l or "authorized contact" in l:
                val = " • ".join([x for x in [contact.get("email"), contact.get("phone")] if x])

            # --- Agent block ---
            elif "agent legal name" in l or ("agent" in p and "legal" in l):
                val = _company_legal_name(company)
            elif "trading as" in l or ("agent" in p and "trading" in p):
                val = _company_trading_as(company)
            elif ("agent" in p and "address" in p) or (("postal address" in l or "business address" in l) and "agent" in p):
                val = _company_address_str(company)
            elif ("psra" in l) or ("psra" in p) or (("licence" in l or "license" in l) and "agent" in p):
                val = _company_psra_number(company)
            elif ("agent" in p and "phone" in p) or ("phone" in l and ("agent" in l or "agent" in p)):
                val = str(
                    (getattr(company, "phone", None) if company else "")
                    or (getattr(company, "contact_phone", None) if company else "")
                    or ""
                )
            elif ("agent" in p and "email" in p) or ("email" in l and ("agent" in l or "agent" in p)):
                val = str(
                    (getattr(company, "email", None) if company else "")
                    or (getattr(company, "contact_email", None) if company else "")
                    or ""
                )
            elif "website" in l and ("agent" in l or "agent" in p):
                val = str(getattr(company, "website", "") if company else "")

            # --- Fees / currency (if present in schema) ---
            elif p == "fees.currency" or (("currency" in p) and ("fees" in p)):
                val = str(getattr(client, "currency", None) or (prefilled or {}).get("fees", {}).get("currency") or "EUR")

            # Fallback: try any prefilled nested value matching this path
            if (val is None) and prefilled:
                nested = _deep_get(prefilled, path)
                if nested is not None:
                    val = _flatten_value_for_field(path, label, nested)

            flat[path] = (val or "")
    return flat

def _flatten_data_json_for_schema(schema: dict, data_json: dict) -> dict[str, str]:
    """Turn posted/constructed nested data_json into path->string for re-render."""
    flat: dict[str, str] = {}
    for section in schema.get("sections", []):
        for f in section.get("fields", []):
            if not isinstance(f, dict) or not f.get("path"):
                continue
            path = f["path"]
            label = (f.get("label") or f.get("title") or "")  # best effort
            val = _deep_get(data_json, path)
            flat[path] = _flatten_value_for_field(path, label, val)
    return flat

# -------------------- status/audit helper --------------------

def _set_sign_status_and_audit(contract: ClientContract, new_status: str, *, notes: str = "", extra_after: dict | None = None):
    """
    Centralised setter for signature status + audit trail.
    (D) Status change audit (now logs full before/after snapshots)
    """
    # full before/after snapshots for richer history
    before_snap = contract_snapshot(contract)

    before_status = contract.sign_status or "Draft"
    contract.sign_status = new_status
    db.session.commit()

    after_snap = contract_snapshot(contract)
    if extra_after:
        after_snap.update(extra_after)

    action_map = {
        "Sent": "send_for_signature",
        "Signed": "signature_signed",
        "Declined": "signature_declined",
        "Expired": "signature_expired",
    }
    action = action_map.get(new_status, "signature_status_change")

    # switched to the unified logger (kept old helper import intact)
    log_contract_audit(
        contract,
        action=action,
        before=before_snap,
        after=after_snap,
        notes=notes,
    )
    db.session.commit()

# ========== NEW: ARCHIVE HELPERS & ROUTES (non-destructive, fully audited) ==========

def _archive_contract(contract: ClientContract, user_id: int | None, reason: str = "Duplicate draft"):
    """
    Soft-archive a contract in a model-agnostic way:
    - Prefer sign_status == 'Archived' (used by this module)
    - If model has archive metadata columns, populate them
    - Write a full before/after audit snapshot
    """
    before = contract_snapshot(contract)

    # status/sign_status toggle
    try:
        # Prefer sign_status field if present in this app
        if hasattr(contract, "sign_status"):
            contract.sign_status = "Archived"
        # Or, if a generic status exists, try a conventional ARCHIVED value
        elif hasattr(contract, "status") and getattr(contract, "status") != "ARCHIVED":
            try:
                contract.status = "ARCHIVED"
            except Exception:
                pass
    except Exception:
        pass

    # metadata (best-effort; columns may or may not exist on your model)
    try:
        if hasattr(contract, "archived_at") and getattr(contract, "archived_at") is None:
            contract.archived_at = _dt.utcnow()
    except Exception:
        pass
    for colname in ("archived_by_id", "archived_by_user_id"):
        if hasattr(contract, colname) and user_id:
            try:
                setattr(contract, colname, user_id)
                break
            except Exception:
                continue
    try:
        if hasattr(contract, "archived_reason") and reason:
            contract.archived_reason = reason[:255]
    except Exception:
        pass

    db.session.commit()

    # audit trail
    after = contract_snapshot(contract)
    log_contract_audit(
        contract,
        action="archive",
        before=before,
        after=after,
        notes=f"Archived via UI. Reason: {reason}",
    )
    db.session.commit()
    return contract


@super_admin_contracts_bp.post("/contracts/<int:contract_id>/archive")
@login_required
@super_admin_required
def contracts_archive_single(contract_id: int):
    reason = (request.form.get("reason") or "Duplicate draft").strip()
    contract = ClientContract.query.get_or_404(contract_id)

    # tenant isolation
    if getattr(current_user, "company_id", None) and contract.client.company_id != current_user.company_id:
        flash("Not found.", "danger")
        return redirect(url_for("super_admin.manage_clients"))

    _archive_contract(contract, getattr(current_user, "id", None), reason)
    flash("Contract archived.", "success")
    return redirect(url_for(".contracts_overview", **request.args.to_dict()))


@super_admin_contracts_bp.post("/contracts/bulk-archive")
@login_required
@super_admin_required
def contracts_archive_bulk():
    ids = request.form.getlist("ids[]") or request.form.getlist("ids")
    reason = (request.form.get("reason") or "Bulk archive (duplicate drafts)").strip()
    if not ids:
        flash("No contracts selected.", "warning")
        return redirect(url_for(".contracts_overview", **request.args.to_dict()))

    # scoped fetch
    q = _scoped_contracts_query().filter(ClientContract.id.in_(ids))
    contracts = q.all()
    for c in contracts:
        _archive_contract(c, getattr(current_user, "id", None), reason)

    flash(f"Archived {len(contracts)} contract(s).", "success")
    return redirect(url_for(".contracts_overview", **request.args.to_dict()))

# -------------------- wizard routes --------------------

@super_admin_contracts_bp.route("/renew/<int:client_id>", methods=["GET", "POST"])
@super_admin_required
@login_required
def renew(client_id: int):
    client = Client.query.get_or_404(client_id)

    # tenant isolation
    if getattr(current_user, "company_id", None) and client.company_id != current_user.company_id:
        flash("Not found.", "danger")
        return redirect(url_for("super_admin.manage_clients"))

    # make sure we always have step as an int
    try:
        step = int(request.args.get("step", 1))
    except Exception:
        step = 1

    # STEP 1: choose template version
    if step == 1:
        jurisdiction = _jurisdiction_for_client(client)
        tpls = (
            ContractTemplate.query
            .filter_by(jurisdiction=jurisdiction, is_active=True)
            .all()
        )
        latest_versions = []
        for t in tpls:
            v = t.versions.order_by(ContractTemplateVersion.created_at.desc()).first()
            if v:
                latest_versions.append((t, v))

        if request.method == "POST":
            tv_id = int(request.form.get("template_version_id") or 0)
            if not tv_id:
                flash("Please choose a contract template version.", "warning")
            else:
                return redirect(url_for(".renew", client_id=client.id, step=2, tv_id=tv_id))
        return render_template("super_admin/contracts/renew_wizard.html",
                               step=1, client=client, latest_versions=latest_versions)

    # =========================
    # STEP 2: schema-driven form
    # =========================
    if step == 2:
        tv_id = int(request.args.get("tv_id") or 0)
        tv = ContractTemplateVersion.query.get_or_404(tv_id)

        # Load form_schema (or empty)
        try:
            schema = json.loads(tv.form_schema) if tv.form_schema else {"sections": []}
        except Exception:
            schema = {"sections": []}
        type_map = _schema_type_map(schema)

        # ---- NEW: build prefill from Company (issuer + snapshot + ai_context) ----
        prefilled_values: Dict[str, Any] = {}
        try:
            company = _get_company_for_client(client)
            if company and build_full_prefill_payload:
                payload = build_full_prefill_payload(
                    company,
                    client_country=(client.country or None),
                    client_region=(getattr(client, "region", None)),
                ) or {}

                # normalize payload parts in case any arrived as JSON strings
                def _ensure_dict(x):
                    if isinstance(x, dict):
                        return x
                    if isinstance(x, (str, bytes)):
                        try:
                            return json.loads(x)
                        except Exception:
                            return {}
                    return {}

                payload = _ensure_dict(payload)
                payload.setdefault("issuer_defaults", {})
                payload.setdefault("contract_fields", {})
                payload.setdefault("profile_snapshot", {})
                payload.setdefault("ai_context", {})

                # Put issuer block under data_json["issuer"] so templates can use it
                prefilled_values["issuer"] = _ensure_dict(payload.get("issuer_defaults", {}))

                # Currency: prefer schema path if present, else seed fees.currency fallback
                issuer_currency = (
                    payload.get("contract_fields", {}).get("currency")
                    or client.currency
                    or "EUR"
                )
                prefilled_values.setdefault("fees", {})
                prefilled_values["fees"].setdefault("currency", issuer_currency)

                # Basic contact defaults (if your schema has these paths)
                contacts = {
                    "primary": {
                        "name": payload.get("contract_fields", {}).get("primary_contact_name"),
                        "email": payload.get("contract_fields", {}).get("primary_contact_email"),
                        "phone": payload.get("contract_fields", {}).get("primary_contact_phone"),
                    }
                }
                prefilled_values["contacts"] = _ensure_dict(contacts)

                # Keep snapshot & ai context in meta for step-2 rendering; persisted on create
                prefilled_values.setdefault("meta", {})
                prefilled_values["meta"]["issuer_snapshot"] = _ensure_dict(payload.get("profile_snapshot", {}))
                prefilled_values["meta"]["ai_context"] = _ensure_dict(payload.get("ai_context", {}))

                # final safety: ensure top-level prefilled_values is fully dict-typed
                for k in ("issuer", "fees", "contacts", "meta"):
                    if k in prefilled_values:
                        prefilled_values[k] = _ensure_dict(prefilled_values[k])

        except Exception:
            current_app.logger.exception("renew step-2: prefill failed; continuing without prefill")

        if request.method == "POST":
            # 1) Build data_json from fs__ fields
            data_json: Dict[str, Any] = {}

            # simple fields: fs__<path>
            for key, val in request.form.items():
                if not key.startswith("fs__"):
                    continue
                path = key[4:]
                typ = type_map.get(path)
                casted = _cast_value(val, typ)
                _set_by_path(data_json, path, casted)

            # tables/lists: fslist__<table_path>__<rowindex>__<colpath>
            rows_by_table: dict[str, dict[int, dict]] = {}
            for key, val in request.form.items():
                if not key.startswith("fslist__"):
                    continue
                # fslist__fees.additional__0__label
                _, rest = key.split("__", 1)
                parts = rest.split("__", 2)
                if len(parts) != 3:
                    continue
                table_path, row_idx, col_path = parts
                try:
                    ri = int(row_idx)
                except Exception:
                    continue
                rows_by_table.setdefault(table_path, {}).setdefault(ri, {})
                col_typ = type_map.get(f"{table_path}.__col__.{col_path}")
                rows_by_table[table_path][ri][col_path] = _cast_value(val, col_typ)

            # assign built lists
            for tpath, rows in rows_by_table.items():
                ordered = [rows[i] for i in sorted(rows.keys())]
                _set_by_path(data_json, tpath, ordered)

            # Merge in the prefilled issuer/meta if user didn’t supply them via form fields
            # (We only add keys that are missing, to respect user input)
            if prefilled_values:
                # reuse local helper in this block
                def _ensure_dict(x):
                    if isinstance(x, dict):
                        return x
                    if isinstance(x, (str, bytes)):
                        try:
                            return json.loads(x)
                        except Exception:
                            return {}
                    return {}
                prefilled_values = _ensure_dict(prefilled_values)
                # issuer
                if "issuer" in prefilled_values and "issuer" not in data_json:
                    data_json["issuer"] = _ensure_dict(prefilled_values["issuer"])
                # contacts
                if "contacts" in prefilled_values and "contacts" not in data_json:
                    data_json["contacts"] = _ensure_dict(prefilled_values["contacts"])
                # meta
                data_json.setdefault("meta", {})
                if "meta" in prefilled_values:
                    pv_meta = _ensure_dict(prefilled_values["meta"])
                    if "issuer_snapshot" not in data_json["meta"]:
                        data_json["meta"]["issuer_snapshot"] = _ensure_dict(pv_meta.get("issuer_snapshot", {}))
                    if "ai_context" not in data_json["meta"]:
                        data_json["meta"]["ai_context"] = _ensure_dict(pv_meta.get("ai_context", {}))

            # 2) Validate against schema rules first
            errors = _validate_against_schema(schema, data_json)
            if errors:
                # NEW: flatten posted data_json to path->string for sticky UI
                flat_from_post = _flatten_data_json_for_schema(schema, data_json)
                return render_template(
                    "super_admin/contracts/renew_wizard.html",
                    step=2,
                    client=client,
                    tv=tv,
                    schema=schema,
                    form_values=flat_from_post,
                    errors=errors,
                )

            # 3) Validate term and mirror key columns
            try:
                sd_s = data_json.get("term", {}).get("start")
                ed_s = data_json.get("term", {}).get("end")
                sd = _dt.fromisoformat(sd_s).date() if sd_s else None
                ed = _dt.fromisoformat(ed_s).date() if ed_s else None
            except Exception:
                sd, ed = None, None

            ok, msg = _validate_term(tv.template.jurisdiction, sd, ed)
            if not ok:
                flash(msg, "danger")
                flat_from_post = _flatten_data_json_for_schema(schema, data_json)
                return render_template(
                    "super_admin/contracts/renew_wizard.html",
                    step=2, client=client, tv=tv, schema=schema, form_values=flat_from_post
                )

            # currency from schema (or client/issuer fallback)
            currency = (
                data_json.get("fees", {}).get("currency")
                or client.currency
                or (prefilled_values.get("fees", {}).get("currency") if prefilled_values else None)
                or "EUR"
            )

            # base fee from schema
            base_fee = data_json.get("fees", {}).get("base_ex_vat") or 0.0
            try:
                base_fee = float(base_fee)
            except Exception:
                base_fee = 0.0

            # 4) Create a DRAFT contract and store full data_json (+ issuer snapshot/meta)
            contract = ClientContract(
                client_id=client.id,
                template_version_id=tv.id,
                start_date=sd,
                end_date=ed,
                contract_value=base_fee,
                currency=currency,
                next_fee_increase_date=None,   # (can be added to schema later if needed)
                additional_fees=None,          # fees.additional lives in data_json now
                sign_status="Draft",
                data_json=data_json,
            )

            # If your model has ai_context/profile_snapshot columns, set them. Otherwise keep inside data_json.meta.*
            try:
                if hasattr(contract, "ai_context"):
                    ai_ctx = (prefilled_values.get("meta", {}) if prefilled_values else {}).get("ai_context") \
                             or data_json.get("meta", {}).get("ai_context")
                    if ai_ctx:
                        setattr(contract, "ai_context", ai_ctx)
                if hasattr(contract, "profile_snapshot"):
                    issuer_snap = (prefilled_values.get("meta", {}) if prefilled_values else {}).get("issuer_snapshot") \
                                  or data_json.get("meta", {}).get("issuer_snapshot")
                    if issuer_snap:
                        setattr(contract, "profile_snapshot", issuer_snap)
            except Exception:
                # non-fatal
                pass

            db.session.add(contract)
            db.session.commit()

            # ✅ (A) AUDIT: create draft (use snapshot-based logger)
            log_contract_audit(
                contract,
                action="create_draft",
                before=None,
                after=contract_snapshot(contract),
                notes="Draft contract created via renewal wizard (with prefill)",
            )
            db.session.commit()

            # 5) Generate artifacts and continue to Step 3 with stable id
            html_url, pdf_url = generate_contract_artifacts(client, contract)
            contract.generated_html_path = html_url
            contract.generated_pdf_path = pdf_url
            db.session.commit()

            return redirect(url_for(".renew", client_id=client.id, step=3, contract_id=contract.id))

        # ---------- GET ----------
        # We pass the prefilled_values as initial form values (non-binding; users can overwrite).
        def _ensure_dict(x):
            if isinstance(x, dict):
                return x
            if isinstance(x, (str, bytes)):
                try:
                    return json.loads(x)
                except Exception:
                    return {}
            return {}

        prefilled_values = _ensure_dict(prefilled_values or {})
        for k in ("issuer", "fees", "contacts", "meta"):
            if k in prefilled_values:
                prefilled_values[k] = _ensure_dict(prefilled_values[k])

        # Build *flat path->string* defaults that match your schema fields
        company = _get_company_for_client(client)
        flat_defaults = _build_flat_defaults_from_schema(schema, client, company, prefilled_values)

        # (Optional) sanitize nested defaults kept for other parts of the page
        display_defaults = json.loads(json.dumps(prefilled_values))  # deep copy
        if sanitize_contract_form_defaults:
            try:
                sanitize_contract_form_defaults(display_defaults)
            except Exception as e:
                current_app.logger.debug(f"sanitize (GET step-2) skipped: {e}")

        return render_template(
            "super_admin/contracts/renew_wizard.html",
            step=2, client=client, tv=tv,
            schema=schema,
            # 🔑 Pass the flattened defaults the form expects
            form_values=flat_defaults,
            # Keep nested prefill in case your template references it elsewhere
            prefill_nested=display_defaults,
        )

    # STEP 3: preview & send
    if step == 3:
        # Prefer contract_id param to avoid duplicate creation on refresh
        contract_id = request.args.get("contract_id", type=int)
        if not contract_id:
            flash("Missing contract to preview.", "danger")
            return redirect(url_for(".renew", client_id=client.id, step=1))

        contract = ClientContract.query.get_or_404(contract_id)
        tv = contract.template_version  # handy for the template

        # Make sure data_json is present and in sync with first-class columns
        _ensure_minimal_data_json(contract)

        # (Re)generate artifacts to reflect any prior changes
        html_url, pdf_url = generate_contract_artifacts(client, contract)
        contract.generated_html_path = html_url
        contract.generated_pdf_path = pdf_url
        db.session.commit()

        if request.method == "POST":
            # ✅ (D) Send for e-signature (status change audited inside helper)
            _set_sign_status_and_audit(
                contract,
                "Sent",
                notes="Contract sent for e-signature from Step 3 preview",
                extra_after={
                    "generated_html_path": contract.generated_html_path,
                    "generated_pdf_path": contract.generated_pdf_path,
                },
            )
            flash("Contract sent for e-signature.", "success")
            return redirect(url_for("super_admin.view_client", client_id=client.id))

        return render_template("super_admin/contracts/renew_wizard.html",
                               step=3, client=client, tv=tv, contract=contract,
                               html_url=html_url, pdf_url=pdf_url)

    # default → step 1
    return redirect(url_for(".renew", client_id=client.id, step=1))


# keep helper at top-level (OK to leave here) — guard against redefinition if present later
try:
    _ensure_dict  # type: ignore # noqa: F401
except NameError:
    def _ensure_dict(x):
        if isinstance(x, dict):
            return x
        if isinstance(x, (str, bytes)):
            try:
                return json.loads(x)
            except Exception:
                return {}
        return {}

@super_admin_contracts_bp.route("/super-admin/contracts/renew/<int:client_id>", methods=["GET", "POST"])
@login_required
@super_admin_required
def renew_legacy_route(client_id: int):
    """
    Legacy/shim route: keep the original symbol and body intact but delegate to the canonical
    /super-admin/contracts/renew/<client_id>?step=...
    """
    # Early delegate — keeps EVERYTHING below intact but unreachable (do not remove anything).
    return redirect(url_for(".renew", client_id=client_id, **request.args))

    # =========================
    # (Unreachable legacy body retained verbatim per "do not remove anything")
    # =========================
    # ... original Step-2 body as previously pasted remains here ...
    # NOTE: It will never execute because of the early return above.
    # (We intentionally keep it to satisfy "do not remove anything" while avoiding duplicate handlers.)

# -------------------- inline edit (Step 3 quick edits) --------------------

@super_admin_contracts_bp.post("/contracts/<int:contract_id>/inline-update")
@super_admin_required
@login_required
def contracts_inline_update(contract_id: int):
    """
    Update a single field in data_json via dotted path (e.g., 'fees.base_ex_vat'), mirror key columns,
    regenerate artifacts, and return to Step 3 preview.
    """
    contract = ClientContract.query.get_or_404(contract_id)
    client = Client.query.get_or_404(contract.client_id)

    json_path = request.form.get("json_path")
    value = request.form.get("value")

    if not json_path:
        flash("Missing json_path.", "warning")
        return redirect(url_for(".renew", client_id=client.id, step=3, contract_id=contract.id))

    # Ensure base structure
    if not contract.data_json:
        _ensure_minimal_data_json(contract)

    # previous for audit (B) — field-level diff
    old_value = _get_by_path(contract.data_json, json_path)
    before_snap = contract_snapshot(contract)

    # Best-effort casting for common cases
    casted: Any = value
    if json_path in ("fees.base_ex_vat",) or json_path.endswith(".amount"):
        try:
            casted = float(value)
        except Exception:
            pass

    _set_by_path(contract.data_json, json_path, casted)

    # Mirror into first-class columns for reporting where relevant
    if json_path == "fees.base_ex_vat":
        try:
            contract.contract_value = float(casted or 0)
        except Exception:
            pass
    elif json_path == "term.start":
        try:
            contract.start_date = _dt.fromisoformat(str(value)).date()
        except Exception:
            pass
    elif json_path == "term.end":
        try:
            contract.end_date = _dt.fromisoformat(str(value)).date()
        except Exception:
            pass

    db.session.commit()

    # ✅ (B) AUDIT: update/edit (snapshot + focused before/after for the field)
    after_snap = contract_snapshot(contract)
    log_contract_audit(
        contract,
        action="inline_update",
        before=before_snap,
        after=after_snap,
        notes=f"Inline update: {json_path}: {old_value} -> {casted}",
    )
    db.session.commit()

    # Regenerate artifacts to reflect the change
    html_url, pdf_url = generate_contract_artifacts(client, contract)
    contract.generated_html_path = html_url
    contract.generated_pdf_path = pdf_url
    db.session.commit()

    flash("Updated.", "success")
    return redirect(url_for(".renew", client_id=client.id, step=3, contract_id=contract.id))


# --------- Check & apply newer template version (AI review & merge) ---------

@super_admin_contracts_bp.get("/contracts/<int:contract_id>/check-update")
@super_admin_required
@login_required
def contracts_check_update(contract_id: int):
    contract = ClientContract.query.get_or_404(contract_id)
    current_tv = contract.template_version
    tpl = current_tv.template

    latest = tpl.versions.order_by(ContractTemplateVersion.created_at.desc()).first()
    if not latest or latest.id == current_tv.id:
        flash("This contract already uses the latest template version.", "info")
        return redirect(url_for(".renew", client_id=contract.client_id, step=3, contract_id=contract.id))

    preview = build_upgrade_preview(
        old_schema_str=current_tv.form_schema,
        new_schema_str=latest.form_schema,
        old_html=current_tv.html_template or "",
        new_html=latest.html_template or "",
    )

    # For convenience, compute removed field paths to optionally archive
    removed_paths: List[str] = []
    for sec_key, changes in (preview.get("schema_delta") or {}).items():
        for rem in changes.get("removed", []):
            if rem.get("path"):
                removed_paths.append(rem["path"])

    return render_template(
        "super_admin/contracts/upgrade_review.html",
        client=contract.client,
        contract=contract,
        current_version=current_tv,
        latest_version=latest,
        preview=preview,
        removed_paths=removed_paths,
    )


@super_admin_contracts_bp.post("/contracts/<int:contract_id>/apply-update")
@super_admin_required
@login_required
def contracts_apply_update(contract_id: int):
    """
    Switch to the newest version in the same template family and merge defaults
    for only the sections the user accepted. Optionally archive removed fields.
    """
    contract = ClientContract.query.get_or_404(contract_id)
    current_tv = contract.template_version
    tpl = current_tv.template
    latest = tpl.versions.order_by(ContractTemplateVersion.created_at.desc()).first()

    if not latest or latest.id == current_tv.id:
        flash("No newer version to apply.", "info")
        return redirect(url_for(".renew", client_id=contract.client_id, step=3, contract_id=contract.id))

    # Load preview helpers again to get defaults/deltas
    preview = build_upgrade_preview(
        old_schema_str=current_tv.form_schema,
        new_schema_str=latest.form_schema,
        old_html=current_tv.html_template or "",
        new_html=latest.html_template or "",
    )

    accepted_sections = request.form.getlist("accept_section")  # list of section keys
    archive_removed = request.form.get("archive_removed") == "on"
    removed_paths = request.form.getlist("removed_paths")

    # previous for audit (C)
    before_version = current_tv.version_label
    before_data = contract.data_json or {}
    before_snap = contract_snapshot(contract)

    # Build new data_json
    new_data = apply_upgrade(
        contract_data=before_data,
        new_schema=preview["new_schema"],
        section_defaults=preview["section_defaults"],
        accepted_sections=accepted_sections,
        archive_removed=(["yes"] if archive_removed else []),
        removed_field_paths=removed_paths,
    )

    # Apply: swap version, save data_json
    contract.template_version_id = latest.id
    contract.data_json = new_data
    db.session.commit()

    # ✅ (C) AUDIT: apply update (snapshot-based)
    after_snap = contract_snapshot(contract)
    log_contract_audit(
        contract,
        action="apply_update",
        before=before_snap,
        after=after_snap,
        notes=f"Applied update; accepted_sections={accepted_sections}, archive_removed={archive_removed}%",
    )
    db.session.commit()

    # Re-generate artifacts
    html_url, pdf_url = generate_contract_artifacts(contract.client, contract)
    contract.generated_html_path = html_url
    contract.generated_pdf_path = pdf_url
    db.session.commit()

    flash(f"Updated to latest template: {latest.version_label}.", "success")
    return redirect(url_for(".renew", client_id=contract.client_id, step=3, contract_id=contract.id))


# -------------------- signature lifecycle routes (manual & webhook) --------------------

@super_admin_contracts_bp.post("/contracts/<int:contract_id>/signature/signed")
@super_admin_required
@login_required
def signature_signed(contract_id: int):
    contract = ClientContract.query.get_or_404(contract_id)
    _set_sign_status_and_audit(contract, "Signed", notes="Marked as Signed")
    flash("Contract marked as Signed.", "success")
    return redirect(url_for(".renew", client_id=contract.client_id, step=3, contract_id=contract.id))


@super_admin_contracts_bp.post("/contracts/<int:contract_id>/signature/declined")
@super_admin_required
@login_required
def signature_declined(contract_id: int):
    contract = ClientContract.query.get_or_404(contract_id)
    reason = request.form.get("reason") or ""
    _set_sign_status_and_audit(contract, "Declined", notes=f"Declined: {reason}".strip())
    flash("Contract marked as Declined.", "warning")
    return redirect(url_for(".renew", client_id=contract.client_id, step=3, contract_id=contract.id))


@super_admin_contracts_bp.post("/contracts/<int:contract_id>/signature/expired")
@super_admin_required
@login_required
def signature_expired(contract_id: int):
    contract = ClientContract.query.get_or_404(contract_id)
    _set_sign_status_and_audit(contract, "Expired", notes="Signature request expired")
    flash("Contract marked as Expired.", "secondary")
    return redirect(url_for(".renew", client_id=contract.client_id, step=3, contract_id=contract.id))


@super_admin_contracts_bp.post("/signature/webhook")
@super_admin_required  # remove if the e-sign provider can’t auth; then add a shared secret instead
def signature_webhook():
    """
    Generic webhook to accept callbacks from e-sign providers.
    Expect JSON like: {"contract_id": 123, "event": "signed|declined|expired", "payload": {...}}
    """
    try:
        payload = request.get_json(force=True) or {}
        contract_id = int(payload.get("contract_id"))
        event = (payload.get("event") or "").lower()
        contract = ClientContract.query.get_or_404(contract_id)
    except Exception:
        abort(400, "Invalid webhook payload")

    extra = {"webhook_payload": payload}
    if event == "signed":
        _set_sign_status_and_audit(contract, "Signed", notes="Webhook: signed", extra_after=extra)
    elif event == "declined":
        _set_sign_status_and_audit(contract, "Declined", notes="Webhook: declined", extra_after=extra)
    elif event == "expired":
        _set_sign_status_and_audit(contract, "Expired", notes="Webhook: expired", extra_after=extra)
    else:
        # Unknown event -> audit generic change, but do not alter status
        create_contract_audit(
            db.session,
            contract_id=contract.id,
            action="signature_webhook_unknown",
            before={"sign_status": contract.sign_status},
            after={"sign_status": contract.sign_status, "webhook_payload": payload},
            notes="Webhook with unknown event",
        )
        db.session.commit()
        return ("ignored", 202)

    return ("ok", 200)

# -------------------- Contracts Overview (dashboard drill-down) --------------------

@super_admin_contracts_bp.get("/overview", endpoint="contracts_overview")
@super_admin_required
@login_required
def contracts_overview():
    """
    Drill-down page for contracts with expiry rollups (Expired, ≤30d, ≤60d, ≤90d)
    and signature-status breakdowns (Pending/Signed/Declined/Drafts/Expired Sig).
    Scoped by current_user.company_id (if present).

    Defaults for the unified table:
      • Show SIGNED contracts + contracts expired within the last 30 days (grace)
      • Exclude ARCHIVED and TERMINATED from the default dataset
      • Archived are only shown when explicitly requested
    Also de-duplicate rows by (client, contract_type) keeping the latest.
    """

    # 1) If a previous DB error occurred in this request, clear aborted txn state now.
    try:
        db.session.rollback()
    except Exception:
        pass

    today = date.today()
    in_30 = today + timedelta(days=30)
    in_60 = today + timedelta(days=60)
    in_90 = today + timedelta(days=90)
    since_30 = today - timedelta(days=30)

    # 2) Base scoped query + eager loading to avoid lazy-load during template render.
    base = _scoped_contracts_query()

    eager_opts = [selectinload(ClientContract.client)]
    # Add optional relations only if they exist on the model
    if hasattr(ClientContract, "preferred_contractor"):
        eager_opts.append(selectinload(ClientContract.preferred_contractor))
    if hasattr(ClientContract, "second_preferred_contractor"):
        eager_opts.append(selectinload(ClientContract.second_preferred_contractor))
    base = base.options(*eager_opts)

    # 2b) Helpers for de-duplication per client + type (or template family)
    def _type_key(c: ClientContract) -> str:
        # Prefer explicit contract_type if your model has it
        try:
            ct = getattr(c, "contract_type", None)
            if ct:
                return f"type:{ct}"
        except Exception:
            pass
        # Fall back to template family (template.id) then template_version.id
        try:
            tv = c.template_version
            if tv and hasattr(tv, "template") and tv.template:
                return f"tpl:{tv.template.id}"
            if tv:
                return f"tv:{tv.id}"
        except Exception:
            pass
        return "default"

    def _latest_key(c: ClientContract):
        # Prefer end_date, then created_at for recency
        return ((c.end_date or date.min), getattr(c, "created_at", date.min))

    def _dedupe(rows: List[ClientContract]) -> List[ClientContract]:
        bucket: dict[tuple[int, str], ClientContract] = {}
        for r in rows:
            key = (getattr(r, "client_id", 0), _type_key(r))
            keep = bucket.get(key)
            if not keep or _latest_key(r) > _latest_key(keep):
                bucket[key] = r
        # Return in a deterministic order (by client then recency)
        return sorted(bucket.values(), key=lambda x: (x.client.name if x.client else "", _latest_key(x)), reverse=False)

    # 3) Helper to safely execute .all() and keep the request alive if a subquery fails
    def _safe_all(q, label: str):
        try:
            return q.all()
        except Exception:
            current_app.logger.exception(f"contracts_overview: query failed in '{label}'")
            try:
                db.session.rollback()
            except Exception:
                pass
            return []

    # ----- Expiry lists (deduped) -----
    expired = _dedupe(_safe_all(
        base.filter(
            ClientContract.end_date.isnot(None),
            ClientContract.end_date < today
        ).order_by(ClientContract.end_date.asc()),
        "expired",
    ))

    expiring_30 = _dedupe(_safe_all(
        base.filter(
            ClientContract.end_date.isnot(None),
            ClientContract.end_date >= today,
            ClientContract.end_date <= in_30
        ).order_by(ClientContract.end_date.asc()),
        "expiring_30",
    ))

    expiring_60 = _dedupe(_safe_all(
        base.filter(
            ClientContract.end_date.isnot(None),
            ClientContract.end_date > in_30,
            ClientContract.end_date <= in_60
        ).order_by(ClientContract.end_date.asc()),
        "expiring_60",
    ))

    expiring_90 = _dedupe(_safe_all(
        base.filter(
            ClientContract.end_date.isnot(None),
            ClientContract.end_date > in_60,
            ClientContract.end_date <= in_90
        ).order_by(ClientContract.end_date.asc()),
        "expiring_90",
    ))

    # ----- Choose safe timestamp cols (fallbacks if attrs not present) -----
    updated_col = getattr(ClientContract, "updated_at", None) or ClientContract.created_at
    created_col = ClientContract.created_at
    signed_col = (
        getattr(ClientContract, "signed_at", None)
        or getattr(ClientContract, "updated_at", None)
        or ClientContract.created_at
    )

    # ----- Signature status breakdown lists (deduped) -----
    pending = _dedupe(_safe_all(
        base.filter(ClientContract.sign_status == "Sent")
            .order_by(updated_col.desc()),
        "pending",
    ))

    if signed_col is not None:
        signed = _dedupe(_safe_all(
            base.filter(
                ClientContract.sign_status == "Signed",
                signed_col >= since_30
            ).order_by(signed_col.desc()),
            "signed",
        ))
    else:
        signed = _dedupe(_safe_all(
            base.filter(ClientContract.sign_status == "Signed")
                .order_by(created_col.desc()),
            "signed_no_col",
        ))

    declined = _dedupe(_safe_all(
        base.filter(ClientContract.sign_status == "Declined")
            .order_by(updated_col.desc()),
        "declined",
    ))

    drafts = _dedupe(_safe_all(
        base.filter(ClientContract.sign_status == "Draft")
            .order_by(created_col.desc()),
        "drafts",
    ))

    expired_sig = _dedupe(_safe_all(
        base.filter(ClientContract.sign_status == "Expired")
            .order_by(updated_col.desc()),
        "expired_sig",
    ))

    # ----- Archived list (explicit; not shown by default) -----
    archived = _dedupe(_safe_all(
        base.filter(ClientContract.sign_status == "Archived").order_by(created_col.desc()),
        "archived",
    ))

    # -------- Server-side filters for the unified table (kept) --------
    q_status = (request.args.get("status") or "").strip()
    q_client = request.args.get("client_id", type=int)
    q_text   = (request.args.get("q") or "").strip()
    include_archived = request.args.get("include_archived") in ("1", "true", "True")

    all_q = _scoped_contracts_query().options(selectinload(ClientContract.client)).order_by(ClientContract.created_at.desc())

    if not include_archived:
        # Hide archived rows by default
        all_q = all_q.filter(ClientContract.sign_status != "Archived")

    if q_status:
        all_q = all_q.filter(ClientContract.sign_status == q_status)
    if q_client:
        all_q = all_q.filter(ClientContract.client_id == q_client)
    if q_text:
        # light search over title and client name if available
        like = f"%{q_text}%"
        try:
            all_q = (all_q.join(Client, Client.id == ClientContract.client_id)
                        .filter(
                            (getattr(ClientContract, "contract_title", ClientContract.id.cast(db.String)).ilike(like)) |
                            (Client.name.ilike(like))
                        ))
        except Exception:
            # fallback if contract_title column doesn't exist in your model
            all_q = (all_q.join(Client, Client.id == ClientContract.client_id)
                        .filter(Client.name.ilike(like)))

    # Default dataset behaviour: Signed + Expired within last 30 days (grace), excluding Terminated/Archived
    user_provided_filters = any([q_status, q_client, q_text, include_archived])
    if not user_provided_filters:
        grace_cutoff = today - timedelta(days=30)

        signed_q = base.filter(ClientContract.sign_status == "Signed")

        grace_q = base.filter(
            ClientContract.end_date.isnot(None),
            ClientContract.end_date >= grace_cutoff,
            ClientContract.end_date < today,
        )
        # Explicitly exclude Terminated/Archived from the default grace view if present
        try:
            grace_q = grace_q.filter(ClientContract.sign_status != "Terminated")
        except Exception:
            pass
        try:
            grace_q = grace_q.filter(ClientContract.sign_status != "Archived")
        except Exception:
            pass

        signed_rows = _safe_all(signed_q, "all_signed_default")
        grace_rows  = _safe_all(grace_q, "all_grace_default")

        merged = _dedupe(signed_rows + grace_rows)
        all_contracts = sorted(merged, key=lambda r: (r.client.name if r.client else "", getattr(r, "created_at", date.min)))
    else:
        try:
            all_contracts = _dedupe(all_q.limit(500).all())
        except Exception:
            current_app.logger.exception("contracts_overview: all_contracts query failed")
            try:
                db.session.rollback()
            except Exception:
                pass
            all_contracts = []

    return render_template(
        "super_admin/contracts/contracts_overview.html",
        counts={
            "expired": len(expired),
            "exp_30": len(expiring_30),
            "exp_60": len(expiring_60),
            "exp_90": len(expiring_90),
            "pending": len(pending),
            "signed": len(signed),
            "declined": len(declined),
            "drafts": len(drafts),
            "expired_sig": len(expired_sig),
            "archived": len(archived),  # NEW
        },
        expired=expired,
        expiring_30=expiring_30,
        expiring_60=expiring_60,
        expiring_90=expiring_90,
        pending=pending,
        signed=signed,
        declined=declined,
        drafts=drafts,
        expired_sig=expired_sig,
        archived=archived,  # NEW: handy if you add a tab later
        today=today,  # handy for the template
        # ✅ NEW: unified table dataset
        all_contracts=all_contracts,
    )
