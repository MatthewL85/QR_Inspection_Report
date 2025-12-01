# app/routes/contractor/key_info.py
from __future__ import annotations
from typing import Optional

from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from sqlalchemy import select

from app.extensions import db
from app.models.client.client import Client
from app.models.client.key_info import ClientKeyInfo
from app.models.client.key_info import ClientKeyInfoShare

bp_contractor = Blueprint(
    "contractor_key_info",
    __name__,
    url_prefix="/contractor/clients/<int:client_id>/key-info",
)

CONTRACTOR_ROLES = {"Contractor", "Admin Contractor"}  # adjust to your roles

def _current_contractor_id() -> Optional[int]:
    """
    Tries common attributes to resolve the contractor id for the logged-in user.
    Adapt if your user model uses a different field.
    """
    for attr in ("contractor_id", "company_id", "contractorId"):
        cid = getattr(current_user, attr, None)
        if cid:
            try:
                return int(cid)
            except Exception:
                pass
    # If your auth stores contractor id elsewhere, handle here.
    return None

@bp_contractor.get("/")
@login_required
def list_shared(client_id: int):
    if getattr(current_user, "role", None) not in CONTRACTOR_ROLES:
        abort(403)
    contractor_id = _current_contractor_id()
    if not contractor_id:
        abort(403)

    client = db.session.get(Client, client_id) or abort(404)

    q = (
        select(ClientKeyInfo)
        .join(ClientKeyInfoShare, ClientKeyInfoShare.key_info_id == ClientKeyInfo.id)
        .where(
            ClientKeyInfo.client_id == client_id,
            ClientKeyInfoShare.contractor_id == contractor_id,
            ClientKeyInfo.status == "active",
        )
        .order_by(ClientKeyInfo.title.asc())
    )
    sections = db.session.execute(q).scalars().all()

    return render_template(
        "contractor/key_info/list.html",
        client=client,
        sections=sections,
    )
