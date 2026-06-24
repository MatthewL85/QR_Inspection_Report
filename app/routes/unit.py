import re

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.client.client import Client
from app.models.members.member import Member
from app.models.members.unit import Unit
from app.models.works.work_order_reopen_request import WorkOrderReopenRequest
from app.services.gar import build_work_order_context
from app.services.unit_access_service import create_unit_access_invite
from app.services.unit_service import UnitService
from app.services.work_order_reopen_service import WorkOrderReopenService
from app.services.works import build_work_order_audit_pack, can_manage_reopen_request, can_manage_work_order
from app.services.works.workflow_service import build_work_order_lifecycle, progress_updates_for_audience, review_contractor_completion


unit_bp = Blueprint("unit_bp", __name__, url_prefix="/units")


def _company_id() -> int | None:
    return getattr(current_user, "company_id", None) or getattr(current_user, "active_company_id", None)


def _can_edit_core_unit_details() -> bool:
    if getattr(current_user, "is_super_admin", False):
        return True
    role_name = (getattr(current_user, "role_name", None) or getattr(getattr(current_user, "role", None), "name", "") or "").strip()
    normalized_role = role_name.lower().replace("_", " ")
    return normalized_role in {"super admin", "superadmin", "platform admin", "system admin"}


def _natural_unit_key(value):
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", str(value or ""))
    ]


def _unit_navigation(unit: Unit, company_id: int):
    units = (
        Unit.query
        .filter(
            Unit.client_id == unit.client_id,
            Unit.company_id == company_id,
        )
        .all()
    )
    units.sort(key=lambda item: (
        _natural_unit_key(item.block_name),
        _natural_unit_key(item.core_name),
        _natural_unit_key(item.unit_number or item.unit_label),
        item.id,
    ))

    if len(units) <= 1:
        return None, None

    current_index = next((index for index, item in enumerate(units) if item.id == unit.id), None)
    if current_index is None:
        return None, None

    previous_unit = units[current_index - 1] if current_index > 0 else units[-1]
    next_unit = units[current_index + 1] if current_index < len(units) - 1 else units[0]
    return previous_unit, next_unit


@unit_bp.route("/", methods=["GET"], endpoint="list")
@login_required
def list_units_route():
    company_id = _company_id()
    if not company_id:
        abort(403)

    page = request.args.get("page", 1, type=int)
    client_id = request.args.get("client_id", type=int)
    search = request.args.get("search")
    block_name = request.args.get("block_name") or request.args.get("block")
    core_name = request.args.get("core_name") or request.args.get("core")

    pagination = UnitService.list_units_for_company(
        company_id=company_id,
        page=page,
        per_page=25,
        client_id=client_id,
        search=search,
        block_name=block_name,
        core_name=core_name,
        only_active=True,
    )
    clients = Client.query.filter_by(company_id=company_id).order_by(Client.name.asc()).all()
    selected_client = next((client for client in clients if client.id == client_id), None)
    page_client_ids = {unit.client_id for unit in pagination.items}
    directory_client_name = None
    if selected_client:
        directory_client_name = selected_client.name
    elif len(page_client_ids) == 1 and pagination.items:
        directory_client_name = pagination.items[0].client.name if pagination.items[0].client else None

    block_values = sorted(
        {
            row[0]
            for row in Unit.query.with_entities(Unit.block_name)
            .filter(Unit.company_id == company_id, Unit.block_name.isnot(None), Unit.block_name != "")
            .all()
        },
        key=str.lower,
    )
    core_values = sorted(
        {
            row[0]
            for row in Unit.query.with_entities(Unit.core_name)
            .filter(Unit.company_id == company_id, Unit.core_name.isnot(None), Unit.core_name != "")
            .all()
        },
        key=str.lower,
    )

    return render_template(
        "units/list.html",
        pagination=pagination,
        units=pagination.items,
        clients=clients,
        blocks=block_values,
        cores=core_values,
        selected_client_id=client_id,
        directory_client_name=directory_client_name,
        search=search or "",
        selected_block=block_name or "",
        selected_core=core_name or "",
        block_name=block_name or "",
        core_name=core_name or "",
        only_active=True,
    )


@unit_bp.route("/<int:unit_id>", methods=["GET"], endpoint="view")
@login_required
def view_unit_route(unit_id):
    company_id = _company_id()
    if not company_id:
        abort(403)

    data = UnitService.get_unit(unit_id)
    if not data or data["unit"].company_id != company_id:
        abort(404)

    previous_unit, next_unit = _unit_navigation(data["unit"], company_id)

    return render_template(
        "units/detail.html",
        unit=data["unit"],
        client=data["client"],
        company=data["company"],
        block=data["block"],
        core=data["core"],
        owners=data["owner_entities"],
        owner_links=data["ownership_history"],
        residents=data["tenant_entities"],
        resident_links=data["tenancy_history"],
        invoices=data["invoices"],
        work_orders=data["work_orders"],
        closed_work_orders=data["closed_work_orders"],
        maintenance_requests=data["maintenance_requests"],
        works_summary=data["works_summary"],
        pending_reopen_requests=data["pending_reopen_requests"],
        closed_work_search=request.args.get("closed_work_search", "").strip(),
        work_view=request.args.get("work_view", "open").strip().lower(),
        documents=data["documents"],
        child_units=data["child_units"],
        previous_unit=previous_unit,
        next_unit=next_unit,
    )


@unit_bp.route("/<int:unit_id>/work-orders/<int:work_order_id>", methods=["GET"], endpoint="work_order_review")
@login_required
def work_order_review(unit_id, work_order_id):
    company_id = _company_id()
    if not company_id:
        abort(403)

    data = UnitService.get_unit(unit_id)
    if not data or data["unit"].company_id != company_id:
        abort(404)

    work_order = UnitService.get_unit_work_order(unit_id, work_order_id, company_id)
    if not work_order:
        abort(404)
    if not can_manage_work_order(current_user, work_order, company_id):
        abort(403)

    return render_template(
        "units/work_order_review.html",
        unit=data["unit"],
        client=data["client"],
        company=data["company"],
        work_order=work_order,
        gar_work_order_context=build_work_order_context(work_order.id, getattr(current_user, "id", None), "admin"),
        work_order_audit_pack=build_work_order_audit_pack(work_order),
        workflow_timeline=build_work_order_lifecycle(work_order),
        progress_updates=progress_updates_for_audience(work_order, "management"),
    )


@unit_bp.route("/<int:unit_id>/work-orders/<int:work_order_id>/reopen", methods=["POST"], endpoint="work_order_reopen")
@login_required
def work_order_reopen(unit_id, work_order_id):
    company_id = _company_id()
    if not company_id:
        abort(403)

    work_order = UnitService.get_unit_work_order(unit_id, work_order_id, company_id)
    if not work_order:
        abort(404)
    if not can_manage_work_order(current_user, work_order, company_id):
        abort(403)

    reopened = UnitService.reopen_work_order(unit_id, work_order_id, company_id)
    if not reopened:
        abort(404)

    flash("Work order reopened successfully.", "success")
    return redirect(url_for("unit_bp.work_order_review", unit_id=unit_id, work_order_id=work_order_id))


@unit_bp.route(
    "/<int:unit_id>/work-orders/<int:work_order_id>/completion-review/<decision>",
    methods=["POST"],
    endpoint="work_order_completion_review",
)
@login_required
def work_order_completion_review(unit_id, work_order_id, decision):
    company_id = _company_id()
    if not company_id:
        abort(403)

    data = UnitService.get_unit(unit_id)
    if not data or data["unit"].company_id != company_id:
        abort(404)

    work_order = UnitService.get_unit_work_order(unit_id, work_order_id, company_id)
    if not work_order:
        abort(404)
    if not can_manage_work_order(current_user, work_order, company_id):
        abort(403)

    reviewed = review_contractor_completion(
        work_order_id=work_order_id,
        company_id=company_id,
        reviewed_by_user_id=current_user.id,
        decision=decision,
        review_notes=request.form.get("review_notes", ""),
    )
    if not reviewed:
        abort(404)

    if decision == "approve":
        flash("Contractor completion approved and work order closed.", "success")
    else:
        flash("Work order returned to the contractor for follow-up.", "success")

    return redirect(url_for("unit_bp.work_order_review", unit_id=unit_id, work_order_id=work_order_id))


@unit_bp.route("/reopen-requests/<int:request_id>/approve", methods=["POST"], endpoint="reopen_request_approve")
@login_required
def reopen_request_approve(request_id):
    company_id = _company_id()
    if not company_id:
        abort(403)

    reopen_request = WorkOrderReopenRequest.query.filter_by(id=request_id).first_or_404()
    if not can_manage_reopen_request(current_user, reopen_request, company_id):
        abort(403)

    approved = WorkOrderReopenService.approve_request(
        request_id=request_id,
        company_id=company_id,
        reviewed_by_user_id=current_user.id,
        review_notes=request.form.get("review_notes", ""),
    )
    if not approved:
        abort(404)

    flash("Reopen request approved and work order reopened.", "success")
    return redirect(request.referrer or url_for("unit_bp.list"))


@unit_bp.route("/reopen-requests/<int:request_id>/reject", methods=["POST"], endpoint="reopen_request_reject")
@login_required
def reopen_request_reject(request_id):
    company_id = _company_id()
    if not company_id:
        abort(403)

    reopen_request = WorkOrderReopenRequest.query.filter_by(id=request_id).first_or_404()
    if not can_manage_reopen_request(current_user, reopen_request, company_id):
        abort(403)

    rejected = WorkOrderReopenService.reject_request(
        request_id=request_id,
        company_id=company_id,
        reviewed_by_user_id=current_user.id,
        review_notes=request.form.get("review_notes", ""),
    )
    if not rejected:
        abort(404)

    flash("Reopen request rejected.", "success")
    return redirect(request.referrer or url_for("unit_bp.list"))


@unit_bp.route("/create", methods=["GET"], endpoint="create")
@login_required
def create_unit_form():
    company_id = _company_id()
    if not company_id:
        abort(403)

    return render_template(
        "units/form.html",
        mode="create",
        unit=None,
        can_edit_core_details=True,
        clients=Client.query.filter_by(company_id=company_id).order_by(Client.name.asc()).all(),
        members=Member.query.filter_by(company_id=company_id).order_by(Member.last_name.asc()).all(),
        possible_parents=Unit.query.filter_by(company_id=company_id).order_by(Unit.unit_label.asc()).all(),
        owner_member=None,
        owner_link=None,
        co_owner_member=None,
        co_owner_link=None,
        tenant_member=None,
        tenant_link=None,
    )


@unit_bp.route("/create", methods=["POST"], endpoint="create_submit")
@login_required
def create_unit_submit():
    company_id = _company_id()
    if not company_id:
        abort(403)

    try:
        unit = UnitService.create_unit(request.form, company_id=company_id)
        flash("Unit created successfully.", "success")
        return redirect(url_for("unit_bp.view", unit_id=unit.id))
    except Exception as exc:
        flash(f"Error creating unit: {exc}", "danger")
        return redirect(url_for("unit_bp.create"))


@unit_bp.route("/<int:unit_id>/edit", methods=["GET"], endpoint="edit")
@login_required
def edit_unit_form(unit_id):
    company_id = _company_id()
    if not company_id:
        abort(403)

    unit = Unit.query.filter_by(id=unit_id, company_id=company_id).first_or_404()
    relationship_context = UnitService.relationship_form_context(unit)

    return render_template(
        "units/form.html",
        mode="edit",
        unit=unit,
        can_edit_core_details=_can_edit_core_unit_details(),
        clients=Client.query.filter_by(company_id=company_id).order_by(Client.name.asc()).all(),
        members=Member.query.filter_by(company_id=company_id).order_by(Member.last_name.asc()).all(),
        possible_parents=Unit.query.filter(
            Unit.company_id == company_id,
            Unit.client_id == unit.client_id,
            Unit.id != unit.id,
        ).order_by(Unit.unit_label.asc()).all(),
        **relationship_context,
    )


@unit_bp.route("/<int:unit_id>/edit", methods=["POST"], endpoint="edit_submit")
@login_required
def edit_unit_submit(unit_id):
    company_id = _company_id()
    if not company_id:
        abort(403)

    try:
        UnitService.update_unit(
            unit_id,
            request.form,
            company_id=company_id,
            can_edit_core_details=_can_edit_core_unit_details(),
        )
        flash("Unit updated successfully.", "success")
        return redirect(url_for("unit_bp.view", unit_id=unit_id))
    except Exception as exc:
        flash(f"Error updating unit: {exc}", "danger")
        return redirect(url_for("unit_bp.edit", unit_id=unit_id))


@unit_bp.route("/<int:unit_id>/access-invites", methods=["POST"], endpoint="create_access_invite")
@login_required
def create_access_invite(unit_id):
    company_id = _company_id()
    if not company_id:
        abort(403)

    unit = Unit.query.filter_by(id=unit_id, company_id=company_id).first_or_404()
    role = (request.form.get("role") or "owner").strip().lower()
    email = (request.form.get("email") or "").strip()

    try:
        invite = create_unit_access_invite(
            unit,
            role=role,
            email=email,
            created_by_user_id=getattr(current_user, "id", None),
            notes="Generated from Unit Detail",
        )
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(url_for("unit_bp.view", unit_id=unit.id, tab="owners"))

    email_note = f" for {invite.email}" if invite.email else ""
    flash(f"Members Logix access code created{email_note}: {invite.claim_code}", "success")
    return redirect(url_for("unit_bp.view", unit_id=unit.id, tab="owners"))
