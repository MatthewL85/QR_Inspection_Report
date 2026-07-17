from __future__ import annotations

import os
from datetime import datetime
from uuid import uuid4

from flask import Blueprint, current_app, flash, redirect, jsonify, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.maintenance.maintenance_request import MaintenanceRequest
from app.models.members.member import Member
from app.models.members.unit_membership import UnitMembership
from app.models.works.work_order import WorkOrder
from app.models.works.work_order_reopen_request import WorkOrderReopenRequest
from app.services.gar import attach_gar_capability_readiness, build_gar_inquiry_response, build_member_role_digest
from app.services.members.works_context import build_member_works_context, member_works_feed_payload
from app.services.unit_access_service import claim_unit_access
from app.services.work_order_reopen_service import WorkOrderReopenService
from app.services.works.workflow_service import (
    notify_member_request_submitted,
    notify_work_order_reopen_requested,
    submit_member_work_order_feedback,
)


members_bp = Blueprint("members", __name__, url_prefix="/members")

MEMBER_REQUEST_UPLOAD_EXTENSIONS = {
    "jpg", "jpeg", "png", "gif", "webp", "heic",
    "mp4", "mov", "webm", "avi", "m4v",
    "pdf", "doc", "docx",
}


def _current_member():
    return Member.query.filter_by(user_id=getattr(current_user, "id", None)).first()


def _current_member_links(member):
    if not member:
        return []

    return (
        UnitMembership.query
        .filter_by(member_id=member.id, is_current=True)
        .order_by(UnitMembership.role.asc())
        .all()
    )


def _accessible_unit_ids(member):
    return tuple(
        link.unit_id for link in _current_member_links(member)
        if link.unit_id
    )


def _works_anchor(anchor: str) -> str:
    return url_for("members.works", _anchor=anchor)


def _member_request_for_current_member(request_id: int, member: Member | None) -> MaintenanceRequest | None:
    if not member:
        return None

    return MaintenanceRequest.query.filter_by(
        id=request_id,
        member_id=member.id,
    ).first()


def _latest_member_visible_request_note(maintenance_request: MaintenanceRequest) -> str | None:
    notes = [
        line.strip()
        for line in (maintenance_request.internal_notes or "").splitlines()
        if line.strip()
    ]
    if not notes:
        return None

    latest_note = notes[-1]
    if ": " in latest_note:
        return latest_note.split(": ", 1)[-1].strip()
    return latest_note


def _save_member_request_upload(file_storage, request_id: int) -> str | None:
    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename)
    if not filename or "." not in filename:
        return None

    extension = filename.rsplit(".", 1)[-1].lower()
    if extension not in MEMBER_REQUEST_UPLOAD_EXTENSIONS:
        return None

    upload_dir = os.path.join(current_app.static_folder, "uploads", "member_requests", str(request_id))
    os.makedirs(upload_dir, exist_ok=True)
    stored_name = f"{uuid4().hex}.{extension}"
    file_storage.save(os.path.join(upload_dir, stored_name))
    return f"/static/uploads/member_requests/{request_id}/{stored_name}"


def _save_member_request_uploads(file_storages, request_id: int) -> tuple[list[str], list[str]]:
    uploaded_references: list[str] = []
    unsupported_filenames: list[str] = []
    for file_storage in file_storages or []:
        if not file_storage or not file_storage.filename:
            continue
        uploaded_reference = _save_member_request_upload(file_storage, request_id)
        if uploaded_reference:
            uploaded_references.append(uploaded_reference)
        else:
            unsupported_filenames.append(file_storage.filename)
    return uploaded_references, unsupported_filenames


def _merge_evidence_links(*groups) -> list[str]:
    links: list[str] = []
    for group in groups:
        if not group:
            continue
        values = group if isinstance(group, list) else [group]
        for value in values:
            value = (value or "").strip()
            if value and value not in links:
                links.append(value)
    return links


@members_bp.route("/dashboard", endpoint="dashboard")
@login_required
def dashboard():
    member = _current_member()
    memberships = _current_member_links(member)
    works_context = build_member_works_context(member, memberships)
    gar_question = (request.args.get("gar_question") or "").strip()
    gar_inquiry_response = None
    if gar_question:
        gar_inquiry_response = build_gar_inquiry_response(
            gar_question,
            role_context="member",
            company_id=getattr(current_user, "company_id", None),
            user_id=getattr(current_user, "id", None),
            execute_source_query=True,
        )

    return render_template(
        "members/dashboard.html",
        member=member,
        memberships=memberships,
        member_next_actions=works_context["member_next_actions"],
        gar_question=gar_question,
        gar_inquiry_response=gar_inquiry_response,
    )


@members_bp.route("/access/claim", methods=["POST"], endpoint="claim_unit_access")
@login_required
def claim_access():
    result = claim_unit_access(request.form.get("claim_code") or "", current_user)
    flash(result.message, "success" if result.ok else "warning")
    return redirect(url_for("members.dashboard"))


@members_bp.route("/works", endpoint="works")
@login_required
def works():
    member = _current_member()
    memberships = _current_member_links(member)
    works_context = build_member_works_context(member, memberships)
    gar_question = (request.args.get("gar_question") or "").strip()
    gar_inquiry_response = None
    if gar_question:
        gar_inquiry_response = build_gar_inquiry_response(
            gar_question,
            role_context="member",
            company_id=getattr(current_user, "company_id", None),
            user_id=getattr(current_user, "id", None),
            execute_source_query=True,
        )

    return render_template(
        "members/works.html",
        member=member,
        memberships=memberships,
        gar_question=gar_question,
        gar_inquiry_response=gar_inquiry_response,
        **works_context,
    )


@members_bp.route("/works/feed.json", endpoint="works_feed")
@login_required
def works_feed():
    member = _current_member()
    memberships = _current_member_links(member)
    works_context = build_member_works_context(member, memberships)

    return jsonify(member_works_feed_payload(member, memberships, works_context))


@members_bp.route("/gar/feed.json", endpoint="gar_feed")
@login_required
def gar_feed():
    member = _current_member()
    memberships = _current_member_links(member)
    works_context = build_member_works_context(member, memberships)

    payload = build_member_role_digest(member, memberships, works_context)
    role_context = payload.get("role_context") or "member"
    return jsonify(attach_gar_capability_readiness(
        payload,
        role_context=role_context,
        question=(request.args.get("question") or "").strip() or None,
    ))


@members_bp.route("/gar/inquiry.json", endpoint="gar_inquiry")
@login_required
def gar_inquiry():
    return jsonify(build_gar_inquiry_response(
        (request.args.get("question") or request.args.get("gar_question") or "").strip(),
        role_context="member",
        company_id=getattr(current_user, "company_id", None),
        user_id=getattr(current_user, "id", None),
        execute_source_query=True,
    ))


@members_bp.route("/works/requests", methods=["POST"], endpoint="create_maintenance_request")
@login_required
def create_maintenance_request():
    member = _current_member()
    unit_ids = _accessible_unit_ids(member)
    unit_id = request.form.get("unit_id", type=int)

    if not member or not unit_id or unit_id not in unit_ids:
        flash("Select one of your linked units before submitting a request.", "warning")
        return redirect(_works_anchor("submit-request"))

    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    if not title or not description:
        flash("Please add a clear title and description for the maintenance request.", "warning")
        return redirect(_works_anchor("submit-request"))

    media_reference = (request.form.get("media_reference") or "").strip()
    media_files = request.files.getlist("media_file")
    maintenance_request = MaintenanceRequest(
        member_id=member.id,
        unit_id=unit_id,
        requested_by_id=getattr(current_user, "id", None),
        title=title,
        description=description,
        category=(request.form.get("category") or "").strip() or None,
        urgency_level=request.form.get("urgency_level") or "Normal",
        request_channel="Members Logix",
        source_system="Members Logix",
        visibility_scope="Admin,PM",
        consent_verified=True,
        status="Pending",
        attachment_url=media_reference or None,
        attachments_count=1 if media_reference else 0,
        media_uploaded=bool(media_reference),
        doc_links=[media_reference] if media_reference else None,
        photo_links=[media_reference] if media_reference else None,
    )
    db.session.add(maintenance_request)
    db.session.flush()

    uploaded_references, unsupported_filenames = _save_member_request_uploads(media_files, maintenance_request.id)
    if unsupported_filenames:
        db.session.rollback()
        flash("That file type is not supported for maintenance request evidence.", "warning")
        return redirect(_works_anchor("submit-request"))
    evidence_links = _merge_evidence_links(media_reference, uploaded_references)
    if evidence_links:
        maintenance_request.attachment_url = evidence_links[0]
        maintenance_request.attachments_count = len(evidence_links)
        maintenance_request.media_uploaded = bool(uploaded_references)
        maintenance_request.doc_links = evidence_links
        maintenance_request.photo_links = evidence_links

    db.session.commit()
    notify_member_request_submitted(maintenance_request)

    flash("Maintenance request submitted. Works Logix can now triage it.", "success")
    return redirect(_works_anchor("my-requests"))


@members_bp.route("/works/requests/<int:request_id>", endpoint="maintenance_request_detail")
@login_required
def maintenance_request_detail(request_id):
    member = _current_member()
    maintenance_request = _member_request_for_current_member(request_id, member)
    if not maintenance_request:
        flash("That request is not available from your Members Logix account.", "warning")
        return redirect(_works_anchor("my-requests"))

    return render_template(
        "members/maintenance_request_detail.html",
        member=member,
        maintenance_request=maintenance_request,
        works_reply=_latest_member_visible_request_note(maintenance_request),
    )


@members_bp.route("/works/requests/<int:request_id>/respond", methods=["POST"], endpoint="respond_to_maintenance_request")
@login_required
def respond_to_maintenance_request(request_id):
    member = _current_member()
    if not member:
        flash("Your member profile is not linked yet.", "warning")
        return redirect(_works_anchor("my-requests"))

    maintenance_request = _member_request_for_current_member(request_id, member)
    if not maintenance_request or maintenance_request.work_order_id:
        flash("That request is not available for update.", "warning")
        return redirect(_works_anchor("my-requests"))

    if (maintenance_request.status or "").strip().lower() != "more info requested":
        flash("This request is not waiting for more information.", "info")
        return redirect(url_for("members.maintenance_request_detail", request_id=request_id))

    response = (request.form.get("response") or "").strip()
    media_reference = (request.form.get("media_reference") or "").strip()
    media_files = request.files.getlist("media_file")
    uploaded_references, unsupported_filenames = _save_member_request_uploads(media_files, maintenance_request.id)
    if unsupported_filenames:
        flash("That file type is not supported for maintenance request evidence.", "warning")
        return redirect(url_for("members.maintenance_request_detail", request_id=request_id))
    if not response and not media_reference and not uploaded_references:
        flash("Please add the extra information or attach evidence before sending.", "warning")
        return redirect(url_for("members.maintenance_request_detail", request_id=request_id))

    if response:
        maintenance_request.description = (
            f"{maintenance_request.description or ''}\n\n"
            f"Member response {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}: {response}"
        ).strip()
    evidence_links = _merge_evidence_links(
        maintenance_request.doc_links,
        media_reference,
        uploaded_references,
    )
    if evidence_links:
        maintenance_request.attachment_url = evidence_links[0]
        maintenance_request.attachments_count = len(evidence_links)
        maintenance_request.media_uploaded = bool(uploaded_references) or bool(maintenance_request.media_uploaded)
        maintenance_request.doc_links = evidence_links
        maintenance_request.photo_links = evidence_links

    maintenance_request.status = "Pending"
    maintenance_request.updated_at = datetime.utcnow()
    db.session.commit()
    notify_member_request_submitted(maintenance_request)

    flash("Additional information sent. Works Logix can now review the request again.", "success")
    return redirect(url_for("members.maintenance_request_detail", request_id=request_id))


@members_bp.route("/works/<int:work_order_id>/reopen", methods=["POST"], endpoint="request_reopen")
@login_required
def request_reopen(work_order_id):
    member = _current_member()
    unit_ids = _accessible_unit_ids(member)
    work_order = WorkOrder.query.filter(
        WorkOrder.id == work_order_id,
        WorkOrder.unit_id.in_(unit_ids),
    ).first()

    if not member or not work_order:
        flash("That work order is not available from your linked units.", "warning")
        return redirect(_works_anchor("closed-work-orders"))

    reason = (request.form.get("reason") or "").strip()
    additional_details = (request.form.get("additional_details") or "").strip()
    evidence_reference = (request.form.get("evidence_reference") or "").strip()
    if not reason:
        flash("Please add a reason for requesting the work order to be reopened.", "warning")
        return redirect(_works_anchor("closed-work-orders"))

    existing_pending = WorkOrderReopenRequest.query.filter_by(
        work_order_id=work_order.id,
        requested_by_member_id=member.id,
        status="Pending",
    ).first()
    if existing_pending:
        flash("A reopen request is already pending for this work order.", "info")
        return redirect(_works_anchor("reopen-requests"))

    reopen_request = WorkOrderReopenService.create_request(
        work_order=work_order,
        reason=reason,
        additional_details=additional_details,
        evidence_reference=evidence_reference,
        requested_by_member_id=member.id,
    )
    notify_work_order_reopen_requested(reopen_request)
    flash("Reopen request sent to Works Logix for review.", "success")
    return redirect(_works_anchor("reopen-requests"))


@members_bp.route("/works/<int:work_order_id>/feedback", methods=["POST"], endpoint="submit_work_order_feedback")
@login_required
def submit_work_order_feedback(work_order_id):
    member = _current_member()
    unit_ids = _accessible_unit_ids(member)
    work_order = WorkOrder.query.filter(
        WorkOrder.id == work_order_id,
        WorkOrder.unit_id.in_(unit_ids),
    ).first()

    if not member or not work_order:
        flash("That work order is not available from your linked units.", "warning")
        return redirect(_works_anchor("open-work-orders"))

    if (work_order.status or "").lower() not in {"completion submitted", "closed", "completed", "resolved"}:
        flash("Feedback is available after the contractor submits completion.", "warning")
        return redirect(_works_anchor("open-work-orders"))

    try:
        rating = float(request.form.get("rating") or 0)
    except ValueError:
        rating = 0
    if rating < 1 or rating > 5:
        flash("Please choose a feedback rating from 1 to 5.", "warning")
        return redirect(_works_anchor("open-work-orders"))

    feedback = submit_member_work_order_feedback(
        work_order=work_order,
        given_by_id=current_user.id,
        rating=rating,
        comments=(request.form.get("comments") or "").strip(),
        evidence_reference=(request.form.get("evidence_reference") or "").strip(),
    )
    if not feedback:
        flash("Feedback could not be saved because no contractor is linked to this work order.", "warning")
        return redirect(_works_anchor("open-work-orders"))

    flash("Thank you. Your feedback is now visible to Works Logix for review.", "success")
    return redirect(_works_anchor("open-work-orders"))
