from __future__ import annotations

from app.models.maintenance.maintenance_request import MaintenanceRequest
from app.models.works.work_order import WorkOrder
from app.models.works.work_order_reopen_request import WorkOrderReopenRequest
from app.models.works.work_order_completion import WorkOrderCompletion
from app.services.works.audit_pack_service import build_completion_evidence_pack
from app.services.works.workflow_service import build_work_order_lifecycle_for_audience


def _iso_date(value):
    return value.isoformat() if value else None


def _unit_payload(unit):
    if not unit:
        return None
    return {
        "id": unit.id,
        "label": unit.unit_name or unit.unit_label or unit.unit_number,
        "number": unit.unit_number,
        "block": unit.block_name,
        "client_id": unit.client_id,
        "development": unit.client.name if unit.client else None,
    }


def _member_request_payload(item):
    return {
        "id": item.id,
        "title": item.title,
        "category": item.category or "General",
        "urgency_level": item.urgency_level or "Normal",
        "status": item.status or "Pending",
        "created_at": _iso_date(item.created_at),
        "attachment_url": item.attachment_url,
        "work_order_id": item.work_order.id if item.work_order else None,
        "unit": _unit_payload(item.unit),
    }


def _member_can_view_completion_detail(completion: WorkOrderCompletion | None) -> bool:
    if not completion or completion.access_masked:
        return False

    scope = {
        part.strip().lower()
        for part in (completion.visibility_scope or "").split(",")
        if part.strip()
    }
    return bool(scope.intersection({"member", "members", "resident", "residents", "owner", "owners"}))


def _member_completion_evidence_payload(completion: WorkOrderCompletion | None):
    pack = build_completion_evidence_pack(completion)
    if not pack.get("submitted"):
        return pack

    can_view_detail = _member_can_view_completion_detail(completion)
    return {
        "submitted": True,
        "submitted_at": pack.get("submitted_at"),
        "contractor": pack.get("contractor"),
        "quality_status": pack.get("quality_status"),
        "evidence_reference_type": pack.get("evidence_reference_type"),
        "evidence_reference_present": pack.get("evidence_reference_present"),
        "attachments_count": pack.get("attachments_count", 0),
        "notes_available": pack.get("notes_present"),
        "notes_excerpt": pack.get("notes_excerpt") if can_view_detail else None,
        "evidence_reference": pack.get("evidence_reference") if can_view_detail else None,
        "detail_visible": can_view_detail,
        "member_review_hint": (
            "Completion details are available for your review."
            if can_view_detail
            else "Completion evidence is recorded and will be reviewed by the management team."
        ),
    }


def _member_work_order_payload(item):
    return {
        "id": item.id,
        "reference": f"WO-{item.id}",
        "title": item.title or f"Work Order #{item.id}",
        "status": item.status or "Open",
        "created_at": _iso_date(item.created_at),
        "unit": _unit_payload(item.unit),
        "feedback_required": (item.status or "").lower() == "completion submitted" and not item.feedback,
        "feedback_sent": bool(item.feedback),
        "completion_evidence": _member_completion_evidence_payload(item.completion),
        "feedback": {
            "rating": item.feedback.overall_rating if item.feedback else None,
            "comments": item.feedback.comments if item.feedback else None,
            "evidence_reference": item.feedback.evidence_reference if item.feedback else None,
            "evidence_submitted": bool(item.feedback and item.feedback.evidence_reference),
        },
    }


def _member_reopen_payload(item):
    return {
        "id": item.id,
        "work_order_id": item.work_order_id,
        "status": item.status or "Pending",
        "reason": item.reason,
        "additional_details": item.additional_details,
        "evidence_reference": item.evidence_reference,
        "evidence_submitted": bool(item.evidence_reference),
        "created_at": _iso_date(item.created_at),
        "unit": _unit_payload(item.unit),
    }


def build_member_works_context(member, memberships):
    unit_ids = tuple(link.unit_id for link in memberships if link.unit_id)
    empty_context = {
        "member_requests": [],
        "open_work_orders": [],
        "closed_work_orders": [],
        "reopen_requests": [],
        "feedback_needed_work_orders": [],
        "member_attention_queues": [],
        "member_next_actions": [],
        "lifecycle_by_work_order": {},
        "completion_evidence_by_work_order": {},
    }
    if not member or not unit_ids:
        return empty_context

    member_requests = (
        MaintenanceRequest.query
        .filter(
            MaintenanceRequest.member_id == member.id,
            MaintenanceRequest.unit_id.in_(unit_ids),
        )
        .order_by(MaintenanceRequest.created_at.desc())
        .all()
    )
    work_orders = (
        WorkOrder.query
        .filter(WorkOrder.unit_id.in_(unit_ids))
        .order_by(WorkOrder.created_at.desc())
        .all()
    )
    reopen_requests = (
        WorkOrderReopenRequest.query
        .filter(
            WorkOrderReopenRequest.unit_id.in_(unit_ids),
            WorkOrderReopenRequest.requested_by_member_id == member.id,
        )
        .order_by(WorkOrderReopenRequest.created_at.desc())
        .all()
    )

    open_request_statuses = {"pending", "open", "triage", "in progress", "converted"}
    open_member_requests = [
        item for item in member_requests
        if (item.status or "Pending").lower() in open_request_statuses
    ]
    open_work_orders = [
        item for item in work_orders
        if (item.status or "").lower() not in {"closed", "completed", "resolved", "cancelled"}
    ]
    closed_work_orders = [
        item for item in work_orders
        if (item.status or "").lower() in {"closed", "completed", "resolved"}
    ]
    feedback_needed_work_orders = [
        item for item in open_work_orders
        if (item.status or "").lower() == "completion submitted" and not item.feedback
    ]
    pending_reopen_requests = [
        item for item in reopen_requests
        if (item.status or "").lower() == "pending"
    ]
    member_attention_queues = [
        {
            "label": "Feedback Needed",
            "count": len(feedback_needed_work_orders),
            "anchor": "open-work-orders",
            "tone": "warning",
            "summary": "Contractor completion is waiting for your review.",
            "next_action": "Review contractor completion and add feedback.",
            "priority_rank": 5,
        },
        {
            "label": "Reopen Pending",
            "count": len(pending_reopen_requests),
            "anchor": "reopen-requests",
            "tone": "danger",
            "summary": "Reopen requests awaiting PM/Admin review.",
            "next_action": "Track the PM/Admin reopen decision.",
            "priority_rank": 4,
        },
        {
            "label": "Open Requests",
            "count": len(open_member_requests),
            "anchor": "my-requests",
            "tone": "primary",
            "summary": "Requests submitted through Members Logix.",
            "next_action": "Track your submitted maintenance requests.",
            "priority_rank": 3,
        },
        {
            "label": "Open Work Orders",
            "count": len(open_work_orders),
            "anchor": "open-work-orders",
            "tone": "info",
            "summary": "Live Works Logix records linked to your unit.",
            "next_action": "Check current Works Logix progress.",
            "priority_rank": 2,
        },
    ]
    member_next_actions = [
        {
            "label": queue["label"],
            "count": queue["count"],
            "anchor": queue["anchor"],
            "tone": queue["tone"],
            "action": queue["next_action"],
            "priority_rank": queue["priority_rank"],
        }
        for queue in member_attention_queues
        if queue["count"] > 0
    ]
    member_next_actions.sort(key=lambda item: (-item["priority_rank"], -item["count"], item["label"]))

    return {
        "member_requests": member_requests,
        "open_work_orders": open_work_orders,
        "closed_work_orders": closed_work_orders,
        "reopen_requests": reopen_requests,
        "feedback_needed_work_orders": feedback_needed_work_orders,
        "member_attention_queues": member_attention_queues,
        "member_next_actions": member_next_actions[:3],
        "lifecycle_by_work_order": {
            item.id: build_work_order_lifecycle_for_audience(item, "member")
            for item in work_orders
        },
        "completion_evidence_by_work_order": {
            item.id: _member_completion_evidence_payload(item.completion)
            for item in work_orders
        },
    }


def member_works_feed_payload(member, memberships, works_context):
    return {
        "context_type": "member_works_queue",
        "member_id": member.id if member else None,
        "linked_units": [
            {
                "membership_id": link.id,
                "role": link.role,
                "unit": _unit_payload(link.unit),
            }
            for link in memberships
        ],
        "next_actions": works_context["member_next_actions"],
        "attention_queues": works_context["member_attention_queues"],
        "requests": [_member_request_payload(item) for item in works_context["member_requests"]],
        "open_work_orders": [_member_work_order_payload(item) for item in works_context["open_work_orders"]],
        "closed_work_orders": [_member_work_order_payload(item) for item in works_context["closed_work_orders"]],
        "reopen_requests": [_member_reopen_payload(item) for item in works_context["reopen_requests"]],
    }
