from __future__ import annotations

from decimal import Decimal

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models.client.client import Client
from app.models.contracts import ClientContract
from app.models.contractor.job_docket import JobDocket
from app.models.members.unit import Unit
from app.models.works.work_order import WorkOrder
from app.services.core.module_connections import module_connection_context
from app.services.core.organisation_identity import (
    accept_organisation_connection_invite,
    create_organisation_connection_invite,
)
from app.services.contractor.job_docket_service import build_payment_request_document_payload
from app.services.gar import attach_gar_capability_readiness, build_gar_inquiry_response, build_operational_digest


finance_bp = Blueprint("finance", __name__, url_prefix="/finance")


def _company_clients():
    query = Client.query
    company_id = getattr(current_user, "company_id", None)
    if company_id:
        query = query.filter(Client.company_id == company_id)
    return query.order_by(Client.name.asc())


def _role_key() -> str:
    role_name = (
        getattr(current_user, "role_name", None)
        or getattr(getattr(current_user, "role", None), "name", "")
        or ""
    )
    return role_name.strip().lower().replace("_", " ")


def _finance_clients():
    query = _company_clients()
    if _role_key() == "financial controller":
        query = query.filter(Client.assigned_fc_id == current_user.id)
    return query


def _finance_client_ids() -> tuple[int, ...] | None:
    if _role_key() == "financial controller":
        return tuple(client.id for client in _finance_clients().all())
    return None


def _finance_payment_request_intake(client_ids: list[int]) -> list[WorkOrder]:
    if not client_ids:
        return []

    query = (
        WorkOrder.query
        .join(WorkOrder.job_docket)
        .filter(
            WorkOrder.client_id.in_(client_ids),
            JobDocket.invoice_status == "Ready for Finance",
            JobDocket.payment_status == "Awaiting Finance Review",
        )
        .order_by(JobDocket.updated_at.desc(), WorkOrder.created_at.desc())
    )
    company_id = getattr(current_user, "company_id", None)
    if company_id:
        query = query.filter(WorkOrder.company_id == company_id)
    return query.all()


def _finance_ready_payment_request(work_order_id: int) -> WorkOrder | None:
    client_ids = [client.id for client in _finance_clients().all()]
    if not client_ids:
        return None

    query = (
        WorkOrder.query
        .join(WorkOrder.job_docket)
        .filter(
            WorkOrder.id == work_order_id,
            WorkOrder.client_id.in_(client_ids),
            JobDocket.invoice_status == "Ready for Finance",
            JobDocket.payment_status == "Awaiting Finance Review",
        )
    )
    company_id = getattr(current_user, "company_id", None)
    if company_id:
        query = query.filter(WorkOrder.company_id == company_id)
    return query.first()


@finance_bp.route("/dashboard", endpoint="dashboard")
@login_required
def dashboard():
    gar_question = (request.args.get("gar_question") or "").strip()
    clients = _finance_clients().all()
    client_ids = [client.id for client in clients]
    payment_request_intake = _finance_payment_request_intake(client_ids)
    contract_query = ClientContract.query
    if client_ids:
        contract_query = contract_query.filter(ClientContract.client_id.in_(client_ids))

    portfolio_value = sum((client.contract_value or Decimal("0")) for client in clients)
    company_id = getattr(current_user, "company_id", None)
    gar_operational_digest = build_operational_digest(
        company_id=company_id,
        role_context=_role_key() or "finance",
        allowed_client_ids=_finance_client_ids(),
    ) if company_id else {}
    gar_inquiry_response = None
    if gar_question:
        gar_inquiry_response = build_gar_inquiry_response(
            gar_question,
            role_context=_role_key() or "finance",
            company_id=company_id,
            user_id=getattr(current_user, "id", None),
            allowed_client_ids=_finance_client_ids(),
            execute_source_query=True,
        )

    return render_template(
        "finance/dashboard.html",
        clients=clients,
        client_count=len(clients),
        unit_count=Unit.query.filter(Unit.client_id.in_(client_ids)).count() if client_ids else 0,
        contract_count=contract_query.count() if client_ids else 0,
        portfolio_value=portfolio_value,
        payment_request_intake=payment_request_intake,
        payment_request_intake_count=len(payment_request_intake),
        gar_operational_digest=gar_operational_digest,
        gar_question=gar_question,
        gar_inquiry_response=gar_inquiry_response,
    )


@finance_bp.route("/clients", endpoint="manage_clients")
@login_required
def manage_clients():
    clients = _finance_clients().all()
    return render_template("finance/manage_clients.html", clients=clients)


@finance_bp.route("/settings/connections", methods=["GET", "POST"], endpoint="settings_connections")
@login_required
def settings_connections():
    company = getattr(current_user, "company", None)
    if not company:
        flash("A finance organisation profile is required before managing connections.", "danger")
        return redirect(url_for("finance.dashboard"))

    if request.method == "POST":
        settings_action = (request.form.get("settings_action") or "").strip()

        if settings_action == "create_connection_invite":
            try:
                invite = create_organisation_connection_invite(
                    source_company_id=company.id,
                    target_email=(request.form.get("target_email") or "").strip() or None,
                    connection_type="management_finance",
                    allowed_modules=["finance", "works", "gar_ai"],
                    created_by_user_id=getattr(current_user, "id", None),
                    notes="Created from Finance Logix connection settings.",
                )
                db.session.commit()
                flash(f"Connection code created: {invite.invite_code}", "success")
            except ValueError as exc:
                db.session.rollback()
                flash(str(exc), "danger")
            return redirect(url_for("finance.settings_connections"))

        if settings_action == "accept_connection_invite":
            invite_code = (request.form.get("invite_code") or "").strip().upper()
            if not invite_code:
                flash("Enter the connection code before connecting organisations.", "warning")
                return redirect(url_for("finance.settings_connections"))
            try:
                accept_organisation_connection_invite(
                    invite_code=invite_code,
                    accepting_company_id=company.id,
                    accepted_by_user_id=getattr(current_user, "id", None),
                )
                db.session.commit()
                flash("Organisation connection accepted.", "success")
            except ValueError as exc:
                db.session.rollback()
                flash(str(exc), "danger")
            return redirect(url_for("finance.settings_connections"))

        flash("Choose a connection action before saving.", "warning")
        return redirect(url_for("finance.settings_connections"))

    return render_template(
        "finance/settings_connections.html",
        company=company,
        connection_context=module_connection_context(company, module_key="finance_logix"),
    )


@finance_bp.route("/payment-requests/<int:work_order_id>", endpoint="payment_request_review")
@login_required
def payment_request_review(work_order_id):
    work_order = _finance_ready_payment_request(work_order_id)
    if not work_order or not work_order.job_docket:
        abort(404)
    if not work_order.unit:
        abort(404)

    return render_template(
        "units/work_order_payment_request_document.html",
        unit=work_order.unit,
        client=work_order.client,
        company=work_order.company,
        work_order=work_order,
        job_docket=work_order.job_docket,
        payload=build_payment_request_document_payload(work_order.job_docket),
        back_url=url_for("finance.dashboard"),
        back_label="Back to Finance",
        secondary_url=url_for("finance.manage_clients"),
        secondary_label="Finance Clients",
        show_finance_handoff_action=False,
        review_surface_label="Finance Logix Intake",
        review_surface_note="Read-only intake for finance users. Invoice approval and payment posting are not live yet.",
    )


@finance_bp.route("/gar/feed.json", endpoint="gar_feed")
@login_required
def gar_feed():
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return jsonify({"error": "company_context_missing"}), 403

    role_context = _role_key() or "finance"
    payload = build_operational_digest(
        company_id=company_id,
        role_context=role_context,
        allowed_client_ids=_finance_client_ids(),
    )
    return jsonify(attach_gar_capability_readiness(
        payload,
        role_context=role_context,
        question=(request.args.get("question") or "").strip() or None,
    ))


@finance_bp.route("/gar/inquiry.json", endpoint="gar_inquiry")
@login_required
def gar_inquiry():
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return jsonify({"error": "company_context_missing"}), 403

    role_context = _role_key() or "finance"
    return jsonify(build_gar_inquiry_response(
        (request.args.get("question") or request.args.get("gar_question") or "").strip(),
        role_context=role_context,
        company_id=company_id,
        user_id=getattr(current_user, "id", None),
        allowed_client_ids=_finance_client_ids(),
        execute_source_query=True,
    ))
