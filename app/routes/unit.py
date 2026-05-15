# app/routes/unit.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

# Controllers / Services
from app.controllers.unit_controller import unit_detail_view
from app.services.unit_service import UnitService

# Blueprint
unit_bp = Blueprint(
    "unit_bp",
    __name__,
    url_prefix="/units"
)


# ------------------------------------------------------
# 🔵 UNIT LIST PAGE
# ------------------------------------------------------
@unit_bp.route("/", methods=["GET"], endpoint="list")
@login_required
def list_units_route():
    """
    Full enterprise-grade Unit List Page with:
    - Search
    - Block filter
    - Core filter
    - Pagination
    """
    search = request.args.get("search")
    block = request.args.get("block")
    core = request.args.get("core")
    page = request.args.get("page", 1, type=int)

    results = UnitService.list_units(
        search=search,
        block=block,
        core=core,
        page=page,
        per_page=25,
    )

    return render_template(
        "units/index.html",
        units=results.items,
        pagination=results,
        search=search,
        selected_block=block,
        selected_core=core,
        blocks=UnitService.get_all_blocks(),
        cores=UnitService.get_all_cores(),
    )


# ------------------------------------------------------
# 🔵 UNIT DETAIL PAGE
# ------------------------------------------------------
@unit_bp.route("/<int:unit_id>", methods=["GET"], endpoint="view")
@login_required
def view_unit_route(unit_id):
    return unit_detail_view(unit_id)


# ------------------------------------------------------
# 🔵 CREATE UNIT (UI COMING NEXT)
# ------------------------------------------------------
@unit_bp.route("/create", methods=["GET"], endpoint="create")
@login_required
def create_unit_form():
    """
    Show create-unit form (Enterprise Version)
    """
    return render_template(
        "units/forms/create_unit.html",
        blocks=UnitService.get_all_blocks(),
        cores=UnitService.get_all_cores(),
        owners=UnitService.get_all_members(),
    )


@unit_bp.route("/create", methods=["POST"], endpoint="create_submit")
@login_required
def create_unit_submit():
    """
    Handles new unit creation.
    """
    try:
        unit = UnitService.create_unit(request.form)
        flash("Unit created successfully.", "success")
        return redirect(url_for("unit_bp.view", unit_id=unit.id))
    except Exception as e:
        flash(f"Error creating unit: {str(e)}", "danger")
        return redirect(url_for("unit_bp.create"))


# ------------------------------------------------------
# 🔵 EDIT UNIT (UI COMING NEXT)
# ------------------------------------------------------
@unit_bp.route("/<int:unit_id>/edit", methods=["GET"], endpoint="edit")
@login_required
def edit_unit_form(unit_id):
    unit_data = UnitService.get_unit(unit_id)

    return render_template(
        "units/forms/edit_unit.html",
        unit=unit_data["unit"],
        blocks=UnitService.get_all_blocks(),
        cores=UnitService.get_all_cores(),
        owners=UnitService.get_all_members(),
    )


@unit_bp.route("/<int:unit_id>/edit", methods=["POST"], endpoint="edit_submit")
@login_required
def edit_unit_submit(unit_id):
    try:
        UnitService.update_unit(unit_id, request.form)
        flash("Unit updated successfully.", "success")
        return redirect(url_for("unit_bp.view", unit_id=unit_id))
    except Exception as e:
        flash(f"Error updating unit: {str(e)}", "danger")
        return redirect(url_for("unit_bp.edit", unit_id=unit_id))
