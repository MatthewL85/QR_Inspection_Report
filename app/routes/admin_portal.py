from __future__ import annotations

from functools import wraps

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app.models.client.client import Client
from app.models.members.unit import Unit
from app.services.gar import attach_gar_capability_readiness, build_gar_inquiry_response, build_operational_digest
from app.services.works.workflow_service import (
    WorksFilters,
    assign_contractor_to_work_order,
    build_command_centre,
    convert_member_request_to_work_order,
    get_member_request_for_triage,
    update_member_request_triage,
    works_command_centre_payload,
)


admin_portal_bp = Blueprint("admin_portal", __name__, url_prefix="/admin-portal")


def _admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        role_name = (
            session.get("role")
            or getattr(current_user, "role_name", None)
            or getattr(getattr(current_user, "role", None), "name", "")
            or ""
        )
        if role_name.strip().lower() != "admin":
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped


def _company_clients():
    query = Client.query
    company_id = getattr(current_user, "company_id", None)
    if company_id:
        query = query.filter(Client.company_id == company_id)
    return query.order_by(Client.name.asc())


def _works_filter_args():
    return {
        key: value
        for key in ("search", "client_id", "status")
        if (value := (request.form.get(key) or request.args.get(key) or "").strip())
    }


@admin_portal_bp.route("/dashboard", endpoint="dashboard")
@login_required
@_admin_required
def dashboard():
    gar_question = (request.args.get("gar_question") or "").strip()
    clients = _company_clients().all()
    client_ids = [client.id for client in clients]
    company_id = getattr(current_user, "company_id", None)
    works_context = (
        build_command_centre(company_id=company_id, filters=WorksFilters())
        if company_id else {"stats": {}, "operational_queues": {}, "next_actions": []}
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
            role_context="admin",
            company_id=company_id,
            user_id=getattr(current_user, "id", None),
            execute_source_query=True,
        )
    return render_template(
        "admin_portal/dashboard.html",
        clients=clients,
        client_count=len(clients),
        unit_count=Unit.query.filter(Unit.client_id.in_(client_ids)).count() if client_ids else 0,
        works_stats=works_context.get("stats", {}),
        works_operational_queues=works_context.get("operational_queues", {}),
        works_next_actions=works_context.get("next_actions", []),
        works_gar_contractor_quality=works_gar_contractor_quality,
        gar_question=gar_question,
        gar_inquiry_response=gar_inquiry_response,
    )


@admin_portal_bp.route("/clients", endpoint="manage_clients")
@login_required
@_admin_required
def manage_clients():
    clients = _company_clients().all()
    return render_template("admin_portal/manage_clients.html", clients=clients)


@admin_portal_bp.route("/work-orders", endpoint="work_orders")
@login_required
@_admin_required
def work_orders():
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        flash("Company context is missing. Please log in again.", "danger")
        return redirect(url_for("auth.login"))

    filters = WorksFilters(
        search=request.args.get("search", "").strip(),
        client_id=request.args.get("client_id", type=int),
        status=request.args.get("status", "").strip(),
    )
    data = build_command_centre(company_id=company_id, filters=filters, include_gar_history=True)
    return render_template("admin_portal/work_orders.html", filters=filters, **data)


@admin_portal_bp.route("/work-orders/feed.json", endpoint="work_orders_feed")
@login_required
@_admin_required
def work_orders_feed():
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return jsonify({"error": "company_context_missing"}), 403

    filters = WorksFilters(
        search=request.args.get("search", "").strip(),
        client_id=request.args.get("client_id", type=int),
        status=request.args.get("status", "").strip(),
    )
    data = build_command_centre(company_id=company_id, filters=filters, include_gar_history=True)
    return jsonify(works_command_centre_payload(data, filters, role_context="admin"))


@admin_portal_bp.route("/work-orders/repeated-returns", endpoint="work_orders_repeated_returns")
@login_required
@_admin_required
def work_orders_repeated_returns():
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        flash("Company context is missing. Please log in again.", "danger")
        return redirect(url_for("auth.login"))

    filters = WorksFilters(
        search=request.args.get("search", "").strip(),
        client_id=request.args.get("client_id", type=int),
        status=request.args.get("status", "").strip(),
    )
    data = build_command_centre(company_id=company_id, filters=filters, include_gar_history=True)
    return render_template(
        "works/repeated_returns.html",
        layout_template="base.html",
        dashboard_endpoint="admin_portal.dashboard",
        dashboard_label="Dashboard",
        command_centre_endpoint="admin_portal.work_orders",
        workspace_title="Repeated Returns",
        workspace_subtitle="Admin review for contractor completions returned more than once.",
        filters=filters,
        **data,
    )


@admin_portal_bp.route(
    "/work-orders/member-requests/<int:request_id>/convert",
    methods=["POST"],
    endpoint="convert_member_request",
)
@login_required
@_admin_required
def convert_member_request(request_id):
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        flash("Company context is missing. Please log in again.", "danger")
        return redirect(url_for("auth.login"))

    work_order = convert_member_request_to_work_order(
        request_id=request_id,
        company_id=company_id,
        created_by_id=current_user.id,
        access_context="admin",
    )
    if not work_order:
        flash("That request could not be converted.", "danger")
        return redirect(url_for("admin_portal.work_orders", **_works_filter_args()))

    flash("Member request converted to a Works Logix work order.", "success")
    return redirect(url_for("admin_portal.work_orders", **_works_filter_args()))


@admin_portal_bp.route(
    "/work-orders/member-requests/<int:request_id>",
    methods=["GET"],
    endpoint="member_request_detail",
)
@login_required
@_admin_required
def member_request_detail(request_id):
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        flash("Company context is missing. Please log in again.", "danger")
        return redirect(url_for("auth.login"))

    member_request = get_member_request_for_triage(request_id=request_id, company_id=company_id)
    if not member_request:
        flash("That request could not be found.", "danger")
        return redirect(url_for("admin_portal.work_orders", **_works_filter_args()))

    return render_template(
        "works/member_request_detail.html",
        layout_template="base.html",
        dashboard_endpoint="admin_portal.work_orders",
        dashboard_label="Works Logix",
        convert_endpoint="admin_portal.convert_member_request",
        triage_endpoint="admin_portal.update_member_request_triage",
        member_request=member_request,
        filters=_works_filter_args(),
    )


@admin_portal_bp.route(
    "/work-orders/member-requests/<int:request_id>/triage",
    methods=["POST"],
    endpoint="update_member_request_triage",
)
@login_required
@_admin_required
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
        access_context="admin",
    )
    if not updated:
        flash("That member request could not be updated.", "danger")
        return redirect(url_for("admin_portal.work_orders", **_works_filter_args()))

    flash("Member request triage response sent.", "success")
    return redirect(url_for("admin_portal.work_orders", **_works_filter_args()))


@admin_portal_bp.route(
    "/work-orders/<int:work_order_id>/assign-contractor",
    methods=["POST"],
    endpoint="assign_work_order_contractor",
)
@login_required
@_admin_required
def assign_work_order_contractor(work_order_id):
    company_id = getattr(current_user, "company_id", None)
    contractor_id = request.form.get("contractor_id", type=int)
    if not company_id or not contractor_id:
        flash("Choose a contractor before assigning this work order.", "warning")
        return redirect(url_for("admin_portal.work_orders", **_works_filter_args()))

    work_order = assign_contractor_to_work_order(
        work_order_id=work_order_id,
        company_id=company_id,
        contractor_id=contractor_id,
        assigned_by_id=current_user.id,
        access_context="admin",
    )
    if not work_order:
        flash("That work order could not be assigned.", "danger")
        return redirect(url_for("admin_portal.work_orders", **_works_filter_args()))

    flash("Work order assigned to contractor.", "success")
    return redirect(url_for("admin_portal.work_orders", **_works_filter_args()))


@admin_portal_bp.route("/gar/feed.json", endpoint="gar_feed")
@login_required
@_admin_required
def gar_feed():
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return jsonify({"error": "company_context_missing"}), 403

    payload = build_operational_digest(
        company_id=company_id,
        role_context="admin",
    )
    return jsonify(attach_gar_capability_readiness(
        payload,
        role_context="admin",
        question=(request.args.get("question") or "").strip() or None,
    ))


@admin_portal_bp.route("/gar/inquiry.json", endpoint="gar_inquiry")
@login_required
@_admin_required
def gar_inquiry():
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return jsonify({"error": "company_context_missing"}), 403

    return jsonify(build_gar_inquiry_response(
        (request.args.get("question") or request.args.get("gar_question") or "").strip(),
        role_context="admin",
        company_id=company_id,
        user_id=getattr(current_user, "id", None),
        execute_source_query=True,
    ))
