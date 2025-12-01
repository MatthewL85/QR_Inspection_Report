from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.decorators import super_admin_required
from app.models.client.client import Client
from app.models.contracts import ClientContract
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

# ---------- routes ----------
@simple_contracts_bp.route("/new", methods=["GET", "POST"])
@super_admin_required
@login_required
def new_contract():
    """Classic quick-create (non-wizard) draft contract."""
    form = ContractForm()

    # Client choices (tenant scoped)
    q = Client.query
    cid = getattr(current_user, "company_id", None)
    if cid:
        q = q.filter(Client.company_id == cid)
    pairs = [(c.id, c.name) for c in q.order_by(Client.name.asc()).all()]
    form.set_client_choices(pairs)

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

        contract = ClientContract(
            client_id=client.id,
            template_version_id=data.get("template_version_id") or None,
            contract_title=data["contract_title"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            currency=data["currency"],
            contract_value=data["contract_value"],
            ppm_schedule=data.get("ppm_schedule"),
            primary_contact_name=data.get("primary_contact_name"),
            primary_contact_email=data.get("primary_contact_email"),
            primary_contact_phone=data.get("primary_contact_phone"),
            sign_status="Draft",
            # Seed a minimal data_json; your wizard uses richer schema JSON elsewhere.
            data_json={
                "term": {
                    "start": data["start_date"].isoformat() if data["start_date"] else None,
                    "end": data["end_date"].isoformat() if data["end_date"] else None,
                },
                "fees": {
                    "currency": data["currency"],
                    "base_ex_vat": float(data["contract_value"] or 0),
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
    # seed client dropdown
    q = Client.query
    cid = getattr(current_user, "company_id", None)
    if cid:
        q = q.filter(Client.company_id == cid)
    pairs = [(c.id, c.name) for c in q.order_by(Client.name.asc()).all()]
    form.set_client_choices(pairs, include_blank=False)

    if request.method == "GET":
        form.mirror_from_instance(contract)
        form.client_id.data = contract.client_id

    if request.method == "POST" and form.validate_on_submit():
        if not is_editable:
            flash("Only Draft contracts can be edited here.", "warning")
            return redirect(url_for("super_admin_simple_contracts.edit_contract", contract_id=contract.id))

        data = form.to_dict()
        # update core columns
        contract.client_id = data["client_id"]
        contract.contract_title = data["contract_title"]
        contract.start_date = data["start_date"]
        contract.end_date = data["end_date"]
        contract.currency = data["currency"]
        contract.contract_value = data["contract_value"]
        contract.ppm_schedule = data.get("ppm_schedule")
        contract.primary_contact_name = data.get("primary_contact_name")
        contract.primary_contact_email = data.get("primary_contact_email")
        contract.primary_contact_phone = data.get("primary_contact_phone")

        # mirror important bits back into data_json (keeps preview pipelines happy)
        dj = contract.data_json or {}
        dj.setdefault("term", {})
        dj["term"]["start"] = data["start_date"].isoformat() if data["start_date"] else None
        dj["term"]["end"] = data["end_date"].isoformat() if data["end_date"] else None
        dj.setdefault("fees", {})
        dj["fees"]["currency"] = data["currency"]
        dj["fees"]["base_ex_vat"] = float(data["contract_value"] or 0)
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
