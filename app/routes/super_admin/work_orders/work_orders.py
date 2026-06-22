from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.decorators.role import super_admin_required
from app.routes.super_admin import super_admin_bp
from app.services.works.workflow_service import (
    WorksFilters,
    assign_contractor_to_work_order,
    build_command_centre,
    convert_member_request_to_work_order,
    get_member_request_for_triage,
    update_member_request_triage,
    works_command_centre_payload,
)


def _company_id() -> int | None:
    return getattr(current_user, "company_id", None) or getattr(current_user, "active_company_id", None)


def _works_filter_args():
    return {
        key: value
        for key in ("search", "client_id", "status")
        if (value := (request.form.get(key) or request.args.get(key) or "").strip())
    }


@super_admin_bp.route("/work-orders", endpoint="work_orders")
@super_admin_required
@login_required
def work_orders():
    company_id = _company_id()
    if not company_id:
        abort(403)

    filters = WorksFilters(
        search=request.args.get("search", "").strip(),
        client_id=request.args.get("client_id", type=int),
        status=request.args.get("status", "").strip(),
    )
    data = build_command_centre(company_id=company_id, filters=filters, include_gar_history=True)

    return render_template(
        "super_admin/work_orders/index.html",
        filters=filters,
        **data,
    )


@super_admin_bp.route("/work-orders/feed.json", endpoint="work_orders_feed")
@super_admin_required
@login_required
def work_orders_feed():
    company_id = _company_id()
    if not company_id:
        abort(403)

    filters = WorksFilters(
        search=request.args.get("search", "").strip(),
        client_id=request.args.get("client_id", type=int),
        status=request.args.get("status", "").strip(),
    )
    data = build_command_centre(company_id=company_id, filters=filters, include_gar_history=True)
    return jsonify(works_command_centre_payload(data, filters, role_context="super_admin"))


@super_admin_bp.route("/work-orders/repeated-returns", endpoint="work_orders_repeated_returns")
@super_admin_required
@login_required
def work_orders_repeated_returns():
    company_id = _company_id()
    if not company_id:
        abort(403)

    filters = WorksFilters(
        search=request.args.get("search", "").strip(),
        client_id=request.args.get("client_id", type=int),
        status=request.args.get("status", "").strip(),
    )
    data = build_command_centre(company_id=company_id, filters=filters, include_gar_history=True)
    return render_template(
        "works/repeated_returns.html",
        layout_template="layouts/super_admin_base.html",
        dashboard_endpoint="super_admin.dashboard",
        dashboard_label="Dashboard",
        command_centre_endpoint="super_admin.work_orders",
        workspace_title="Repeated Returns",
        workspace_subtitle="Management review for contractor completions returned more than once.",
        filters=filters,
        **data,
    )


@super_admin_bp.route(
    "/work-orders/member-requests/<int:request_id>/convert",
    methods=["POST"],
    endpoint="convert_member_request_to_work_order",
)
@super_admin_required
@login_required
def convert_member_request(request_id):
    company_id = _company_id()
    if not company_id:
        abort(403)

    work_order = convert_member_request_to_work_order(
        request_id=request_id,
        company_id=company_id,
        created_by_id=current_user.id,
        access_context="super_admin",
    )
    if not work_order:
        abort(404)

    flash("Member request converted to a Works Logix work order.", "success")
    return redirect(url_for("super_admin.work_orders", **_works_filter_args()))


@super_admin_bp.route(
    "/work-orders/member-requests/<int:request_id>",
    methods=["GET"],
    endpoint="member_request_detail",
)
@super_admin_required
@login_required
def member_request_detail(request_id):
    company_id = _company_id()
    if not company_id:
        abort(403)

    member_request = get_member_request_for_triage(request_id=request_id, company_id=company_id)
    if not member_request:
        abort(404)

    return render_template(
        "works/member_request_detail.html",
        layout_template="layouts/super_admin_base.html",
        dashboard_endpoint="super_admin.work_orders",
        dashboard_label="Works Logix",
        convert_endpoint="super_admin.convert_member_request_to_work_order",
        triage_endpoint="super_admin.update_member_request_triage",
        member_request=member_request,
        filters=_works_filter_args(),
    )


@super_admin_bp.route(
    "/work-orders/member-requests/<int:request_id>/triage",
    methods=["POST"],
    endpoint="update_member_request_triage",
)
@super_admin_required
@login_required
def triage_member_request(request_id):
    company_id = _company_id()
    if not company_id:
        abort(403)

    updated = update_member_request_triage(
        request_id=request_id,
        company_id=company_id,
        reviewed_by_id=current_user.id,
        action=request.form.get("action", ""),
        message=request.form.get("message", ""),
        access_context="super_admin",
    )
    if not updated:
        flash("That member request could not be updated.", "danger")
        return redirect(url_for("super_admin.work_orders", **_works_filter_args()))

    flash("Member request triage response sent.", "success")
    return redirect(url_for("super_admin.work_orders", **_works_filter_args()))


@super_admin_bp.route(
    "/work-orders/<int:work_order_id>/assign-contractor",
    methods=["POST"],
    endpoint="assign_work_order_contractor",
)
@super_admin_required
@login_required
def assign_work_order_contractor(work_order_id):
    company_id = _company_id()
    contractor_id = request.form.get("contractor_id", type=int)
    if not company_id or not contractor_id:
        abort(400)

    work_order = assign_contractor_to_work_order(
        work_order_id=work_order_id,
        company_id=company_id,
        contractor_id=contractor_id,
        assigned_by_id=current_user.id,
        access_context="super_admin",
    )
    if not work_order:
        abort(404)

    flash("Work order assigned to contractor.", "success")
    return redirect(url_for("super_admin.work_orders", **_works_filter_args()))
