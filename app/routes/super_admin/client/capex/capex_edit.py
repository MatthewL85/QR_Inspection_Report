# app/routes/super_admin/client/capex/capex_edit.py
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
# EDIT
# =========================
@capex_bp.route("/super-admin/clients/<int:client_id>/capex/<uuid:project_id>/edit", methods=["GET", "POST"])
@login_required
def capex_edit(client_id: int, project_id):
    client = Client.query.get_or_404(client_id)
    if not _can_manage(client):
        flash("You don’t have permission to manage this client's CAPEX.", "danger")
        return redirect(url_for("capex_bp.capex_list", client_id=client.id))

    # Ensure UUID instance
    if not isinstance(project_id, UUID):
        project_id = UUID(str(project_id))

    proj = CapexProject.query.filter_by(id=project_id, client_id=client.id).first_or_404()
    form = CapexProjectForm(obj=proj)
    form.id.data = str(proj.id)

    if request.method == "POST" and form.validate_on_submit():
        proj.name = form.name.data
        proj.target_year = form.target_year.data
        proj.cost = form.cost.data
        proj.priority = form.priority.data
        proj.funding = form.funding.data
        proj.status = form.status.data
        proj.notes = form.notes.data
        proj.updated_by = current_user.id

        db.session.commit()

        try:
            recompute_capex_profile(client_id=client.id, actor_user_id=current_user.id)
        except Exception:
            pass

        flash("CAPEX project updated.", "success")
        return redirect(url_for("capex_bp.capex_list", client_id=client.id))

    # GET: render edit screen (or reuse list template with an edit form section)
    return render_template("super_admin/client/capex_edit.html", client=client, form=form, project=proj)