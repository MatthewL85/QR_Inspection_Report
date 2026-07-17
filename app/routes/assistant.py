from __future__ import annotations

from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.models.client.client import Client
from app.models.members.unit import Unit
from app.services.gar import attach_gar_capability_readiness, build_gar_inquiry_response, build_operational_digest
from app.services.works.workflow_service import (
    WorksFilters,
    assign_contractor_to_work_order,
    build_command_centre,
    build_contractor_routing_options,
    convert_member_request_to_work_order,
    get_member_request_for_triage,
    request_quotes_for_work_order,
    select_quote_response_for_work_order,
    update_member_request_triage,
    works_command_centre_payload,
)


assistant_bp = Blueprint("assistant", __name__, url_prefix="/assistant")

ASSISTANT_COVER_ROLES = {
    "assistant manager",
    "master assistant",
    "assistant lead",
    "senior assistant",
}


def _role_key(user) -> str:
    role_name = (
        getattr(user, "role_name", None)
        or getattr(getattr(user, "role", None), "name", "")
        or ""
    )
    return role_name.strip().lower().replace("_", " ")


def _has_assistant_cover_access() -> bool:
    return _role_key(current_user) in ASSISTANT_COVER_ROLES


def _assigned_clients():
    query = Client.query
    company_id = getattr(current_user, "company_id", None)
    if company_id:
        query = query.filter(Client.company_id == company_id)

    if _has_assistant_cover_access():
        return query.order_by(Client.name.asc())

    user_id = getattr(current_user, "id", None)
    if user_id:
        query = query.filter(
            or_(
                Client.assigned_assistant_id == user_id,
                Client.assigned_pm_id == user_id,
            )
        )

    return query.order_by(Client.name.asc())


def _assigned_client_ids() -> tuple[int, ...] | None:
    if _has_assistant_cover_access():
        return None
    return tuple(client.id for client in _assigned_clients().all())


def _works_filter_args():
    return {
        key: value
        for key in ("search", "client_id", "status")
        if (value := (request.form.get(key) or request.args.get(key) or "").strip())
    }


@assistant_bp.route("/dashboard", endpoint="dashboard")
@login_required
def dashboard():
    clients = _assigned_clients().all()
    client_ids = [client.id for client in clients]
    company_id = getattr(current_user, "company_id", None)
    role_context = "assistant_manager_cover" if _has_assistant_cover_access() else "assigned_assistant"
    gar_question = (request.args.get("gar_question") or "").strip()
    works_context = (
        build_command_centre(
            company_id=company_id,
            filters=WorksFilters(allowed_client_ids=_assigned_client_ids()),
        )
        if company_id else {"stats": {}, "operational_queues": {}}
    )
    works_gar_contractor_quality = (
        works_context.get("gar_works_intelligence", {})
        .get("pattern_memory", {})
        .get("patterns", {})
        .get("contractor_quality", [])
    )
    gar_inquiry_response = None
    if gar_question:
        gar_inquiry_response = build_gar_inquiry_response(
            gar_question,
            role_context=role_context,
            company_id=company_id,
            user_id=getattr(current_user, "id", None),
            allowed_client_ids=_assigned_client_ids(),
            execute_source_query=True,
        )
    return render_template(
        "assistant/dashboard.html",
        clients=clients,
        client_count=len(clients),
        unit_count=Unit.query.filter(Unit.client_id.in_(client_ids)).count() if client_ids else 0,
        cover_access=_has_assistant_cover_access(),
        works_stats=works_context.get("stats", {}),
        works_operational_queues=works_context.get("operational_queues", {}),
        works_next_actions=works_context.get("next_actions", []),
        works_gar_contractor_quality=works_gar_contractor_quality,
        gar_question=gar_question,
        gar_inquiry_response=gar_inquiry_response,
    )


@assistant_bp.route("/clients", endpoint="manage_clients")
@login_required
def manage_clients():
    clients = _assigned_clients().all()
    return render_template(
        "assistant/manage_clients.html",
        clients=clients,
        cover_access=_has_assistant_cover_access(),
    )


@assistant_bp.route("/work-orders", endpoint="work_orders")
@login_required
def work_orders():
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        flash("Company context is missing. Please log in again.", "danger")
        return redirect(url_for("auth.login"))

    filters = WorksFilters(
        search=request.args.get("search", "").strip(),
        client_id=request.args.get("client_id", type=int),
        status=request.args.get("status", "").strip(),
        allowed_client_ids=_assigned_client_ids(),
    )
    data = build_command_centre(company_id=company_id, filters=filters, include_gar_history=True)
    return render_template(
        "assistant/work_orders.html",
        filters=filters,
        cover_access=_has_assistant_cover_access(),
        **data,
    )


@assistant_bp.route("/work-orders/feed.json", endpoint="work_orders_feed")
@login_required
def work_orders_feed():
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return jsonify({"error": "company_context_missing"}), 403

    filters = WorksFilters(
        search=request.args.get("search", "").strip(),
        client_id=request.args.get("client_id", type=int),
        status=request.args.get("status", "").strip(),
        allowed_client_ids=_assigned_client_ids(),
    )
    data = build_command_centre(company_id=company_id, filters=filters, include_gar_history=True)
    role_context = "assistant_manager_cover" if _has_assistant_cover_access() else "assigned_assistant"
    return jsonify(works_command_centre_payload(data, filters, role_context=role_context))


@assistant_bp.route("/work-orders/repeated-returns", endpoint="work_orders_repeated_returns")
@login_required
def work_orders_repeated_returns():
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        flash("Company context is missing. Please log in again.", "danger")
        return redirect(url_for("auth.login"))

    filters = WorksFilters(
        search=request.args.get("search", "").strip(),
        client_id=request.args.get("client_id", type=int),
        status=request.args.get("status", "").strip(),
        allowed_client_ids=_assigned_client_ids(),
    )
    data = build_command_centre(company_id=company_id, filters=filters, include_gar_history=True)
    return render_template(
        "works/repeated_returns.html",
        layout_template="base.html",
        dashboard_endpoint="assistant.dashboard",
        dashboard_label="Dashboard",
        command_centre_endpoint="assistant.work_orders",
        workspace_title="Repeated Returns",
        workspace_subtitle=(
            "Assistant Manager cover review for repeated contractor completion returns."
            if _has_assistant_cover_access()
            else "Assistant review for repeated contractor completion returns on assigned developments."
        ),
        cover_access=_has_assistant_cover_access(),
        filters=filters,
        **data,
    )


@assistant_bp.route("/gar/feed.json", endpoint="gar_feed")
@login_required
def gar_feed():
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return jsonify({"error": "company_context_missing"}), 403

    role_context = "assistant_manager_cover" if _has_assistant_cover_access() else "assigned_assistant"
    payload = build_operational_digest(
        company_id=company_id,
        role_context=role_context,
        allowed_client_ids=_assigned_client_ids(),
    )
    return jsonify(attach_gar_capability_readiness(
        payload,
        role_context=role_context,
        question=(request.args.get("question") or "").strip() or None,
    ))


@assistant_bp.route("/gar/inquiry.json", endpoint="gar_inquiry")
@login_required
def gar_inquiry():
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return jsonify({"error": "company_context_missing"}), 403

    role_context = "assistant_manager_cover" if _has_assistant_cover_access() else "assigned_assistant"
    return jsonify(build_gar_inquiry_response(
        (request.args.get("question") or request.args.get("gar_question") or "").strip(),
        role_context=role_context,
        company_id=company_id,
        user_id=getattr(current_user, "id", None),
        allowed_client_ids=_assigned_client_ids(),
        execute_source_query=True,
    ))


@assistant_bp.route(
    "/work-orders/member-requests/<int:request_id>/convert",
    methods=["POST"],
    endpoint="convert_member_request",
)
@login_required
def convert_member_request(request_id):
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        flash("Company context is missing. Please log in again.", "danger")
        return redirect(url_for("auth.login"))
    contractor_id = request.form.get("contractor_id", type=int)
    if not contractor_id:
        flash("Select a contractor before converting the request to a work order.", "warning")
        return redirect(url_for("assistant.member_request_detail", request_id=request_id, **_works_filter_args()))

    work_order = convert_member_request_to_work_order(
        request_id=request_id,
        company_id=company_id,
        created_by_id=current_user.id,
        contractor_id=contractor_id,
        allowed_client_ids=_assigned_client_ids(),
        access_context="assistant_manager_cover" if _has_assistant_cover_access() else "assigned_assistant",
    )
    if not work_order:
        flash("That request could not be converted for your assigned developments.", "danger")
        return redirect(url_for("assistant.work_orders", **_works_filter_args()))

    flash("Member request converted and sent to the selected contractor.", "success")
    return redirect(url_for("assistant.work_orders", **_works_filter_args()))


@assistant_bp.route(
    "/work-orders/member-requests/<int:request_id>",
    methods=["GET"],
    endpoint="member_request_detail",
)
@login_required
def member_request_detail(request_id):
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        flash("Company context is missing. Please log in again.", "danger")
        return redirect(url_for("auth.login"))

    member_request = get_member_request_for_triage(
        request_id=request_id,
        company_id=company_id,
        allowed_client_ids=_assigned_client_ids(),
    )
    if not member_request:
        flash("That request is not available for your assigned developments.", "danger")
        return redirect(url_for("assistant.work_orders", **_works_filter_args()))

    return render_template(
        "works/member_request_detail.html",
        layout_template="base.html",
        dashboard_endpoint="assistant.work_orders",
        dashboard_label="Works Logix",
        convert_endpoint="assistant.convert_member_request",
        triage_endpoint="assistant.update_member_request_triage",
        member_request=member_request,
        contractor_routing_options=build_contractor_routing_options(
            member_request=member_request,
            company_id=company_id,
        ),
        filters=_works_filter_args(),
        cover_access=_has_assistant_cover_access(),
    )


@assistant_bp.route(
    "/work-orders/member-requests/<int:request_id>/triage",
    methods=["POST"],
    endpoint="update_member_request_triage",
)
@login_required
def update_member_request_triage_route(request_id):
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        flash("Company context is missing. Please log in again.", "danger")
        return redirect(url_for("auth.login"))

    updated = update_member_request_triage(
        request_id=request_id,
        company_id=company_id,
        reviewed_by_id=getattr(current_user, "id", None),
        action=request.form.get("action", ""),
        message=request.form.get("message", ""),
        allowed_client_ids=_assigned_client_ids(),
        access_context="assistant_manager_cover" if _has_assistant_cover_access() else "assigned_assistant",
    )
    if not updated:
        flash("That member request could not be updated.", "danger")
        return redirect(url_for("assistant.work_orders", **_works_filter_args()))

    flash("Member request triage response sent.", "success")
    return redirect(url_for("assistant.work_orders", **_works_filter_args()))


@assistant_bp.route(
    "/work-orders/<int:work_order_id>/assign-contractor",
    methods=["POST"],
    endpoint="assign_work_order_contractor",
)
@login_required
def assign_work_order_contractor(work_order_id):
    company_id = getattr(current_user, "company_id", None)
    contractor_id = request.form.get("contractor_id", type=int)
    if not company_id or not contractor_id:
        flash("Choose a contractor before assigning this work order.", "warning")
        return redirect(url_for("assistant.work_orders", **_works_filter_args()))

    work_order = assign_contractor_to_work_order(
        work_order_id=work_order_id,
        company_id=company_id,
        contractor_id=contractor_id,
        allowed_client_ids=_assigned_client_ids(),
        assigned_by_id=current_user.id,
        access_context="assistant_manager_cover" if _has_assistant_cover_access() else "assigned_assistant",
    )
    if not work_order:
        flash("That work order could not be assigned for your developments.", "danger")
        return redirect(url_for("assistant.work_orders", **_works_filter_args()))

    flash("Work order assigned to contractor.", "success")
    return redirect(url_for("assistant.work_orders", **_works_filter_args()))


@assistant_bp.route(
    "/work-orders/<int:work_order_id>/request-quotes",
    methods=["POST"],
    endpoint="request_work_order_quotes",
)
@login_required
def request_work_order_quotes(work_order_id):
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        flash("Company context is missing. Please log in again.", "danger")
        return redirect(url_for("auth.login"))

    quote_deadline = None
    quote_deadline_raw = (request.form.get("quote_deadline") or "").strip()
    if quote_deadline_raw:
        try:
            quote_deadline = datetime.strptime(quote_deadline_raw, "%Y-%m-%d")
        except ValueError:
            flash("Enter a valid quote deadline.", "warning")
            return redirect(url_for("assistant.work_orders", **_works_filter_args()))

    access_context = "assistant_manager_cover" if _has_assistant_cover_access() else "assigned_assistant"
    summary = request_quotes_for_work_order(
        work_order_id=work_order_id,
        company_id=company_id,
        contractor_ids=request.form.getlist("contractor_ids", type=int),
        requested_by_id=current_user.id,
        allowed_client_ids=_assigned_client_ids(),
        access_context=access_context,
        quote_deadline=quote_deadline,
        notes=(request.form.get("quote_notes") or "").strip(),
        visible_to_directors=bool(request.form.get("visible_to_directors")),
    )
    if not summary.get("work_order"):
        flash("That work order could not be found for your assigned developments.", "danger")
        return redirect(url_for("assistant.work_orders", **_works_filter_args()))

    if summary["created"]:
        flash(f"Quotation request sent to {summary['created']} contractor user(s).", "success")
    elif summary["skipped_existing"]:
        flash("Those quotation requests already exist.", "info")
    else:
        flash("No connected contractor users could receive that quotation request.", "warning")
    return redirect(url_for("assistant.work_orders", queue="quote_requests", **_works_filter_args()))


@assistant_bp.route(
    "/work-orders/<int:work_order_id>/quotes/<int:quote_response_id>/select",
    methods=["POST"],
    endpoint="select_work_order_quote",
)
@login_required
def select_work_order_quote(work_order_id, quote_response_id):
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        flash("Company context is missing. Please log in again.", "danger")
        return redirect(url_for("auth.login"))

    access_context = "assistant_manager_cover" if _has_assistant_cover_access() else "assigned_assistant"
    quote_response = select_quote_response_for_work_order(
        work_order_id=work_order_id,
        quote_response_id=quote_response_id,
        company_id=company_id,
        selected_by_id=current_user.id,
        decision_note=(request.form.get("decision_note") or "").strip(),
        allowed_client_ids=_assigned_client_ids(),
        access_context=access_context,
    )
    if not quote_response:
        flash("That quotation could not be selected for your assigned developments.", "danger")
        return redirect(url_for("assistant.work_orders", queue="quote_requests", **_works_filter_args()))

    flash("Quotation selected and the contractor has been assigned.", "success")
    return redirect(url_for("assistant.work_orders", queue="open", **_works_filter_args()))
