# app/routes/super_admin/contracts/contracts.py
from __future__ import annotations

import json
import re
from datetime import date, timedelta, datetime as _dt
from typing import Any, Dict, List

from flask import Blueprint, request, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.decorators import super_admin_required
from app.extensions import db
from app.models.client.client import Client
from app.models.contracts import ContractTemplate, ContractTemplateVersion, ClientContract
from app.services.contract.contracts import generate_contract_artifacts, contract_snapshot, log_contract_audit
from app.services.contract.contract_upgrades import build_upgrade_preview, apply_upgrade
from app.services.contract.contract_audits import create_contract_audit  # ✅ unified audit helper (kept)

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

    if "additional" not in payload["fees"]:
        try:
            extras_map = json.loads(contract.additional_fees) if contract.additional_fees else {}
        except Exception:
            extras_map = {}
        payload["fees"]["additional"] = [{"label": k, "amount": float(v or 0)} for k, v in extras_map.items()]

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

    step = int(request.args.get("step", 1))

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

    # STEP 2: schema-driven form (reads tv.form_schema)
    if step == 2:
        tv_id = int(request.args.get("tv_id") or 0)
        tv = ContractTemplateVersion.query.get_or_404(tv_id)

        # Load form_schema (or empty)
        try:
            schema = json.loads(tv.form_schema) if tv.form_schema else {"sections": []}
        except Exception:
            schema = {"sections": []}
        type_map = _schema_type_map(schema)

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

            # 2) Validate against schema rules first
            errors = _validate_against_schema(schema, data_json)
            if errors:
                # Re-render Step 2 with errors & sticky values
                return render_template(
                    "super_admin/contracts/renew_wizard.html",
                    step=2, client=client, tv=tv, schema=schema,
                    form_values=data_json, errors=errors
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
                return render_template(
                    "super_admin/contracts/renew_wizard.html",
                    step=2, client=client, tv=tv, schema=schema, form_values=data_json
                )

            # currency from schema (or client fallback)
            currency = (
                data_json.get("fees", {}).get("currency")
                or client.currency
                or "EUR"
            )

            # base fee from schema
            base_fee = data_json.get("fees", {}).get("base_ex_vat") or 0.0
            try:
                base_fee = float(base_fee)
            except Exception:
                base_fee = 0.0

            # 4) Create a DRAFT contract and store full data_json
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
            db.session.add(contract)
            db.session.commit()

            # ✅ (A) AUDIT: create draft (use snapshot-based logger)
            log_contract_audit(
                contract,
                action="create_draft",
                before=None,
                after=contract_snapshot(contract),
                notes="Draft contract created via renewal wizard",
            )
            db.session.commit()

            # 5) Generate artifacts and continue to Step 3 with stable id
            html_url, pdf_url = generate_contract_artifacts(client, contract)
            contract.generated_html_path = html_url
            contract.generated_pdf_path = pdf_url
            db.session.commit()

            return redirect(url_for(".renew", client_id=client.id, step=3, contract_id=contract.id))

        # GET — render from schema (empty defaults)
        return render_template(
            "super_admin/contracts/renew_wizard.html",
            step=2, client=client, tv=tv,
            schema=schema, form_values={}
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
        notes=f"Applied update; accepted_sections={accepted_sections}, archive_removed={archive_removed}",
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
