# app/routes/client/key_info/propose.py
from __future__ import annotations
from flask import request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models.client.key_info import ClientKeyInfoChange
from app.routes.client.key_info import bp
from .utils import require_org_roles, load_client_or_404, safe_int_list
from app.services.key_info import can_propose

@bp.post("/propose", endpoint="propose_change")
@login_required
def propose_change(client_id: int):
    require_org_roles()
    if not can_propose(current_user):
        abort(403)

    client = load_client_or_404(client_id)

    key_info_id_raw = request.form.get("key_info_id")
    key_info_id = int(key_info_id_raw) if key_info_id_raw else None

    proposed_title = (request.form.get("title") or "").strip()
    proposed_content = request.form.get("content") or ""

    proposed_contractor_ids = safe_int_list(request.form.getlist("contractor_ids"))

    change = ClientKeyInfoChange(
        client_id=client.id,
        key_info_id=key_info_id,
        proposed_title=proposed_title,
        proposed_content=proposed_content,
        proposed_contractor_ids=proposed_contractor_ids,
        submitted_by_id=current_user.id,
    )
    db.session.add(change)
    db.session.commit()

    flash("Change submitted for approval.", "info")
    return redirect(url_for("client_key_info.list_sections", client_id=client.id))
