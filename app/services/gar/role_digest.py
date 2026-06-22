"""Role-aware GAR feed helpers for user-facing modules."""

from __future__ import annotations

from typing import Any


def _as_count(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _unit_label(unit) -> str:
    if not unit:
        return "-"

    block = getattr(unit, "block_name", None) or (
        unit.block.name if getattr(unit, "block", None) else None
    )
    core = getattr(unit, "core_name", None) or (
        unit.core.name if getattr(unit, "core", None) else None
    )
    unit_number = (
        getattr(unit, "unit_number", None)
        or getattr(unit, "unit_label", None)
        or f"Unit #{getattr(unit, 'id', '-')}"
    )
    if block:
        return f"{block} / {unit_number}"
    if core:
        return f"{core} / {unit_number}"
    return unit_number


def build_member_role_digest(member, memberships: list, works_context: dict[str, Any]) -> dict[str, Any]:
    """Build the GAR digest a member/resident can safely see."""

    unit_ids = [link.unit_id for link in memberships if getattr(link, "unit_id", None)]
    roles = sorted({(link.role or "member").lower() for link in memberships})
    is_resident_only = bool(roles) and set(roles).issubset({"resident", "tenant"})
    role_context = "resident" if is_resident_only else "member"
    member_actions = works_context.get("member_next_actions", [])
    linked_units = [
        {
            "unit_id": link.unit_id,
            "unit": _unit_label(getattr(link, "unit", None)),
            "role": link.role,
            "is_primary": bool(getattr(link, "is_primary", False)),
        }
        for link in memberships
    ]
    summary = {
        "linked_units": len(unit_ids),
        "member_requests": len(works_context.get("member_requests", []) or []),
        "open_work_orders": len(works_context.get("open_work_orders", []) or []),
        "closed_work_orders": len(works_context.get("closed_work_orders", []) or []),
        "reopen_requests": len(works_context.get("reopen_requests", []) or []),
        "feedback_needed": len(works_context.get("feedback_needed_work_orders", []) or []),
        "priority_action_count": len(member_actions),
    }

    return {
        "context_type": "gar_role_digest",
        "role_context": role_context,
        "visibility_scope": {
            "member_id": getattr(member, "id", None),
            "user_id": getattr(member, "user_id", None),
            "unit_ids": unit_ids,
            "roles": roles,
        },
        "summary": summary,
        "priority_actions": member_actions,
        "linked_units": linked_units,
        "works_attention": works_context.get("member_attention_queues", []),
        "source_references": [
            {
                "model": "Member",
                "record_id": getattr(member, "id", None),
                "fields": ["user_id", "company_id", "client_id", "is_owner", "is_director"],
            },
            {
                "model": "UnitMembership",
                "record_id": unit_ids,
                "fields": ["unit_id", "member_id", "role", "is_current", "is_primary"],
            },
            {
                "model": "MaintenanceRequest",
                "record_id": "unit-scoped",
                "fields": ["unit_id", "member_id", "status", "urgency", "created_at"],
            },
            {
                "model": "WorkOrder",
                "record_id": "unit-scoped",
                "fields": ["unit_id", "status", "contractor_id", "completion_submitted_at"],
            },
        ],
    }


def build_contractor_role_digest(user, work_data: dict[str, Any]) -> dict[str, Any]:
    """Build the GAR digest a contractor can safely see."""

    stats = work_data.get("stats", {}) or {}
    next_actions = work_data.get("next_actions", []) or []
    return {
        "context_type": "gar_role_digest",
        "role_context": "contractor",
        "visibility_scope": {
            "user_id": getattr(user, "id", None),
            "contractor_id": getattr(user, "contractor_id", None),
        },
        "summary": {
            "assigned": _as_count(stats.get("assigned")),
            "active": _as_count(stats.get("active")),
            "submitted": _as_count(stats.get("submitted")),
            "returned": _as_count(stats.get("returned")),
            "closed": _as_count(stats.get("closed")),
            "total": _as_count(stats.get("total")),
            "attention_total": _as_count(stats.get("attention_total")),
            "priority_action_count": len(next_actions),
        },
        "priority_actions": next_actions,
        "works_attention": {
            "assigned": len(work_data.get("assigned_work_orders", []) or []),
            "active": len(work_data.get("active_work_orders", []) or []),
            "submitted": len(work_data.get("submitted_work_orders", []) or []),
            "returned": len(work_data.get("returned_work_orders", []) or []),
        },
        "source_references": [
            {
                "model": "User",
                "record_id": getattr(user, "id", None),
                "fields": ["role", "company_id", "contractor_id", "is_active"],
            },
            {
                "model": "WorkOrder",
                "record_id": "contractor-scoped",
                "fields": ["contractor_id", "assigned_user_id", "status", "completion_submitted_at"],
            },
            {
                "model": "WorkOrderCompletion",
                "record_id": "contractor-scoped",
                "fields": ["work_order_id", "submitted_by_id", "review_status"],
            },
            {
                "model": "ContractorFeedback",
                "record_id": "contractor-scoped",
                "fields": ["work_order_id", "rating", "created_at"],
            },
        ],
    }
