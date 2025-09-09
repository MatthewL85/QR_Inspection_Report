# app/routes/super_admin/client/capex/capex_add.py
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
# ADD
# =========================
@capex_bp.post("/super-admin/clients/<int:client_id>/capex/add")
@login_required
def capex_add(client_id: int):
    client = Client.query.get_or_404(client_id)
    if not _can_manage(client):
        flash("You don’t have permission to manage this client's CAPEX.", "danger")
        return redirect(url_for("capex_bp.capex_list", client_id=client.id))

    form = CapexProjectForm()
    if not form.validate_on_submit():
        # Re-render list with errors
        return capex_list(client_id)

    proj = CapexProject(
        client_id=client.id,
        name=form.name.data,
        target_year=form.target_year.data,
        cost=form.cost.data,
        priority=form.priority.data,
        funding=form.funding.data,
        status=form.status.data,
        notes=form.notes.data,
        created_by=current_user.id,
        updated_by=current_user.id
    )

    db.session.add(proj)
    # bump status if necessary
    if client.capex_status == "not_created":
        client.capex_status = "in_progress"
    db.session.commit()

    # refresh snapshot (don’t block UX on errors)
    try:
        recompute_capex_profile(client_id=client.id, actor_user_id=current_user.id)
    except Exception:
        pass

    flash("CAPEX project added.", "success")
    return redirect(url_for("capex_bp.capex_list", client_id=client.id))
