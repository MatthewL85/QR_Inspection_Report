# app/controllers/unit_controller.py

from typing import Any, Optional

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.extensions import db
from app.models.client.client import Client
from app.models.members.member import Member
from app.models.members.unit import Unit
from app.services.unit_service import UnitService


# ------------------------------------------------------
# Resolve active company (Super Admin safe)
# ------------------------------------------------------
def _get_company_id_for_current_user() -> Optional[int]:
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        company_id = getattr(current_user, "active_company_id", None)
    return company_id


# ------------------------------------------------------
# LIST (Material Dashboard)
# ------------------------------------------------------
@login_required
def list_units() -> Any:
    company_id = _get_company_id_for_current_user()
    if not company_id:
        abort(403)

    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=25, type=int)

    client_id = request.args.get("client_id", type=int)
    search = request.args.get("search", type=str)
    block_name = request.args.get("block_name", type=str)
    core_name = request.args.get("core_name", type=str)
    only_active = request.args.get("only_active", "1") in ("1", "true", "True", True)

    pagination = UnitService.list_units_for_company(
        company_id=company_id,
        page=page,
        per_page=per_page,
        client_id=client_id,
        search=search,
        block_name=block_name,
        core_name=core_name,
        only_active=only_active,
    )

    clients = (
        Client.query.filter_by(company_id=company_id)
        .order_by(Client.name.asc())
        .all()
    )

    return render_template(
        "units/list.html",
        pagination=pagination,
        units=pagination.items,
        clients=clients,
        selected_client_id=client_id,
        search=search or "",
        block_name=block_name or "",
        core_name=core_name or "",
        only_active=only_active,
    )


# ------------------------------------------------------
# ENTERPRISE UNIT DETAIL VIEW
# ------------------------------------------------------
@login_required
def unit_detail_view(unit_id: int):
    company_id = _get_company_id_for_current_user()
    if not company_id:
        abort(403)

    data = UnitService.get_unit(unit_id)
    if not data or data["unit"].company_id != company_id:
        abort(404)

    return render_template(
        "units/detail.html",
        unit=data["unit"],
        client=data["client"],
        company=data["company"],
        block=data["block"],
        core=data["core"],
        owners=data["owner_entities"],
        owner_links=data["owners"],
        residents=data["resident_entities"],
        resident_links=data["residents"],
        invoices=data["invoices"],
        work_orders=data["work_orders"],
        documents=data["documents"],
        child_units=data["child_units"],
    )


# ------------------------------------------------------
# CREATE UNIT (Now includes Owners/Residents Phase 1)
# ------------------------------------------------------
@login_required
def create_unit() -> Any:
    company_id = _get_company_id_for_current_user()
    if not company_id:
        abort(403)

    clients = (
        Client.query.filter_by(company_id=company_id)
        .order_by(Client.name.asc())
        .all()
    )

    members = Member.query.filter_by(company_id=company_id).order_by(Member.last_name.asc()).all()

    possible_parents = (
        Unit.query.filter_by(company_id=company_id)
        .order_by(Unit.block_name.asc(), Unit.core_name.asc(), Unit.unit_label.asc())
        .all()
    )

    if request.method == "POST":
        form = request.form

        unit = UnitService.create_unit(form, company_id=company_id)
        if not unit:
            flash("Unable to create unit. Please check the form fields.", "danger")
            return redirect(url_for("unit.create_unit"))

        owner_ids = request.form.getlist("owner_member_ids[]")
        resident_ids = request.form.getlist("resident_member_ids[]")

        UnitService.assign_owners(unit, owner_ids)
        UnitService.assign_residents(unit, resident_ids)

        db.session.commit()

        flash("Unit created successfully.", "success")
        return redirect(url_for("unit.unit_detail_view", unit_id=unit.id))

    return render_template(
        "units/form.html",
        mode="create",
        unit=None,
        clients=clients,
        members=members,
        possible_parents=possible_parents,
        owners_assigned=[],
        residents_assigned=[],
    )


# ------------------------------------------------------
# EDIT UNIT (Now includes Owners/Residents Phase 1)
# ------------------------------------------------------
@login_required
def edit_unit(unit_id: int) -> Any:
    company_id = _get_company_id_for_current_user()
    if not company_id:
        abort(403)

    unit = Unit.query.filter_by(id=unit_id, company_id=company_id).first_or_404()

    clients = (
        Client.query.filter_by(company_id=company_id)
        .order_by(Client.name.asc())
        .all()
    )

    members = Member.query.filter_by(company_id=company_id).order_by(Member.last_name.asc()).all()

    possible_parents = (
        Unit.query.filter(
            Unit.company_id == company_id,
            Unit.id != unit.id,
        )
        .order_by(Unit.block_name.asc(), Unit.core_name.asc(), Unit.unit_label.asc())
        .all()
    )

    owners_assigned = [uo.member_id for uo in unit.owners]
    residents_assigned = [ur.member_id for ur in unit.residents]

    if request.method == "POST":
        UnitService.update_unit(unit.id, request.form, company_id=company_id)

        owner_ids = request.form.getlist("owner_member_ids[]")
        resident_ids = request.form.getlist("resident_member_ids[]")

        UnitService.assign_owners(unit, owner_ids)
        UnitService.assign_residents(unit, resident_ids)

        db.session.commit()

        flash("Unit updated successfully.", "success")
        return redirect(url_for("unit.unit_detail_view", unit_id=unit.id))

    return render_template(
        "units/form.html",
        mode="edit",
        unit=unit,
        clients=clients,
        members=members,
        possible_parents=possible_parents,
        owners_assigned=owners_assigned,
        residents_assigned=residents_assigned,
    )


# ------------------------------------------------------
# DELETE
# ------------------------------------------------------
@login_required
def delete_unit(unit_id: int) -> Any:
    company_id = _get_company_id_for_current_user()
    if not company_id:
        abort(403)

    success = UnitService.delete_unit(unit_id=unit_id, company_id=company_id)

    flash("Unit deleted." if success else "Unit not found.", "success" if success else "warning")

    return redirect(url_for("unit.list_units"))
