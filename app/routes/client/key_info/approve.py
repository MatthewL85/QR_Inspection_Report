# app/routes/client/key_info/approve.py
from __future__ import annotations
from flask import request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models.client.key_info import ClientKeyInfoChange
from app.routes.client.key_info import bp
from .utils import require_org_roles
from app.services.key_info import can_approve, apply_change, reject_change

@bp.post("/changes/<int:change_id>/approve", endpoint="approve_change_route")
@login_required
def approve_change_route(client_id: int, change_id: int):
    require_org_roles()
    change = db.session.get(ClientKeyInfoChange, change_id)
    if not change or change.client_id != client_id:
        abort(404)
    if not can_approve(current_user):
        abort(403)

    reason = (request.form.get("reason") or "Approved").strip()
    apply_change(change, current_user, reason=reason)
    flash("Change approved and published.", "success")
    return redirect(url_for("client_key_info.list_sections", client_id=client_id))

@bp.post("/changes/<int:change_id>/reject", endpoint="reject_change_route")
@login_required
def reject_change_route(client_id: int, change_id: int):
    require_org_roles()
    change = db.session.get(ClientKeyInfoChange, change_id)
    if not change or change.client_id != client_id:
        abort(404)
    if not can_approve(current_user):
        abort(403)

    reason = (request.form.get("reason") or "Rejected").strip()
    reject_change(change, current_user, reason=reason)
    flash("Change rejected.", "warning")
    return redirect(url_for("client_key_info.list_sections", client_id=client_id))
