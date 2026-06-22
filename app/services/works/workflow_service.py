from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import or_

from app.extensions import db
from app.models.client.client import Client
from app.models.contractor.contractor import Contractor
from app.models.contractor.contractor_feedback import ContractorFeedback
from app.models.core.notification import Notification
from app.models.core.role import Role
from app.models.core.user import User
from app.models.maintenance.maintenance_request import MaintenanceRequest
from app.models.members.unit import Unit
from app.models.members.unit_membership import UnitMembership
from app.models.works.work_order import WorkOrder
from app.models.works.work_order_completion import WorkOrderCompletion
from app.models.works.work_order_lifecycle_event import WorkOrderLifecycleEvent
from app.models.works.work_order_reopen_request import WorkOrderReopenRequest
from app.services.gar.context import build_work_order_relevant_history
from app.services.gar import build_works_intelligence_queue
from app.services.works.audit_pack_service import build_completion_evidence_pack


OPEN_WORK_STATUSES = {
    "open",
    "available",
    "accepted",
    "pending",
    "in progress",
    "quote requested",
    "quote submitted",
    "quote approved",
    "returned",
    "returned to creator",
    "completion submitted",
}

CLOSED_WORK_STATUSES = {
    "completed",
    "closed",
    "resolved",
    "cancelled",
}

MEMBER_WORKS_LINK = "/members/works"
CONTRACTOR_WORKS_LINK = "/contractor/work-orders"

MANAGEMENT_NOTIFICATION_ROLES = {
    "Admin",
    "Super Admin",
    "Assistant Manager",
    "Master Assistant",
    "Assistant Lead",
    "Senior Assistant",
}


@dataclass(frozen=True)
class WorksFilters:
    search: str = ""
    client_id: int | None = None
    status: str = ""
    allowed_client_ids: tuple[int, ...] | None = None


@dataclass(frozen=True)
class ContractorWorkFilters:
    search: str = ""
    status: str = ""


def _normalise_status(value: str | None) -> str:
    return (value or "").strip().lower()


def is_open_status(value: str | None) -> bool:
    normalised = _normalise_status(value)
    return not normalised or normalised in OPEN_WORK_STATUSES


def is_closed_status(value: str | None) -> bool:
    return _normalise_status(value) in CLOSED_WORK_STATUSES


def _work_order_company_filter(company_id: int):
    return or_(
        WorkOrder.company_id == company_id,
        WorkOrder.client.has(Client.company_id == company_id),
        WorkOrder.unit.has(Unit.company_id == company_id),
    )


def _maintenance_request_company_filter(company_id: int):
    return or_(
        MaintenanceRequest.unit.has(Unit.company_id == company_id),
        MaintenanceRequest.member.has(company_id=company_id),
    )


def _apply_work_filters(query, filters: WorksFilters):
    if filters.allowed_client_ids is not None:
        query = query.filter(WorkOrder.client_id.in_(filters.allowed_client_ids))

    if filters.client_id:
        query = query.filter(WorkOrder.client_id == filters.client_id)

    if filters.status:
        query = query.filter(WorkOrder.status == filters.status)

    if filters.search:
        term = f"%{filters.search}%"
        query = query.filter(
            or_(
                WorkOrder.title.ilike(term),
                WorkOrder.description.ilike(term),
                WorkOrder.external_reference.ilike(term),
                WorkOrder.unit.has(Unit.unit_label.ilike(term)),
                WorkOrder.unit.has(Unit.unit_number.ilike(term)),
                WorkOrder.client.has(Client.name.ilike(term)),
                WorkOrder.client.has(Client.property_name.ilike(term)),
            )
        )
    return query


def _with_anchor(url: str, anchor: str = "") -> str:
    return f"{url}#{anchor}" if anchor else url


def _work_order_review_link(work_order: WorkOrder, anchor: str = "work-order-review") -> str:
    if work_order.unit_id:
        return _with_anchor(f"/units/{work_order.unit_id}/work-orders/{work_order.id}", anchor)
    return _with_anchor("/super-admin/work-orders", f"work-order-{work_order.id}")


def _works_queue_link_for_user(user: User | None) -> str:
    role_name = (getattr(getattr(user, "role", None), "name", "") or "").strip().lower()
    if role_name in {"assistant", "assistant property manager", "assistant manager", "master assistant", "assistant lead", "senior assistant"}:
        return "/assistant/work-orders"
    if role_name == "property manager":
        return "/pm/work-orders"
    return "/super-admin/work-orders"


def _works_queue_anchor_link_for_user(user: User | None, anchor: str = "") -> str:
    return _with_anchor(_works_queue_link_for_user(user), anchor)


def _works_repeated_returns_link_for_user(user: User | None) -> str:
    role_name = (getattr(getattr(user, "role", None), "name", "") or "").strip().lower()
    if role_name in {"assistant", "assistant property manager", "assistant manager", "master assistant", "assistant lead", "senior assistant"}:
        return "/assistant/work-orders/repeated-returns"
    if role_name == "property manager":
        return "/pm/work-orders/repeated-returns"
    return "/super-admin/work-orders/repeated-returns"


def _contractor_work_order_link(work_order: WorkOrder) -> str:
    return _with_anchor(CONTRACTOR_WORKS_LINK, f"work-order-{work_order.id}")


def _member_work_order_link(work_order: WorkOrder, anchor_prefix: str = "work-order") -> str:
    return _with_anchor(MEMBER_WORKS_LINK, f"{anchor_prefix}-{work_order.id}")


def _work_manager_link_for_type(work_order: WorkOrder, notification_type: str) -> str:
    if notification_type == "works_quality_review":
        return _works_repeated_returns_link_for_user(None)

    anchor_by_type = {
        "works_completion_review": "completion-review",
        "works_member_feedback": "member-feedback",
        "works_reopen_request": "reopen-review",
    }
    return _work_order_review_link(
        work_order,
        anchor=anchor_by_type.get(notification_type, "work-order-review"),
    )


def _actor_label(user_id: int | None, fallback: str = "Works Logix") -> str:
    if not user_id:
        return fallback

    user = User.query.get(user_id)
    if not user:
        return fallback

    role_name = getattr(getattr(user, "role", None), "name", None)
    if role_name:
        return f"{user.full_name} ({role_name})"
    return user.full_name or fallback


def _notification_exists(*, recipient_id: int, notification_type: str, link_url: str, match_data: dict) -> bool:
    existing_notifications = Notification.query.filter_by(
        recipient_id=recipient_id,
        type=notification_type,
        link_url=link_url,
    ).all()
    for item in existing_notifications:
        data = item.extracted_data or {}
        if all(data.get(key) == value for key, value in match_data.items()):
            return True
    return False


def _queue_notification(
    *,
    recipient_id: int | None,
    message: str,
    notification_type: str,
    link_url: str,
    priority_level: str = "Normal",
    suggested_action: str = "",
    extracted_data: dict | None = None,
) -> bool:
    if not recipient_id:
        return False

    match_data = extracted_data or {}
    if _notification_exists(
        recipient_id=recipient_id,
        notification_type=notification_type,
        link_url=link_url,
        match_data=match_data,
    ):
        return False

    db.session.add(
        Notification(
            recipient_id=recipient_id,
            message=message,
            type=notification_type,
            link_url=link_url,
            priority_level=priority_level,
            gar_category="Works Logix",
            suggested_action=suggested_action,
            extracted_data=match_data,
        )
    )
    return True


def record_work_order_lifecycle_event(
    *,
    work_order: WorkOrder,
    event_type: str,
    title: str,
    source_module: str = "Works Logix",
    actor_user_id: int | None = None,
    actor_label: str = "",
    note: str = "",
    status_snapshot: str = "",
    member_id: int | None = None,
    contractor_id: int | None = None,
    event_metadata: dict | None = None,
    occurred_at=None,
) -> WorkOrderLifecycleEvent:
    """Stage a GAR-ready work order lifecycle event without committing."""

    event = WorkOrderLifecycleEvent(
        work_order_id=work_order.id,
        company_id=work_order.company_id,
        client_id=work_order.client_id,
        unit_id=work_order.unit_id,
        contractor_id=contractor_id if contractor_id is not None else work_order.contractor_id,
        member_id=member_id,
        actor_user_id=actor_user_id,
        source_module=source_module,
        event_type=event_type,
        title=title,
        note=note,
        status_snapshot=status_snapshot or work_order.status,
        actor_label=actor_label,
        event_metadata=event_metadata,
        gar_context_reference=f"WorkOrder#{work_order.id}",
        occurred_at=occurred_at or datetime.utcnow(),
    )
    db.session.add(event)
    return event


def _work_manager_recipient_ids(*, client: Client | None, company_id: int | None) -> set[int]:
    recipients: set[int] = set()
    if client:
        recipients.update(
            user_id
            for user_id in (client.assigned_pm_id, client.assigned_assistant_id)
            if user_id
        )

    if company_id:
        management_users = (
            User.query
            .join(Role, User.role_id == Role.id)
            .filter(
                User.company_id == company_id,
                User.is_active.is_(True),
                Role.name.in_(MANAGEMENT_NOTIFICATION_ROLES),
            )
            .all()
        )
        recipients.update(user.id for user in management_users)

    return recipients


def _notify_work_managers(
    *,
    work_order: WorkOrder,
    notification_type: str,
    message: str,
    suggested_action: str,
    priority_level: str = "Normal",
    extra_data: dict | None = None,
) -> int:
    recipient_ids = _work_manager_recipient_ids(
        client=work_order.client,
        company_id=work_order.company_id,
    )
    created = 0
    for recipient_id in recipient_ids:
        recipient = User.query.get(recipient_id)
        link_url = (
            _works_repeated_returns_link_for_user(recipient)
            if notification_type == "works_quality_review"
            else _work_manager_link_for_type(work_order, notification_type)
        )
        extracted_data = {
            "work_order_id": work_order.id,
            "unit_id": work_order.unit_id,
            "client_id": work_order.client_id,
            "action_target": link_url,
        }
        if extra_data:
            extracted_data.update(extra_data)
        created += int(
            _queue_notification(
                recipient_id=recipient_id,
                message=message,
                notification_type=notification_type,
                link_url=link_url,
                priority_level=priority_level,
                suggested_action=suggested_action,
                extracted_data=extracted_data,
            )
        )
    return created


def _notify_contractor_users(
    *,
    work_order: WorkOrder,
    notification_type: str,
    message: str,
    suggested_action: str,
    priority_level: str = "Normal",
) -> int:
    if not work_order.contractor_id:
        return 0

    contractor_users = (
        User.query
        .filter(
            User.contractor_id == work_order.contractor_id,
            User.is_active.is_(True),
        )
        .all()
    )
    created = 0
    action_target = (
        _with_anchor(CONTRACTOR_WORKS_LINK, f"returned-work-order-{work_order.id}")
        if notification_type == "works_returned"
        else _contractor_work_order_link(work_order)
    )
    for user in contractor_users:
        created += int(
            _queue_notification(
                recipient_id=user.id,
                message=message,
                notification_type=notification_type,
                link_url=action_target,
                priority_level=priority_level,
                suggested_action=suggested_action,
                extracted_data={
                    "work_order_id": work_order.id,
                    "unit_id": work_order.unit_id,
                    "client_id": work_order.client_id,
                    "contractor_id": work_order.contractor_id,
                    "action_target": action_target,
                },
            )
        )
    return created


def _notify_linked_members_of_completion(work_order: WorkOrder) -> int:
    if not work_order.unit_id:
        return 0

    links = (
        UnitMembership.query
        .filter(
            UnitMembership.unit_id == work_order.unit_id,
            UnitMembership.is_current.is_(True),
            UnitMembership.role.in_(("owner", "resident", "tenant")),
        )
        .all()
    )

    created = 0
    for link in links:
        member = link.member
        if not member or not member.user_id:
            continue

        created += int(
            _queue_notification(
                recipient_id=member.user_id,
                message=f"Work order WO-{work_order.id} has been submitted for completion review. Please add feedback if needed.",
                notification_type="works_completion",
                link_url=_member_work_order_link(work_order),
                priority_level="Normal",
                suggested_action="Review the completion and provide resident feedback.",
                extracted_data={
                    "work_order_id": work_order.id,
                    "unit_id": work_order.unit_id,
                    "client_id": work_order.client_id,
                    "action_target": _member_work_order_link(work_order),
                },
            )
        )

    return created


def _notify_linked_members_of_closure(work_order: WorkOrder) -> int:
    if not work_order.unit_id:
        return 0

    links = (
        UnitMembership.query
        .filter(
            UnitMembership.unit_id == work_order.unit_id,
            UnitMembership.is_current.is_(True),
            UnitMembership.role.in_(("owner", "resident", "tenant")),
        )
        .all()
    )

    created = 0
    for link in links:
        member = link.member
        if not member or not member.user_id:
            continue

        created += int(
            _queue_notification(
                recipient_id=member.user_id,
                message=f"Work order WO-{work_order.id} has been approved and closed by Works Logix.",
                notification_type="works_closed",
                link_url=_member_work_order_link(work_order, "closed-work-order"),
                priority_level="Normal",
                suggested_action="View the completed work order record.",
                extracted_data={
                    "work_order_id": work_order.id,
                    "unit_id": work_order.unit_id,
                    "client_id": work_order.client_id,
                    "action_target": _member_work_order_link(work_order, "closed-work-order"),
                },
            )
        )

    return created


def notify_member_request_submitted(maintenance_request: MaintenanceRequest) -> int:
    unit = maintenance_request.unit
    client = unit.client if unit else None
    recipient_ids = _work_manager_recipient_ids(
        client=client,
        company_id=getattr(unit, "company_id", None),
    )
    recipients = User.query.filter(User.id.in_(recipient_ids)).all() if recipient_ids else []
    created = 0
    for recipient in recipients:
        created += int(
            _queue_notification(
                recipient_id=recipient.id,
                message=f"New Members Logix maintenance request: {maintenance_request.title}.",
                notification_type="works_member_request",
                link_url=_works_queue_anchor_link_for_user(recipient, f"member-request-{maintenance_request.id}"),
                priority_level=maintenance_request.urgency_level or "Normal",
                suggested_action="Triage the member request and convert it to a work order if required.",
                extracted_data={
                    "maintenance_request_id": maintenance_request.id,
                    "unit_id": maintenance_request.unit_id,
                    "client_id": unit.client_id if unit else None,
                    "action_target": _works_queue_anchor_link_for_user(recipient, f"member-request-{maintenance_request.id}"),
                },
            )
        )
    db.session.commit()
    return created


def get_member_request_for_triage(
    *,
    request_id: int,
    company_id: int,
    allowed_client_ids: tuple[int, ...] | None = None,
) -> MaintenanceRequest | None:
    member_request = (
        MaintenanceRequest.query
        .filter(
            MaintenanceRequest.id == request_id,
            _maintenance_request_company_filter(company_id),
        )
        .first()
    )
    if not member_request:
        return None

    if allowed_client_ids is not None:
        client_id = member_request.unit.client_id if member_request.unit else None
        if client_id not in allowed_client_ids:
            return None

    return member_request


def update_member_request_triage(
    *,
    request_id: int,
    company_id: int,
    reviewed_by_id: int | None,
    action: str,
    message: str,
    allowed_client_ids: tuple[int, ...] | None = None,
    access_context: str = "works_triage",
) -> MaintenanceRequest | None:
    """Record a non-conversion triage decision and notify the member."""

    member_request = get_member_request_for_triage(
        request_id=request_id,
        company_id=company_id,
        allowed_client_ids=allowed_client_ids,
    )
    if not member_request or member_request.work_order_id:
        return None

    action_key = (action or "").strip().lower()
    clean_message = (message or "").strip()
    if action_key == "request_info":
        member_request.status = "More Info Requested"
        notification_type = "works_request_more_info"
        suggested_action = "Review the request and provide the extra information requested."
        default_message = "Works Logix needs more information before this can be progressed."
    elif action_key == "reject":
        member_request.status = "Rejected"
        notification_type = "works_request_rejected"
        suggested_action = "Review the decision from Works Logix."
        default_message = "Works Logix has reviewed this request and will not convert it to a work order."
    else:
        return None

    note = clean_message or default_message
    existing_notes = (member_request.internal_notes or "").strip()
    stamped_note = (
        f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} | {access_context} | "
        f"{member_request.status}: {note}"
    )
    member_request.internal_notes = f"{existing_notes}\n{stamped_note}".strip() if existing_notes else stamped_note
    member_request.updated_at = datetime.utcnow()

    recipient_ids = {
        user_id
        for user_id in (
            member_request.requested_by_id,
            getattr(member_request.member, "user_id", None),
        )
        if user_id
    }
    link_url = f"/members/works#member-request-{member_request.id}"
    for recipient_id in recipient_ids:
        _queue_notification(
            recipient_id=recipient_id,
            message=f"{default_message} {note}",
            notification_type=notification_type,
            link_url=link_url,
            priority_level="Normal",
            suggested_action=suggested_action,
            extracted_data={
                "maintenance_request_id": member_request.id,
                "unit_id": member_request.unit_id,
                "client_id": member_request.unit.client_id if member_request.unit else None,
                "reviewed_by_id": reviewed_by_id,
                "action_target": link_url,
                "access_context": access_context,
            },
        )

    db.session.commit()
    return member_request


def notify_work_order_reopen_requested(reopen_request: WorkOrderReopenRequest) -> int:
    work_order = reopen_request.work_order
    if not work_order:
        return 0

    created = _notify_work_managers(
        work_order=work_order,
        notification_type="works_reopen_request",
        message=f"A member/resident requested WO-{work_order.id} be reopened.",
        suggested_action="Review the reopen request and approve or reject it.",
        priority_level="High",
    )
    db.session.commit()
    return created


def build_command_centre(
    company_id: int,
    filters: WorksFilters,
    *,
    include_gar_history: bool = False,
) -> dict:
    """Build the Works Logix Phase 3A dashboard from shared source-of-truth models."""

    clients = (
        Client.query
        .filter_by(company_id=company_id)
        .order_by(Client.name.asc())
        .all()
    )
    if filters.allowed_client_ids is not None:
        allowed_ids = set(filters.allowed_client_ids)
        clients = [client for client in clients if client.id in allowed_ids]

    base_work_query = WorkOrder.query.filter(_work_order_company_filter(company_id))
    scoped_work_query = base_work_query
    if filters.allowed_client_ids is not None:
        scoped_work_query = scoped_work_query.filter(WorkOrder.client_id.in_(filters.allowed_client_ids))
    filtered_work_query = _apply_work_filters(base_work_query, filters)

    all_work_orders = scoped_work_query.order_by(WorkOrder.created_at.desc()).all()
    filtered_work_orders = filtered_work_query.order_by(WorkOrder.created_at.desc()).all()

    open_work_orders = [item for item in filtered_work_orders if is_open_status(item.status)]
    closed_work_orders = [item for item in filtered_work_orders if is_closed_status(item.status)]
    contractors = (
        Contractor.query
        .filter(Contractor.is_active.is_(True))
        .order_by(Contractor.company_name.asc())
        .all()
    )

    open_member_requests = (
        MaintenanceRequest.query
        .filter(_maintenance_request_company_filter(company_id))
        .filter(MaintenanceRequest.work_order_id.is_(None))
        .order_by(MaintenanceRequest.created_at.desc())
        .all()
    )
    open_member_requests = [
        item for item in open_member_requests
        if is_open_status(item.status) and (
            not filters.client_id or (item.unit and item.unit.client_id == filters.client_id)
        ) and (
            filters.allowed_client_ids is None
            or (item.unit and item.unit.client_id in filters.allowed_client_ids)
        )
    ]
    if filters.search:
        needle = filters.search.lower()
        open_member_requests = [
            item for item in open_member_requests
            if needle in (item.title or "").lower()
            or needle in (item.description or "").lower()
            or needle in (item.category or "").lower()
            or (item.unit and needle in (item.unit.unit_label or "").lower())
            or (item.unit and needle in (item.unit.unit_number or "").lower())
            or (item.unit and item.unit.client and needle in (item.unit.client.name or "").lower())
        ]

    pending_reopen_requests = (
        WorkOrderReopenRequest.query
        .join(Unit, WorkOrderReopenRequest.unit_id == Unit.id)
        .filter(
            Unit.company_id == company_id,
            WorkOrderReopenRequest.status == "Pending",
        )
        .order_by(WorkOrderReopenRequest.created_at.desc())
        .all()
    )
    if filters.allowed_client_ids is not None:
        pending_reopen_requests = [
            item for item in pending_reopen_requests
            if item.unit and item.unit.client_id in filters.allowed_client_ids
        ]
    if filters.client_id:
        pending_reopen_requests = [
            item for item in pending_reopen_requests
            if item.unit and item.unit.client_id == filters.client_id
        ]

    open_total = len([item for item in filtered_work_orders if is_open_status(item.status)])
    closed_total = len([item for item in filtered_work_orders if is_closed_status(item.status)])
    unassigned_work_orders = [
        item for item in filtered_work_orders
        if is_open_status(item.status) and not item.contractor_id
    ]
    completion_review_work_orders = [
        item for item in filtered_work_orders
        if _normalise_status(item.status) == "completion submitted"
    ]
    returned_work_orders = [
        item for item in filtered_work_orders
        if _normalise_status(item.status) == "returned"
    ]
    contractor_follow_up_work_orders = [
        item for item in filtered_work_orders
        if _normalise_status(item.status) in {"assigned", "returned"}
    ]
    repeated_return_work_orders = [
        item for item in filtered_work_orders
        if build_work_order_review_cycle(item).get("needs_management_attention")
    ]
    operational_queues = {
        "member_request_triage": {
            "label": "Member Request Triage",
            "count": len(open_member_requests),
            "anchor": "member-requests",
            "tone": "warning",
            "description": "New Members Logix requests waiting to become Works Logix work orders.",
            "next_action": "Review and convert valid requests to work orders.",
            "priority_rank": 4,
        },
        "unassigned_work_orders": {
            "label": "Unassigned Work Orders",
            "count": len(unassigned_work_orders),
            "anchor": "open-work-orders",
            "tone": "danger",
            "description": "Open Works records that still need contractor routing.",
            "next_action": "Assign a contractor or internal owner.",
            "priority_rank": 5,
        },
        "completion_review": {
            "label": "Completion Review",
            "count": len(completion_review_work_orders),
            "anchor": "open-work-orders",
            "tone": "primary",
            "description": "Contractor completions waiting for PM/Admin approval or return.",
            "next_action": "Approve completion or return to the contractor.",
            "priority_rank": 4,
        },
        "reopen_requests": {
            "label": "Reopen Requests",
            "count": len(pending_reopen_requests),
            "anchor": "reopen-requests",
            "tone": "warning",
            "description": "Member or resident reopen requests waiting for a decision.",
            "next_action": "Review evidence and decide whether to reopen.",
            "priority_rank": 5,
        },
        "contractor_follow_up": {
            "label": "Contractor Follow-up",
            "count": len(contractor_follow_up_work_orders),
            "anchor": "open-work-orders",
            "tone": "info",
            "description": "Assigned or returned work orders needing contractor action.",
            "next_action": "Check contractor progress and returned items.",
            "priority_rank": 3,
        },
        "repeated_returns": {
            "label": "Repeated Returns",
            "count": len(repeated_return_work_orders),
            "anchor": "open-work-orders",
            "tone": "danger",
            "description": "Completions returned more than once and needing management review.",
            "next_action": "Review evidence, return reasons and contractor performance signals.",
            "priority_rank": 6,
        },
    }
    next_actions = [
        {
            "key": key,
            "label": queue["label"],
            "count": queue["count"],
            "anchor": queue["anchor"],
            "tone": queue["tone"],
            "action": queue["next_action"],
            "priority_rank": queue["priority_rank"],
        }
        for key, queue in operational_queues.items()
        if queue["count"] > 0
    ]
    next_actions.sort(key=lambda item: (-item["priority_rank"], -item["count"], item["label"]))
    attention_total = sum(queue["count"] for queue in operational_queues.values())
    gar_works_intelligence = build_works_intelligence_queue(
        company_id=company_id,
        work_orders=filtered_work_orders,
        member_requests=open_member_requests,
        reopen_requests=pending_reopen_requests,
        client_id=filters.client_id,
        allowed_client_ids=filters.allowed_client_ids,
    )
    gar_history_by_work_order = {}
    gar_history_work_orders = []
    if include_gar_history:
        visible_history_work_orders = {
            item.id: item
            for item in (
                open_work_orders
                + closed_work_orders[:12]
                + completion_review_work_orders
                + returned_work_orders
                + contractor_follow_up_work_orders
                + repeated_return_work_orders
            )
        }
        gar_history_by_work_order = {
            work_order_id: build_work_order_relevant_history(
                work_order_id,
                audience="admin",
                _work_order=work_order,
            )
            for work_order_id, work_order in visible_history_work_orders.items()
        }
        gar_history_work_orders = [
            {
                "work_order": work_order,
                "history": gar_history_by_work_order.get(work_order_id, {}),
                "related_count": gar_history_by_work_order.get(work_order_id, {}).get("summary", {}).get("related_count", 0),
                "routing_action": gar_history_by_work_order.get(work_order_id, {}).get("routing_recommendation", {}).get("action"),
                "routing_detail": gar_history_by_work_order.get(work_order_id, {}).get("routing_recommendation", {}).get("detail"),
            }
            for work_order_id, work_order in visible_history_work_orders.items()
            if gar_history_by_work_order.get(work_order_id, {}).get("summary", {}).get("related_count", 0) > 0
        ]
        gar_history_work_orders.sort(
            key=lambda item: (
                -item.get("related_count", 0),
                item["work_order"].created_at or datetime.min,
            ),
            reverse=True,
        )

    return {
        "clients": clients,
        "contractors": contractors,
        "status_options": sorted({item.status for item in all_work_orders if item.status}),
        "work_orders": filtered_work_orders,
        "open_work_orders": open_work_orders,
        "closed_work_orders": closed_work_orders,
        "unassigned_work_orders": unassigned_work_orders,
        "completion_review_work_orders": completion_review_work_orders,
        "returned_work_orders": returned_work_orders,
        "contractor_follow_up_work_orders": contractor_follow_up_work_orders,
        "repeated_return_work_orders": repeated_return_work_orders,
        "open_member_requests": open_member_requests,
        "pending_reopen_requests": pending_reopen_requests,
        "operational_queues": operational_queues,
        "next_actions": next_actions[:3],
        "gar_works_intelligence": gar_works_intelligence,
        "gar_history_by_work_order": gar_history_by_work_order,
        "gar_history_work_orders": gar_history_work_orders[:8],
        "return_context_by_work_order": {
            item.id: build_work_order_return_context(item)
            for item in filtered_work_orders
        },
        "review_cycle_by_work_order": {
            item.id: build_work_order_review_cycle(item)
            for item in filtered_work_orders
        },
        "quality_signal_by_work_order": {
            item.id: build_work_order_quality_review_signal(item)
            for item in filtered_work_orders
        },
        "stats": {
            "open_work_orders": open_total,
            "open_member_requests": len(open_member_requests),
            "closed_work_orders": closed_total,
            "total_work_orders": len(filtered_work_orders),
            "pending_reopen_requests": len(pending_reopen_requests),
            "unassigned_work_orders": len(unassigned_work_orders),
            "completion_review": len(completion_review_work_orders),
            "returned_work_orders": len(returned_work_orders),
            "contractor_follow_up": len(contractor_follow_up_work_orders),
            "repeated_returns": len(repeated_return_work_orders),
            "attention_total": attention_total,
        },
    }


def _iso_date(value):
    return value.isoformat() if value else None


def _unit_payload(unit: Unit | None) -> dict | None:
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


def _client_payload(client: Client | None) -> dict | None:
    if not client:
        return None
    return {
        "id": client.id,
        "name": client.name,
        "property_name": client.property_name,
    }


def build_work_order_return_context(work_order: WorkOrder | None) -> dict:
    if not work_order:
        return {"returned": False}

    returned_events = [
        event for event in (work_order.lifecycle_events or [])
        if (event.event_type or "").strip().lower() == "completion_returned"
    ]
    if not returned_events:
        return {"returned": False}

    latest = sorted(
        returned_events,
        key=lambda event: event.occurred_at or event.created_at or datetime.min,
        reverse=True,
    )[0]
    return {
        "returned": True,
        "reason": latest.note or "Returned by Works Logix for further action.",
        "returned_at": _iso_date(latest.occurred_at or latest.created_at),
        "reviewed_by": latest.actor_user.full_name if latest.actor_user else latest.actor_label,
        "source_module": latest.source_module or "Works Logix",
        "event_id": latest.id,
    }


def build_work_order_review_cycle(work_order: WorkOrder | None) -> dict:
    if not work_order:
        return {
            "completion_submissions": 0,
            "completion_returns": 0,
            "resubmissions": 0,
            "needs_management_attention": False,
        }

    lifecycle_events = list(work_order.lifecycle_events or [])
    completion_submissions = [
        event for event in lifecycle_events
        if (event.event_type or "").strip().lower() == "completion_submitted"
    ]
    completion_returns = [
        event for event in lifecycle_events
        if (event.event_type or "").strip().lower() == "completion_returned"
    ]
    return {
        "completion_submissions": len(completion_submissions),
        "completion_returns": len(completion_returns),
        "resubmissions": max(len(completion_submissions) - 1, 0),
        "needs_management_attention": len(completion_returns) >= 2,
    }


def build_work_order_quality_review_signal(work_order: WorkOrder | None) -> dict:
    if not work_order:
        return {
            "contractor_name": None,
            "completion_quality_status": "missing",
            "completion_review_flags": [],
            "member_feedback_received": False,
            "member_feedback_rating": None,
            "member_feedback_evidence": False,
            "has_low_feedback": False,
            "suggested_focus": ["Review the work order evidence pack."],
        }

    completion_evidence = build_completion_evidence_pack(work_order.completion)
    feedback = work_order.feedback
    review_cycle = build_work_order_review_cycle(work_order)
    suggested_focus = []

    if review_cycle.get("completion_returns", 0) >= 2:
        suggested_focus.append("Compare return reasons against contractor resubmissions.")
    if completion_evidence.get("quality_status") in {"missing", "missing_evidence", "needs_review"}:
        suggested_focus.append("Check whether completion evidence is clear enough to support closure.")
    if feedback and feedback.overall_rating and feedback.overall_rating <= 2:
        suggested_focus.append("Review member/resident feedback before closure.")
    if not suggested_focus:
        suggested_focus.append("Review the evidence pack and decide whether to close or return.")

    return {
        "contractor_name": work_order.contractor_company.company_name if work_order.contractor_company else None,
        "completion_quality_status": completion_evidence.get("quality_status"),
        "completion_review_flags": completion_evidence.get("review_flags", []),
        "completion_evidence_type": completion_evidence.get("evidence_reference_type"),
        "member_feedback_received": bool(feedback),
        "member_feedback_rating": feedback.overall_rating if feedback else None,
        "member_feedback_evidence": bool(feedback and feedback.evidence_reference),
        "has_low_feedback": bool(feedback and feedback.overall_rating and feedback.overall_rating <= 2),
        "suggested_focus": suggested_focus,
    }


def _work_order_payload(
    work_order: WorkOrder,
    *,
    include_gar_history: bool = False,
    gar_audience: str = "admin",
) -> dict:
    payload = {
        "id": work_order.id,
        "reference": f"WO-{work_order.id}",
        "title": work_order.title or f"Work Order #{work_order.id}",
        "description": work_order.description,
        "status": work_order.status or "Open",
        "request_type": work_order.request_type,
        "business_type": work_order.business_type,
        "created_at": _iso_date(work_order.created_at),
        "client": _client_payload(work_order.client),
        "unit": _unit_payload(work_order.unit),
        "contractor_id": work_order.contractor_id,
        "completion": {
            "notes": work_order.completion.completion_notes if work_order.completion else None,
            "evidence_reference": work_order.completion.external_reference if work_order.completion else None,
        },
        "completion_evidence": build_completion_evidence_pack(work_order.completion),
        "return_context": build_work_order_return_context(work_order),
        "review_cycle": build_work_order_review_cycle(work_order),
        "quality_review_signal": build_work_order_quality_review_signal(work_order),
        "feedback": {
            "rating": work_order.feedback.overall_rating if work_order.feedback else None,
            "comments": work_order.feedback.comments if work_order.feedback else None,
            "evidence_reference": work_order.feedback.evidence_reference if work_order.feedback else None,
            "evidence_submitted": bool(work_order.feedback and work_order.feedback.evidence_reference),
        },
    }
    if include_gar_history:
        history = build_work_order_relevant_history(
            work_order.id,
            audience=gar_audience,
            _work_order=work_order,
        )
        payload["gar_relevant_history"] = {
            "related_count": history.get("summary", {}).get("related_count", 0),
            "contractor_safe_summary": history.get("contractor_safe_summary"),
            "admin_summary": history.get("admin_summary"),
            "routing_recommendation": history.get("routing_recommendation", {}),
            "latest_reference": history.get("summary", {}).get("latest_reference"),
        }
    return payload


def _member_request_payload(item: MaintenanceRequest) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "description": item.description,
        "category": item.category or "General",
        "urgency_level": item.urgency_level or "Normal",
        "status": item.status or "Pending",
        "created_at": _iso_date(item.created_at),
        "attachment_url": item.attachment_url,
        "unit": _unit_payload(item.unit),
        "work_order_id": item.work_order.id if item.work_order else None,
    }


def _reopen_request_payload(item: WorkOrderReopenRequest) -> dict:
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


def _gar_history_review_payload(item: dict) -> dict:
    work_order = item.get("work_order")
    history = item.get("history", {}) or {}
    return {
        "work_order": _work_order_payload(work_order) if work_order else None,
        "related_count": item.get("related_count", 0),
        "routing_action": item.get("routing_action"),
        "routing_detail": item.get("routing_detail"),
        "latest_reference": history.get("summary", {}).get("latest_reference"),
        "admin_summary": history.get("admin_summary"),
    }


def works_command_centre_payload(
    data: dict,
    filters: WorksFilters,
    *,
    role_context: str,
) -> dict:
    """Create a read-only Works command-centre feed for web/app clients."""

    gar_intelligence = data.get("gar_works_intelligence", {}) or {}
    gar_pattern_memory = gar_intelligence.get("pattern_memory", {}) or {}
    gar_patterns = gar_pattern_memory.get("patterns", {}) or {}
    return {
        "context_type": "works_command_centre",
        "role_context": role_context,
        "filters": {
            "search": filters.search,
            "client_id": filters.client_id,
            "status": filters.status,
            "client_scope": "restricted" if filters.allowed_client_ids is not None else "company",
        },
        "stats": data.get("stats", {}),
        "next_actions": data.get("next_actions", []),
        "operational_queues": data.get("operational_queues", {}),
        "queues": {
            "member_requests": [_member_request_payload(item) for item in data.get("open_member_requests", [])],
            "open_work_orders": [_work_order_payload(item, include_gar_history=True, gar_audience=role_context) for item in data.get("open_work_orders", [])],
            "closed_work_orders": [_work_order_payload(item, include_gar_history=True, gar_audience=role_context) for item in data.get("closed_work_orders", [])],
            "unassigned_work_orders": [_work_order_payload(item, include_gar_history=True, gar_audience=role_context) for item in data.get("unassigned_work_orders", [])],
            "completion_review": [_work_order_payload(item, include_gar_history=True, gar_audience=role_context) for item in data.get("completion_review_work_orders", [])],
            "returned_work_orders": [_work_order_payload(item, include_gar_history=True, gar_audience=role_context) for item in data.get("returned_work_orders", [])],
            "contractor_follow_up": [_work_order_payload(item, include_gar_history=True, gar_audience=role_context) for item in data.get("contractor_follow_up_work_orders", [])],
            "repeated_returns": [_work_order_payload(item, include_gar_history=True, gar_audience=role_context) for item in data.get("repeated_return_work_orders", [])],
            "reopen_requests": [_reopen_request_payload(item) for item in data.get("pending_reopen_requests", [])],
        },
        "gar": {
            "signal_count": gar_intelligence.get("signal_count", 0),
            "attention_total": gar_intelligence.get("attention_total", 0),
            "summary": gar_intelligence.get("summary", {}),
            "cover_context": gar_intelligence.get("cover_context", {}),
            "contractor_quality": gar_patterns.get("contractor_quality", []),
            "history_review": [
                _gar_history_review_payload(item)
                for item in data.get("gar_history_work_orders", [])
            ],
        },
    }


def contractor_work_queue_payload(data: dict, filters: ContractorWorkFilters) -> dict:
    """Create a read-only contractor queue feed for web/app clients."""

    return {
        "context_type": "contractor_work_queue",
        "filters": {
            "search": filters.search,
            "status": filters.status,
        },
        "stats": data.get("stats", {}),
        "next_actions": data.get("next_actions", []),
        "queues": {
            "assigned": [_work_order_payload(item, include_gar_history=True, gar_audience="contractor") for item in data.get("assigned_work_orders", [])],
            "active": [_work_order_payload(item, include_gar_history=True, gar_audience="contractor") for item in data.get("active_work_orders", [])],
            "submitted": [_work_order_payload(item, include_gar_history=True, gar_audience="contractor") for item in data.get("submitted_work_orders", [])],
            "returned": [_work_order_payload(item, include_gar_history=True, gar_audience="contractor") for item in data.get("returned_work_orders", [])],
            "closed": [_work_order_payload(item, include_gar_history=True, gar_audience="contractor") for item in data.get("closed_work_orders", [])],
        },
    }


def convert_member_request_to_work_order(
    *,
    request_id: int,
    company_id: int,
    created_by_id: int,
    allowed_client_ids: tuple[int, ...] | None = None,
    access_context: str = "direct",
) -> WorkOrder | None:
    """Turn a Members Logix maintenance request into a Works Logix work order."""

    member_request = (
        MaintenanceRequest.query
        .filter(
            MaintenanceRequest.id == request_id,
            _maintenance_request_company_filter(company_id),
        )
        .first()
    )
    if not member_request or not member_request.unit:
        return None
    if allowed_client_ids is not None and member_request.unit.client_id not in allowed_client_ids:
        return None

    existing_work_order = WorkOrder.query.filter_by(maintenance_request_id=member_request.id).first()
    if existing_work_order:
        if not member_request.work_order_id:
            member_request.work_order_id = existing_work_order.id
            db.session.commit()
        return existing_work_order

    unit = member_request.unit
    member = member_request.member

    work_order = WorkOrder(
        title=member_request.title,
        description=member_request.description or member_request.title,
        request_type="Work Order",
        business_type=member_request.category,
        status="Open",
        created_at=datetime.utcnow(),
        created_by_id=created_by_id,
        client_id=unit.client_id,
        company_id=company_id,
        unit_id=unit.id,
        maintenance_request_id=member_request.id,
        occupant_name=member.full_name if member else None,
        occupant_phone=getattr(member, "phone", None) if member else None,
        occupant_apartment=unit.unit_label or unit.unit_number,
        privacy_scope="Admin,PM,Contractor",
        attachments_count=member_request.attachments_count or 0,
        parsed_summary=member_request.parsed_summary or member_request.gar_summary,
        extracted_data=member_request.extracted_data,
        ai_source_type="member_request",
        is_ai_processed=member_request.is_ai_processed,
        gar_urgency_score=member_request.ai_priority_score,
        gar_recommended_action=member_request.gar_summary,
    )

    db.session.add(work_order)
    db.session.flush()

    record_work_order_lifecycle_event(
        work_order=work_order,
        event_type="member_request_converted",
        title="Member request converted to work order",
        source_module="Works Logix",
        actor_user_id=created_by_id,
        actor_label=_actor_label(created_by_id),
        note=member_request.title or "Members Logix request converted for triage.",
        status_snapshot=work_order.status,
        member_id=member.id if member else None,
        event_metadata={
            "maintenance_request_id": member_request.id,
            "source_module": "Members Logix",
            "unit_id": unit.id,
            "access_context": access_context,
            "allowed_client_scope": "restricted" if allowed_client_ids is not None else "company",
        },
        occurred_at=work_order.created_at,
    )

    member_request.work_order_id = work_order.id
    member_request.status = "Converted"
    member_request.resolved_at = datetime.utcnow()
    db.session.commit()

    return work_order


def assign_contractor_to_work_order(
    *,
    work_order_id: int,
    company_id: int,
    contractor_id: int,
    allowed_client_ids: tuple[int, ...] | None = None,
    assigned_by_id: int | None = None,
    access_context: str = "direct",
) -> WorkOrder | None:
    query = WorkOrder.query.filter(
        WorkOrder.id == work_order_id,
        _work_order_company_filter(company_id),
    )
    if allowed_client_ids is not None:
        query = query.filter(WorkOrder.client_id.in_(allowed_client_ids))

    work_order = query.first()
    contractor = Contractor.query.filter(
        Contractor.id == contractor_id,
        Contractor.is_active.is_(True),
    ).first()
    if not work_order or not contractor:
        return None

    work_order.contractor_id = contractor.id
    if not work_order.business_type and contractor.business_type:
        work_order.business_type = contractor.business_type
    if _normalise_status(work_order.status) in {"", "open", "pending"}:
        work_order.status = "Assigned"

    record_work_order_lifecycle_event(
        work_order=work_order,
        event_type="contractor_assigned",
        title="Contractor assigned",
        source_module="Works Logix",
        actor_user_id=assigned_by_id,
        actor_label=_actor_label(assigned_by_id, contractor.company_name or "Works Logix"),
        note="Work order routed to the contractor queue.",
        status_snapshot=work_order.status,
        contractor_id=contractor.id,
        event_metadata={
            "contractor_id": contractor.id,
            "contractor_name": contractor.company_name,
            "access_context": access_context,
            "allowed_client_scope": "restricted" if allowed_client_ids is not None else "company",
        },
    )

    _notify_contractor_users(
        work_order=work_order,
        notification_type="works_assignment",
        message=f"Work order WO-{work_order.id} has been assigned to your contractor queue.",
        suggested_action="Review the job details and accept or start the work.",
        priority_level="Normal",
    )

    db.session.commit()
    return work_order


def get_contractor_work_orders(
    contractor_id: int,
    user_id: int | None = None,
    filters: ContractorWorkFilters | None = None,
) -> dict:
    filters = filters or ContractorWorkFilters()
    work_orders = (
        WorkOrder.query
        .filter(WorkOrder.contractor_id == contractor_id)
        .order_by(WorkOrder.created_at.desc())
        .all()
    )
    if user_id:
        user_orders = (
            WorkOrder.query
            .filter(
                or_(
                    WorkOrder.accepted_contractor_id == user_id,
                    WorkOrder.assigned_user_id == user_id,
                )
            )
            .all()
        )
        by_id = {item.id: item for item in work_orders}
        by_id.update({item.id: item for item in user_orders})
        work_orders = sorted(by_id.values(), key=lambda item: item.created_at or datetime.min, reverse=True)

    if filters.search:
        needle = filters.search.lower()
        work_orders = [
            item for item in work_orders
            if needle in (item.title or "").lower()
            or needle in (item.description or "").lower()
            or needle in (item.external_reference or "").lower()
            or needle in (item.business_type or "").lower()
            or needle in (item.request_type or "").lower()
            or (item.client and needle in (item.client.name or "").lower())
            or (item.client and needle in (item.client.property_name or "").lower())
            or (item.unit and needle in (item.unit.unit_label or "").lower())
            or (item.unit and needle in (item.unit.unit_number or "").lower())
        ]

    status_options = sorted({item.status for item in work_orders if item.status})

    if filters.status:
        status_filter = _normalise_status(filters.status)
        work_orders = [
            item for item in work_orders
            if _normalise_status(item.status) == status_filter
        ]

    assigned_statuses = {"assigned", "open", "quote requested", "quote submitted"}
    active_statuses = {"accepted", "in progress"}

    assigned_work_orders = [
        item for item in work_orders
        if _normalise_status(item.status) in assigned_statuses
    ]
    active_work_orders = [
        item for item in work_orders
        if _normalise_status(item.status) in active_statuses
    ]
    closed_work_orders = [
        item for item in work_orders
        if is_closed_status(item.status)
    ]
    submitted_work_orders = [
        item for item in work_orders
        if _normalise_status(item.status) == "completion submitted"
    ]
    returned_work_orders = [
        item for item in work_orders
        if _normalise_status(item.status) == "returned"
    ]
    contractor_next_actions = [
        {
            "label": "Returned Work",
            "count": len(returned_work_orders),
            "anchor": "returned-work",
            "tone": "danger",
            "action": "Review return notes and resubmit completion evidence.",
            "priority_rank": 5,
        },
        {
            "label": "New Assignments",
            "count": len(assigned_work_orders),
            "anchor": "assigned-work",
            "tone": "primary",
            "action": "Accept or start newly assigned work orders.",
            "priority_rank": 4,
        },
        {
            "label": "Active Work",
            "count": len(active_work_orders),
            "anchor": "active-work",
            "tone": "info",
            "action": "Update progress or submit completion evidence.",
            "priority_rank": 3,
        },
    ]
    contractor_next_actions = [
        item for item in contractor_next_actions
        if item["count"] > 0
    ]
    contractor_next_actions.sort(key=lambda item: (-item["priority_rank"], -item["count"], item["label"]))

    return {
        "work_orders": work_orders,
        "assigned_work_orders": assigned_work_orders,
        "active_work_orders": active_work_orders,
        "submitted_work_orders": submitted_work_orders,
        "closed_work_orders": closed_work_orders,
        "returned_work_orders": returned_work_orders,
        "next_actions": contractor_next_actions[:3],
        "status_options": status_options,
        "stats": {
            "assigned": len(assigned_work_orders),
            "active": len(active_work_orders),
            "submitted": len(submitted_work_orders),
            "closed": len(closed_work_orders),
            "returned": len(returned_work_orders),
            "total": len(work_orders),
            "attention_total": len(assigned_work_orders) + len(returned_work_orders),
        },
    }


def contractor_update_work_order(
    *,
    work_order_id: int,
    contractor_id: int,
    user_id: int,
    action: str,
    completion_notes: str = "",
    evidence_reference: str = "",
) -> WorkOrder | None:
    work_order = WorkOrder.query.filter(
        WorkOrder.id == work_order_id,
        WorkOrder.contractor_id == contractor_id,
    ).first()
    if not work_order:
        return None

    if action == "accept":
        work_order.status = "Accepted"
        work_order.accepted_contractor_id = user_id
        record_work_order_lifecycle_event(
            work_order=work_order,
            event_type="contractor_accepted",
            title="Contractor accepted work order",
            source_module="Contractor Logix",
            actor_user_id=user_id,
            actor_label="Contractor",
            note="Contractor accepted the assigned work order.",
            status_snapshot=work_order.status,
        )
    elif action == "reject":
        work_order.status = "Rejected"
        record_work_order_lifecycle_event(
            work_order=work_order,
            event_type="contractor_rejected",
            title="Contractor rejected work order",
            source_module="Contractor Logix",
            actor_user_id=user_id,
            actor_label="Contractor",
            note=completion_notes or "Contractor rejected the assigned work order.",
            status_snapshot=work_order.status,
        )
        _notify_work_managers(
            work_order=work_order,
            notification_type="works_contractor_rejected",
            message=f"Contractor rejected WO-{work_order.id}.",
            suggested_action="Review the contractor reason and reroute the work order if required.",
            priority_level="High",
            extra_data={"contractor_rejection_reason": completion_notes or None},
        )
    elif action == "start":
        work_order.status = "In Progress"
        work_order.accepted_contractor_id = work_order.accepted_contractor_id or user_id
        record_work_order_lifecycle_event(
            work_order=work_order,
            event_type="contractor_started",
            title="Contractor started work",
            source_module="Contractor Logix",
            actor_user_id=user_id,
            actor_label="Contractor",
            note="Contractor marked the work order as in progress.",
            status_snapshot=work_order.status,
        )
    elif action == "complete":
        work_order.status = "Completion Submitted"
        work_order.accepted_contractor_id = work_order.accepted_contractor_id or user_id
        evidence_reference = evidence_reference.strip()
        if work_order.completion:
            work_order.completion.completion_notes = completion_notes or work_order.completion.completion_notes
            if evidence_reference:
                work_order.completion.external_reference = evidence_reference
                work_order.completion.media_uploaded = True
                work_order.completion.attachments_count = max(work_order.completion.attachments_count or 0, 1)
        else:
            db.session.add(
                WorkOrderCompletion(
                    work_order_id=work_order.id,
                    completed_by_id=user_id,
                    contractor_id=contractor_id,
                    completion_notes=completion_notes,
                    external_reference=evidence_reference or None,
                    media_uploaded=bool(evidence_reference),
                    attachments_count=1 if evidence_reference else 0,
                    consent_verified=True,
                    source_system="Contractor Logix",
                )
            )
        record_work_order_lifecycle_event(
            work_order=work_order,
            event_type="completion_submitted",
            title="Completion submitted",
            source_module="Contractor Logix",
            actor_user_id=user_id,
            actor_label="Contractor",
            note=completion_notes or "Contractor submitted completion evidence.",
            status_snapshot=work_order.status,
            event_metadata={
                "evidence_reference": evidence_reference or None,
                "media_uploaded": bool(evidence_reference),
            },
        )
        _notify_linked_members_of_completion(work_order)
        _notify_work_managers(
            work_order=work_order,
            notification_type="works_completion_review",
            message=f"Contractor completion submitted for WO-{work_order.id}.",
            suggested_action="Review contractor evidence, member feedback and approve or return the work.",
            priority_level="High",
        )
    else:
        return None

    db.session.commit()
    return work_order


def submit_member_work_order_feedback(
    *,
    work_order: WorkOrder,
    given_by_id: int,
    rating: float,
    comments: str = "",
    evidence_reference: str = "",
) -> ContractorFeedback | None:
    if not work_order.contractor_id:
        return None

    existing = ContractorFeedback.query.filter_by(
        work_order_id=work_order.id,
        given_by_id=given_by_id,
    ).first()

    if existing:
        existing.overall_rating = rating
        existing.comments = comments
        existing.evidence_reference = evidence_reference or None
        existing.feedback_source = "Members Logix"
        existing.source_system = "Members Logix"
        existing.consent_verified = True
        feedback = existing
    else:
        feedback = ContractorFeedback(
            work_order_id=work_order.id,
            contractor_id=work_order.contractor_id,
            given_by_id=given_by_id,
            overall_rating=rating,
            comments=comments,
            evidence_reference=evidence_reference or None,
            feedback_source="Members Logix",
            source_system="Members Logix",
            consent_verified=True,
            visibility_scope="Admin,PM",
        )
        db.session.add(feedback)

    record_work_order_lifecycle_event(
        work_order=work_order,
        event_type="member_feedback_submitted",
        title="Member / resident feedback submitted",
        source_module="Members Logix",
        actor_user_id=given_by_id,
        note=comments or f"Rating: {rating}/5",
        status_snapshot=work_order.status,
        event_metadata={
            "rating": rating,
            "evidence_reference": evidence_reference or None,
            "evidence_submitted": bool(evidence_reference),
        },
    )

    _notify_work_managers(
        work_order=work_order,
        notification_type="works_member_feedback",
        message=f"Member/resident feedback was submitted for WO-{work_order.id}.",
        suggested_action="Review the feedback before closing or returning the work order.",
        priority_level="Normal",
    )

    db.session.commit()
    return feedback


def review_contractor_completion(
    *,
    work_order_id: int,
    company_id: int,
    reviewed_by_user_id: int,
    decision: str,
    review_notes: str = "",
) -> WorkOrder | None:
    work_order = WorkOrder.query.filter(
        WorkOrder.id == work_order_id,
        _work_order_company_filter(company_id),
    ).first()
    if not work_order or _normalise_status(work_order.status) != "completion submitted":
        return None

    if decision == "approve":
        work_order.status = "Closed"
        if work_order.completion:
            work_order.completion.confirmed_by_admin_id = reviewed_by_user_id
            work_order.completion.gar_explanation = review_notes or work_order.completion.gar_explanation
        record_work_order_lifecycle_event(
            work_order=work_order,
            event_type="completion_approved",
            title="Completion approved and closed",
            source_module="Works Logix",
            actor_user_id=reviewed_by_user_id,
            note=review_notes or "PM/Admin approved the contractor completion.",
            status_snapshot=work_order.status,
        )
        _notify_linked_members_of_closure(work_order)
    elif decision == "return":
        prior_return_count = WorkOrderLifecycleEvent.query.filter_by(
            work_order_id=work_order.id,
            event_type="completion_returned",
        ).count()
        return_count = prior_return_count + 1
        work_order.status = "Returned"
        work_order.gar_explanation = review_notes or work_order.gar_explanation
        record_work_order_lifecycle_event(
            work_order=work_order,
            event_type="completion_returned",
            title="Returned to contractor",
            source_module="Works Logix",
            actor_user_id=reviewed_by_user_id,
            note=review_notes or "PM/Admin returned the work order for further action.",
            status_snapshot=work_order.status,
        )
        _notify_contractor_users(
            work_order=work_order,
            notification_type="works_returned",
            message=f"WO-{work_order.id} has been returned by Works Logix for further action.",
            suggested_action="Review the return notes and resubmit completion when resolved.",
            priority_level="High",
        )
        if return_count >= 2:
            _notify_work_managers(
                work_order=work_order,
                notification_type="works_quality_review",
                message=f"WO-{work_order.id} has been returned {return_count} times and needs quality review.",
                suggested_action="Open the repeated returns queue and review the evidence pack.",
                priority_level="High",
                extra_data={
                    "return_count": return_count,
                    "gar_signal": "repeated_completion_returns",
                },
            )
    else:
        return None

    db.session.commit()
    return work_order


def build_work_order_lifecycle(work_order: WorkOrder) -> list[dict]:
    """Build a review-friendly lifecycle from the linked source records."""

    events: list[dict] = []

    def add_event(
        *,
        title: str,
        source: str,
        occurred_at=None,
        actor: str = "",
        note: str = "",
        status: str = "",
        access_context: str = "",
    ) -> None:
        events.append(
            {
                "title": title,
                "source": source,
                "occurred_at": occurred_at,
                "actor": actor or "-",
                "note": note or "-",
                "status": status or "",
                "access_context": access_context or "",
            }
        )

    if work_order.maintenance_request:
        request = work_order.maintenance_request
        add_event(
            title="Member request submitted",
            source="Members Logix",
            occurred_at=request.created_at,
            actor=request.member.full_name if request.member else "Member / Resident",
            note=request.title or request.description,
            status=request.status or "Submitted",
        )

    add_event(
        title="Work order created",
        source="Works Logix",
        occurred_at=work_order.created_at,
        actor=work_order.created_by.full_name if work_order.created_by else "Works Logix",
        note=work_order.title or work_order.description,
        status="Created",
    )

    if work_order.contractor_id:
        add_event(
            title="Contractor assigned",
            source="Works Logix",
            occurred_at=None,
            actor=work_order.contractor_company.company_name if work_order.contractor_company else "Contractor",
            note="Contractor queue notified through Contractor Logix.",
            status="Assigned",
        )

    if work_order.accepted_contractor_id:
        add_event(
            title="Contractor accepted / started",
            source="Contractor Logix",
            occurred_at=None,
            actor=work_order.accepted_contractor.full_name if work_order.accepted_contractor else "Contractor",
            note="Contractor has engaged with the assigned work order.",
            status=work_order.status or "Accepted",
        )

    if work_order.completion:
        completion = work_order.completion
        add_event(
            title="Completion submitted",
            source="Contractor Logix",
            occurred_at=completion.completed_at,
            actor=completion.completed_by.full_name if completion.completed_by else "Contractor",
            note=completion.completion_notes or "Completion submitted for PM/Admin review.",
            status="Completion Submitted",
        )

    if work_order.feedback:
        feedback = work_order.feedback
        add_event(
            title="Member / resident feedback submitted",
            source=feedback.feedback_source or "Members Logix",
            occurred_at=feedback.created_at,
            actor=feedback.given_by.full_name if feedback.given_by else "Member / Resident",
            note=feedback.comments or f"Rating: {feedback.overall_rating}/5",
            status="Feedback",
        )

    for reopen_request in sorted(
        work_order.reopen_requests or [],
        key=lambda item: item.created_at or datetime.min,
    ):
        add_event(
            title="Reopen requested",
            source="Members Logix",
            occurred_at=reopen_request.created_at,
            actor=reopen_request.requested_by_member.full_name if reopen_request.requested_by_member else "Member / Resident",
            note=reopen_request.reason or reopen_request.additional_details,
            status=reopen_request.status or "Pending",
        )
        if reopen_request.reviewed_at:
            add_event(
                title=f"Reopen request {reopen_request.status.lower()}",
                source="Works Logix",
                occurred_at=reopen_request.reviewed_at,
                actor=reopen_request.reviewed_by.full_name if reopen_request.reviewed_by else "Works Logix",
                note=reopen_request.review_notes or "-",
                status=reopen_request.status or "Reviewed",
            )

    if is_closed_status(work_order.status):
        add_event(
            title="Work order closed",
            source="Works Logix",
            occurred_at=None,
            actor=work_order.completion.confirmed_by_admin.full_name if work_order.completion and work_order.completion.confirmed_by_admin else "Works Logix",
            note="Completion approved and member/resident closure notification issued.",
            status=work_order.status or "Closed",
        )
    elif _normalise_status(work_order.status) == "returned":
        add_event(
            title="Returned to contractor",
            source="Works Logix",
            occurred_at=None,
            actor="Works Logix",
            note=work_order.gar_explanation or "Further contractor action is required.",
            status="Returned",
        )

    stored_events = [
        item.as_timeline_event()
        for item in WorkOrderLifecycleEvent.query
        .filter_by(work_order_id=work_order.id)
        .order_by(WorkOrderLifecycleEvent.occurred_at.asc(), WorkOrderLifecycleEvent.id.asc())
        .all()
    ]
    if stored_events:
        stored_titles = {item["title"] for item in stored_events}
        events = stored_events + [
            item for item in events
            if item["title"] not in stored_titles
        ]

    return sorted(
        events,
        key=lambda event: (
            event["occurred_at"] is None,
            event["occurred_at"] or datetime.max,
        ),
    )


def build_work_order_lifecycle_for_audience(work_order: WorkOrder, audience: str = "admin") -> list[dict]:
    """Return the shared lifecycle trail with light audience-specific redaction."""

    audience_key = (audience or "admin").strip().lower()
    events = build_work_order_lifecycle(work_order)
    if audience_key in {"admin", "pm", "assistant", "super_admin"}:
        return events

    visible_events: list[dict] = []
    for event in events:
        item = dict(event)
        source = (item.get("source") or "").lower()
        if audience_key == "member":
            if source == "contractor logix":
                item["actor"] = "Contractor"
            if source == "works logix" and item.get("event_type") in {"contractor_assigned"}:
                item["note"] = "The work order has been routed for action."
        elif audience_key == "contractor":
            if source == "members logix":
                item["actor"] = "Member / Resident"
            if item.get("event_type") in {"member_feedback_submitted"}:
                item["note"] = "Feedback has been shared with Works Logix for review."
        visible_events.append(item)
    return visible_events


def _event_type_from_timeline_event(event: dict) -> str:
    title = (event.get("title") or "").strip().lower()
    source = (event.get("source") or "").strip().lower()
    if title == "member request submitted":
        return "member_request_submitted"
    if title == "work order created":
        return "work_order_created"
    if title == "contractor assigned":
        return "contractor_assigned"
    if title == "contractor accepted / started":
        return "contractor_engaged"
    if title == "completion submitted":
        return "completion_submitted"
    if title == "member / resident feedback submitted":
        return "member_feedback_submitted"
    if title == "reopen requested":
        return "reopen_requested"
    if title.startswith("reopen request"):
        return "reopen_reviewed"
    if title == "work order closed":
        return "work_order_closed"
    if title == "returned to contractor":
        return "completion_returned"
    return "_".join(part for part in [source.replace(" ", "_"), title.replace(" ", "_")] if part)[:80]


def _lifecycle_event_exists(work_order_id: int, event_type: str, title: str, note: str, occurred_at) -> bool:
    query = WorkOrderLifecycleEvent.query.filter_by(
        work_order_id=work_order_id,
        event_type=event_type,
        title=title,
    )
    if occurred_at:
        query = query.filter(WorkOrderLifecycleEvent.occurred_at == occurred_at)
    else:
        query = query.filter(WorkOrderLifecycleEvent.note == note)
    return query.first() is not None


def backfill_work_order_lifecycle_events(work_order: WorkOrder) -> int:
    """Stage missing persisted lifecycle events for an existing work order."""

    created = 0
    for event in build_work_order_lifecycle(work_order):
        if event.get("persisted"):
            continue

        event_type = _event_type_from_timeline_event(event)
        title = event.get("title") or "Lifecycle event"
        note = event.get("note") or "-"
        occurred_at = event.get("occurred_at")
        if _lifecycle_event_exists(work_order.id, event_type, title, note, occurred_at):
            continue

        db.session.add(
            WorkOrderLifecycleEvent(
                work_order_id=work_order.id,
                company_id=work_order.company_id,
                client_id=work_order.client_id,
                unit_id=work_order.unit_id,
                contractor_id=work_order.contractor_id,
                source_module=event.get("source") or "Works Logix",
                event_type=event_type,
                title=title,
                note=note,
                status_snapshot=event.get("status") or work_order.status,
                actor_label=event.get("actor") or "-",
                event_metadata={"backfilled": True},
                gar_context_reference=f"WorkOrder#{work_order.id}",
                occurred_at=occurred_at or datetime.utcnow(),
            )
        )
        created += 1
    return created
