# app/routes/super_admin/client/capex/capex_delete.py
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
# DELETE
# =========================
@capex_bp.post("/super-admin/clients/<int:client_id>/capex/<uuid:project_id>/delete")
@login_required
def capex_delete(client_id: int, project_id):
    client = Client.query.get_or_404(client_id)
    if not _can_manage(client):
        flash("You don’t have permission to manage this client's CAPEX.", "danger")
        return redirect(url_for("capex_bp.capex_list", client_id=client.id))

    proj = CapexProject.query.filter_by(id=project_id, client_id=client.id).first()
    if not proj:
        flash("Project not found.", "warning")
        return redirect(url_for("capex_bp.capex_list", client_id=client.id))

    db.session.delete(proj)
    db.session.commit()

    # If no projects remain, reset status
    if client.capex_projects.count() == 0:
        client.capex_status = "not_created"
        db.session.commit()

    try:
        recompute_capex_profile(client_id=client.id, actor_user_id=current_user.id)
    except Exception:
        pass

    flash("Project deleted.", "info")
    return redirect(url_for("capex_bp.capex_list", client_id=client.id))