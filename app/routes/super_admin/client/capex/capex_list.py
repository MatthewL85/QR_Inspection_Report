# app/routes/super_admin/client/capex/capex_list.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import case
from uuid import UUID

from app.models import db, Client
from app.models.capex import CapexProject, CapexProjectDependency
from app.forms.capex import CapexProjectForm
from app.services.capex.capex_service import recompute_capex_profile

capex_bp = Blueprint("capex_bp", __name__)

# ---- Permission helper: Super Admin OR assigned PM (same company) ----
def _can_manage(client: Client) -> bool:
    role = getattr(current_user, "role_name", None)
    return (
        role == "Super Admin"
        or (role == "Property Manager"
            and client.assigned_pm_id == current_user.id
            and current_user.company_id == client.company_id)
    )

# =========================
# LIST
# =========================
@capex_bp.get("/super-admin/clients/<int:client_id>/capex/")
@login_required
def capex_list(client_id: int):
    client = Client.query.get_or_404(client_id)
    if not _can_manage(client):
        flash("You don’t have permission to manage this client's CAPEX.", "danger")
        return redirect(url_for("super_admin.manage_clients"))

    # Priority order: High > Medium > Low
    priority_order = case(
        (CapexProject.priority == "High", 1),
        (CapexProject.priority == "Medium", 2),
        else_=3
    )

    projects = (CapexProject.query
                .filter_by(client_id=client.id)
                .order_by(CapexProject.target_year.asc().nulls_last(), priority_order.asc())
                .all())

    form = CapexProjectForm()  # empty form for quick-add modal if you like
    return render_template("super_admin/client/capex_list.html",
                           client=client, projects=projects, form=form)