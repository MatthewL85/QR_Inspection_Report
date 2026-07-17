from __future__ import annotations

from datetime import datetime, time

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.decorators import super_admin_required
from app.models.client.client import Client
from app.models.core.user import User
from app.models.contracts import ClientContract, ContractTemplateVersion
from app.forms.contracts.contract_form import ContractForm

# prefill helpers (null-safe)
try:
    from app.models.onboarding.company import Company
except Exception:
    Company = None  # type: ignore

try:
    from app.services.contract.prefill import build_full_prefill_payload
except Exception:
    build_full_prefill_payload = None  # type: ignore

simple_contracts_bp = Blueprint(
    "super_admin_simple_contracts",
    __name__,
    url_prefix="/super-admin/contracts",
)

# ---------- helpers ----------
def _get_company_for_client(client: Client):
    try:
        if hasattr(client, "company") and client.company:
            return client.company
    except Exception:
        pass
    try:
        if Company and getattr(client, "company_id", None):
            return Company.query.get(client.company_id)  # type: ignore
    except Exception:
        pass
    return None

def _tenant_guard(client: Client) -> bool:
    """Return True if the current user is allowed to access this client's data."""
    cid = getattr(current_user, "company_id", None)
    return (cid is None) or (client.company_id == cid)

def _date_to_datetime(value):
    return datetime.combine(value, time.min) if value else None

def _set_common_choices(form: ContractForm) -> None:
    """Populate client and renewal alert owner choices in the current tenant scope."""
    q = Client.query
    cid = getattr(current_user, "company_id", None)
    if cid:
        q = q.filter(Client.company_id == cid)
    pairs = [(c.id, c.name) for c in q.order_by(Client.name.asc()).all()]
    form.set_client_choices(pairs)

    users_q = User.query
    if cid:
        users_q = users_q.filter(User.company_id == cid)
    user_pairs = [(u.id, u.full_name or u.email) for u in users_q.order_by(User.full_name.asc()).all()]
    form.set_alert_owner_choices(user_pairs)

# ---------- routes ----------
@simple_contracts_bp.route("/new", methods=["GET", "POST"])
@super_admin_required
@login_required
def new_contract():
    """Classic quick-create (non-wizard) draft contract."""
    form = ContractForm()
    _set_common_choices(form)

    # Optional prefill from issuer/company
    if request.method == "GET":
        # If a client is preselected via ?client_id=, we can prefill from their company
        preselect_id = request.args.get("client_id", type=int)
        if preselect_id:
            form.client_id.data = preselect_id
            client = Client.query.get(preselect_id)
            if client and _tenant_guard(client):
                company = _get_company_for_client(client)
                if company and build_full_prefill_payload:
                    payload = build_full_prefill_payload(company, client_country=client.country, client_region=getattr(client, "region", None))
                    form.apply_prefill_payload(payload)

    if request.method == "POST" and form.validate_on_submit():
        data = form.to_dict()

        client = Client.query.get_or_404(data["client_id"])
        if not _tenant_guard(client):
            flash("Not found.", "danger")
            return redirect(url_for("super_admin.manage_clients"))

        template_version_id = data.get("template_version_id")
        if not template_version_id:
            fallback_template_version = ContractTemplateVersion.query.order_by(ContractTemplateVersion.id.asc()).first()
            if not fallback_template_version:
                flash("Create a contract template version before starting a contract.", "warning")
                return redirect(url_for("super_admin_contracts.contracts_overview"))
            template_version_id = fallback_template_version.id

        contract = ClientContract(
            client_id=client.id,
            template_version_id=template_version_id,
            start_date=data["start_date"],
            end_date=data["end_date"],
            currency=data["currency"],
            contract_value=data["contract_value"],
            target_management_fee=data.get("target_management_fee"),
            annual_increase_percent=data.get("annual_increase_percent"),
            renewal_month=data.get("renewal_month"),
            next_fee_increase_date=data.get("next_fee_increase_date"),
            new_contract_drafted=data.get("new_contract_drafted") or False,
            renewal_notes=data.get("renewal_notes"),
            alert_owner_id=data.get("alert_owner_id"),
            last_reviewed_at=_date_to_datetime(data.get("last_reviewed_at")),
            gar_contract_risk_level=data.get("gar_contract_risk_level"),
            gar_contract_recommendation=data.get("gar_contract_recommendation"),
            sign_status="Draft",
            # Seed a minimal data_json; your wizard uses richer schema JSON elsewhere.
            data_json={
                "meta": {
                    "contract_title": data["contract_title"],
                },
                "term": {
                    "start": data["start_date"].isoformat() if data["start_date"] else None,
                    "end": data["end_date"].isoformat() if data["end_date"] else None,
                },
                "fees": {
                    "currency": data["currency"],
                    "base_ex_vat": float(data["contract_value"] or 0),
                    "target_management_fee": float(data["target_management_fee"] or 0) if data.get("target_management_fee") else None,
                    "annual_increase_percent": float(data["annual_increase_percent"] or 0) if data.get("annual_increase_percent") else None,
                    "ppm_schedule": data.get("ppm_schedule"),
                },
                "renewal": {
                    "month": data.get("renewal_month"),
                    "next_fee_increase_date": data["next_fee_increase_date"].isoformat() if data.get("next_fee_increase_date") else None,
                    "new_contract_drafted": data.get("new_contract_drafted") or False,
                    "notes": data.get("renewal_notes"),
                },
                "contacts": {
                    "primary": {
                        "name": data.get("primary_contact_name"),
                        "email": data.get("primary_contact_email"),
                        "phone": data.get("primary_contact_phone"),
                    }
                },
            },
        )

        # Optional: attach AI context / profile snapshot when available
        if build_full_prefill_payload:
            company = _get_company_for_client(client)
            if company:
                payload = build_full_prefill_payload(company, client_country=client.country, client_region=getattr(client, "region", None))
                # If model has explicit columns, set them; otherwise keep inside data_json.meta
                ai_ctx = (payload or {}).get("ai_context") or {}
                prof = (payload or {}).get("profile_snapshot") or {}
                if hasattr(contract, "ai_context"):
                    contract.ai_context = ai_ctx
                else:
                    contract.data_json.setdefault("meta", {})["ai_context"] = ai_ctx
                if hasattr(contract, "profile_snapshot"):
                    contract.profile_snapshot = prof
                else:
                    contract.data_json.setdefault("meta", {})["issuer_snapshot"] = prof

        db.session.add(contract)
        db.session.commit()
        flash("Draft contract created.", "success")
        return redirect(url_for("super_admin_simple_contracts.edit_contract", contract_id=contract.id))

    return render_template("super_admin/contracts/simple_contract_form.html", form=form, mode="create", contract=None)


@simple_contracts_bp.route("/<int:contract_id>/edit", methods=["GET", "POST"])
@super_admin_required
@login_required
def edit_contract(contract_id: int):
    """Classic edit for Draft contracts (read-only otherwise)."""
    contract = ClientContract.query.get_or_404(contract_id)
    client = Client.query.get_or_404(contract.client_id)
    if not _tenant_guard(client):
        flash("Not found.", "danger")
        return redirect(url_for("super_admin.manage_clients"))

    is_editable = (contract.sign_status or "Draft") == "Draft"

    form = ContractForm()
    _set_common_choices(form)
    form.client_id.choices = [(id_, label) for id_, label in form.client_id.choices if id_ != 0]

    if request.method == "GET":
        form.mirror_from_instance(contract)
        form.client_id.data = contract.client_id
        form.contract_title.data = contract.get_json("meta.contract_title", f"Contract #{contract.id}")
        form.ppm_schedule.data = contract.get_json("fees.ppm_schedule")
        form.primary_contact_name.data = contract.get_json("contacts.primary.name")
        form.primary_contact_email.data = contract.get_json("contacts.primary.email")
        form.primary_contact_phone.data = contract.get_json("contacts.primary.phone")

    if request.method == "POST" and form.validate_on_submit():
        if not is_editable:
            flash("Only Draft contracts can be edited here.", "warning")
            return redirect(url_for("super_admin_simple_contracts.edit_contract", contract_id=contract.id))

        data = form.to_dict()
        # update core columns
        contract.client_id = data["client_id"]
        contract.start_date = data["start_date"]
        contract.end_date = data["end_date"]
        contract.currency = data["currency"]
        contract.contract_value = data["contract_value"]
        contract.target_management_fee = data.get("target_management_fee")
        contract.annual_increase_percent = data.get("annual_increase_percent")
        contract.renewal_month = data.get("renewal_month")
        contract.next_fee_increase_date = data.get("next_fee_increase_date")
        contract.new_contract_drafted = data.get("new_contract_drafted") or False
        contract.renewal_notes = data.get("renewal_notes")
        contract.alert_owner_id = data.get("alert_owner_id")
        contract.last_reviewed_at = _date_to_datetime(data.get("last_reviewed_at"))
        contract.gar_contract_risk_level = data.get("gar_contract_risk_level")
        contract.gar_contract_recommendation = data.get("gar_contract_recommendation")

        # mirror important bits back into data_json (keeps preview pipelines happy)
        dj = contract.data_json or {}
        dj.setdefault("meta", {})
        dj["meta"]["contract_title"] = data["contract_title"]
        dj.setdefault("term", {})
        dj["term"]["start"] = data["start_date"].isoformat() if data["start_date"] else None
        dj["term"]["end"] = data["end_date"].isoformat() if data["end_date"] else None
        dj.setdefault("fees", {})
        dj["fees"]["currency"] = data["currency"]
        dj["fees"]["base_ex_vat"] = float(data["contract_value"] or 0)
        dj["fees"]["target_management_fee"] = float(data["target_management_fee"] or 0) if data.get("target_management_fee") else None
        dj["fees"]["annual_increase_percent"] = float(data["annual_increase_percent"] or 0) if data.get("annual_increase_percent") else None
        dj["fees"]["ppm_schedule"] = data.get("ppm_schedule")
        dj.setdefault("renewal", {})
        dj["renewal"].update({
            "month": data.get("renewal_month"),
            "next_fee_increase_date": data["next_fee_increase_date"].isoformat() if data.get("next_fee_increase_date") else None,
            "new_contract_drafted": data.get("new_contract_drafted") or False,
            "notes": data.get("renewal_notes"),
        })
        dj.setdefault("contacts", {}).setdefault("primary", {})
        dj["contacts"]["primary"].update({
            "name": data.get("primary_contact_name"),
            "email": data.get("primary_contact_email"),
            "phone": data.get("primary_contact_phone"),
        })
        contract.data_json = dj

        db.session.commit()
        flash("Contract updated.", "success")
        return redirect(url_for("super_admin_simple_contracts.edit_contract", contract_id=contract.id))

    return render_template("super_admin/contracts/simple_contract_form.html", form=form, mode="edit", contract=contract, is_editable=is_editable)
