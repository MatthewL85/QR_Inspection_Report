# app/routes/client/key_info/views.py
from __future__ import annotations

import os
import secrets
from pathlib import Path

from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import select, desc, asc
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.client.key_info import ClientKeyInfo, ClientKeyInfoChange
from app.services.key_info import (
    can_propose as can_propose_fn,
    can_approve as can_approve_fn,
    create_proposal,
    apply_change,
    reject_change,
)
from . import bp
from .utils import require_org_roles, load_client_or_404, safe_int_list


def _role_loose_match(user, allowed: set[str]) -> bool:
    raw = (getattr(user, "role", "") or "").strip().lower()
    normalized = raw.replace("_", " ")
    return normalized in {r.lower().replace("_", " ") for r in allowed}


def _can_propose_relaxed(user) -> bool:
    if can_propose_fn(user):
        return True
    return _role_loose_match(
        user,
        {"Admin", "Property Manager", "Financial Controller", "Super Admin",
         "superadmin", "property_manager", "financial_controller"},
    )


def _can_approve_relaxed(user) -> bool:
    if can_approve_fn(user):
        return True
    return _role_loose_match(user, {"Property Manager", "Super Admin", "superadmin", "property_manager"})


# ─────────────────────────────────────────────────────────────────────────────
# List + New/Update UI
# ─────────────────────────────────────────────────────────────────────────────
@bp.route("/clients/<int:client_id>/key-info/", methods=["GET"])
@bp.route("/clients/<int:client_id>/key-info", methods=["GET"])
@login_required
def list_sections(client_id: int):
    require_org_roles()
    client = load_client_or_404(client_id)

    sections = db.session.execute(
        select(ClientKeyInfo)
        .where(ClientKeyInfo.client_id == client_id, ClientKeyInfo.status == "active")
        .order_by(asc(ClientKeyInfo.title))
    ).scalars().all()

    pending = db.session.execute(
        select(ClientKeyInfoChange)
        .where(ClientKeyInfoChange.client_id == client_id, ClientKeyInfoChange.status == "pending")
        .order_by(desc(ClientKeyInfoChange.submitted_at))
    ).scalars().all()

    # Contractors (optional)
    try:
        from app.models.contractor import Contractor
        contractors = db.session.execute(
            select(Contractor).order_by(asc(Contractor.company_name))
        ).scalars().all()
    except Exception:
        contractors = []

    return render_template(
        "clients/key_info/list.html",
        client=client,
        sections=sections,
        pending=pending,
        contractors=contractors,
        can_propose=_can_propose_relaxed(current_user),
        can_approve=_can_approve_relaxed(current_user),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Create / Edit proposals
# ─────────────────────────────────────────────────────────────────────────────
@bp.route("/clients/<int:client_id>/key-info/propose", methods=["POST"])
@login_required
def propose_change(client_id: int):
    require_org_roles()
    load_client_or_404(client_id)

    key_info_id = request.form.get("key_info_id")
    title = (request.form.get("title") or "").strip()
    content = request.form.get("content") or ""
    contractor_ids = safe_int_list(request.form.getlist("contractor_ids"))

    ki = None
    if key_info_id:
        ki = db.session.get(ClientKeyInfo, int(key_info_id))
        if not ki or ki.client_id != client_id:
            flash("Section not found for this client.", "danger")
            return redirect(url_for("client_key_info.list_sections", client_id=client_id))

    try:
        create_proposal(
            client_id=client_id,
            submitted_by=current_user,
            title=title,
            content=content,  # HTML or plaintext; TEXT column supports tables/images/video embeds (by URL)
            key_info=ki,
            proposed_contractor_ids=contractor_ids,
            pro_attested_by_contractor=bool(request.form.get("pro_attested_by_contractor")),
            pro_attestation_note=(request.form.get("pro_attestation_note") or "").strip() or None,
        )
        flash("Change submitted for approval.", "success")
    except PermissionError as e:
        flash(str(e), "danger")

    return redirect(url_for("client_key_info.list_sections", client_id=client_id))


# ─────────────────────────────────────────────────────────────────────────────
# Approve / Reject
# ─────────────────────────────────────────────────────────────────────────────
@bp.route("/clients/<int:client_id>/key-info/changes/<int:change_id>/approve", methods=["POST"])
@login_required
def approve_change_route(client_id: int, change_id: int):
    require_org_roles()
    load_client_or_404(client_id)

    ch = db.session.get(ClientKeyInfoChange, change_id)
    if not ch or ch.client_id != client_id:
        flash("Change not found.", "danger")
        return redirect(url_for("client_key_info.list_sections", client_id=client_id))

    if not _can_approve_relaxed(current_user):
        flash("Only Property Manager or Super Admin can approve.", "danger")
        return redirect(url_for("client_key_info.list_sections", client_id=client_id))

    apply_change(ch, current_user, reason=request.form.get("reason") or None)
    flash("Change approved and published.", "success")
    return redirect(url_for("client_key_info.list_sections", client_id=client_id))


@bp.route("/clients/<int:client_id>/key-info/changes/<int:change_id>/reject", methods=["POST"])
@login_required
def reject_change_route(client_id: int, change_id: int):
    require_org_roles()
    load_client_or_404(client_id)

    ch = db.session.get(ClientKeyInfoChange, change_id)
    if not ch or ch.client_id != client_id:
        flash("Change not found.", "danger")
        return redirect(url_for("client_key_info.list_sections", client_id=client_id))

    if not _can_approve_relaxed(current_user):
        flash("Only Property Manager or Super Admin can reject.", "danger")
        return redirect(url_for("client_key_info.list_sections", client_id=client_id))

    reject_change(ch, current_user, reason=request.form.get("reason") or None)
    flash("Change rejected.", "warning")
    return redirect(url_for("client_key_info.list_sections", client_id=client_id))


# ─────────────────────────────────────────────────────────────────────────────
# TinyMCE asset upload (images / videos)
# Returns: {"location": "<public URL>"} as TinyMCE expects
# ─────────────────────────────────────────────────────────────────────────────
ALLOWED_IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_MEDIA_EXTS = {"mp4", "webm", "ogg"}


@bp.route("/clients/<int:client_id>/key-info/upload", methods=["POST"])
@login_required
def upload_asset(client_id: int):
    require_org_roles()
    load_client_or_404(client_id)

    f = request.files.get("file")
    if not f or f.filename == "":
        return jsonify({"error": "No file provided"}), 400

    filename = secure_filename(f.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in (ALLOWED_IMAGE_EXTS | ALLOWED_MEDIA_EXTS):
        return jsonify({"error": "Unsupported file type"}), 400

    # Save under /static/uploads/key_info/<client_id>/
    base_upload = current_app.config.get("UPLOAD_FOLDER") or os.path.join(current_app.static_folder, "uploads")
    target_dir = Path(base_upload) / "key_info" / str(client_id)
    target_dir.mkdir(parents=True, exist_ok=True)

    new_name = f"{secrets.token_hex(10)}.{ext}"
    path = target_dir / new_name
    f.save(path.as_posix())

    # Public URL
    rel_from_static = Path("uploads") / "key_info" / str(client_id) / new_name
    public_url = url_for("static", filename=str(rel_from_static).replace("\\", "/"))

    return jsonify({"location": public_url}), 200
