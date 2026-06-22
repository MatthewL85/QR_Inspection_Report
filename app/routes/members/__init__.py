from __future__ import annotations

from flask import Blueprint, flash, redirect, jsonify, render_template, request, url_for
from flask_login import current_user, login_required

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
    db.session.commit()
    notify_member_request_submitted(maintenance_request)

    flash("Maintenance request submitted. Works Logix can now triage it.", "success")
    return redirect(_works_anchor("my-requests"))


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
