from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit


ACTION_REQUIRED_TYPES = {
    "works_assignment",
    "works_completion",
    "works_completion_review",
    "works_member_feedback",
    "works_member_request",
    "works_reopen_request",
    "works_returned",
    "works_quality_review",
    "contract_renewal",
}

WORKFLOW_STAGE_BY_TYPE = {
    "works_member_request": {
        "stage": "Member Request",
        "action": "Triage request",
        "audience": "Works / Assistant",
    },
    "works_assignment": {
        "stage": "Contractor Assigned",
        "action": "Progress job",
        "audience": "Contractor",
    },
    "works_completion": {
        "stage": "Completion Submitted",
        "action": "Review completion",
        "audience": "Member / Resident",
    },
    "works_completion_review": {
        "stage": "PM Review",
        "action": "Approve or return",
        "audience": "PM / Admin",
    },
    "works_member_feedback": {
        "stage": "Member Feedback",
        "action": "Review feedback",
        "audience": "PM / Admin",
    },
    "works_reopen_request": {
        "stage": "Reopen Requested",
        "action": "Review reopen",
        "audience": "PM / Admin",
    },
    "works_returned": {
        "stage": "Returned",
        "action": "Resubmit completion",
        "audience": "Contractor",
    },
    "works_quality_review": {
        "stage": "Quality Review",
        "action": "Review repeated returns",
        "audience": "PM / Admin",
    },
    "works_closed": {
        "stage": "Closed",
        "action": "View record",
        "audience": "Member / Resident",
    },
    "contract_renewal": {
        "stage": "Renewal Alert",
        "action": "Review contract",
        "audience": "Management",
    },
}

MODULE_RULES = (
    ("works_", "works", "Works Logix"),
    ("contract_", "contracts", "Contract Manager"),
    ("capex", "capex", "CAPEX Logix"),
    ("member", "members", "Members Logix"),
    ("resident", "members", "Members Logix"),
    ("contractor", "contractor", "Contractor Logix"),
    ("finance", "finance", "Finance Logix"),
    ("policy", "hr", "HR Logix"),
    ("hr_", "hr", "HR Logix"),
    ("gar", "gar", "GAR AI"),
)

PRIORITY_RANK = {
    "critical": 5,
    "urgent": 5,
    "high": 4,
    "medium": 3,
    "normal": 2,
    "low": 1,
}

SOURCE_REFERENCE_FIELDS = (
    ("work_order_id", "WorkOrder", "Work Order"),
    ("maintenance_request_id", "MaintenanceRequest", "Maintenance Request"),
    ("completion_id", "WorkOrderCompletion", "Completion"),
    ("feedback_id", "ContractorFeedback", "Feedback"),
    ("reopen_request_id", "WorkOrderReopenRequest", "Reopen Request"),
    ("contract_id", "ClientContract", "Contract"),
    ("client_contract_id", "ClientContract", "Contract"),
    ("unit_id", "Unit", "Unit"),
    ("client_id", "Client", "Client"),
    ("contractor_id", "Contractor", "Contractor"),
)


def _normalise(value: Any) -> str:
    return str(value or "").strip().lower()


def _module_for(notification) -> tuple[str, str]:
    notification_type = _normalise(getattr(notification, "type", None))
    category = _normalise(getattr(notification, "gar_category", None))
    source = f"{notification_type} {category}"

    for prefix, key, label in MODULE_RULES:
        if prefix in source:
            return key, label

    return "core", "Core Platform"


def _priority_rank(notification) -> int:
    priority = _normalise(getattr(notification, "priority_level", None)) or "normal"
    return PRIORITY_RANK.get(priority, PRIORITY_RANK["normal"])


def _action_required(notification) -> bool:
    notification_type = _normalise(getattr(notification, "type", None))
    suggested_action = bool((getattr(notification, "suggested_action", None) or "").strip())
    is_unread = not bool(getattr(notification, "is_read", False))
    return notification_type in ACTION_REQUIRED_TYPES or (is_unread and suggested_action)


def _workflow_stage(notification) -> dict[str, str]:
    notification_type = _normalise(getattr(notification, "type", None))
    stage = WORKFLOW_STAGE_BY_TYPE.get(notification_type)
    if stage:
        return stage

    module_key, module_label = _module_for(notification)
    if getattr(notification, "gar_category", None):
        return {
            "stage": "GAR Signal",
            "action": "Review context",
            "audience": module_label,
        }

    return {
        "stage": "Information",
        "action": "Review",
        "audience": module_label if module_key != "core" else "Platform",
    }


def _tone(notification, is_action_required: bool) -> str:
    rank = _priority_rank(notification)
    if rank >= 4:
        return "danger"
    if is_action_required:
        return "warning"
    if getattr(notification, "is_governance_related", False) or getattr(notification, "gar_category", None):
        return "primary"
    return "neutral"


def safe_notification_link_url(link_url: str | None, fallback: str = "/") -> str:
    target = (link_url or "").strip()
    if not target:
        return fallback

    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return fallback
    if not target.startswith("/") or target.startswith("//"):
        return fallback

    return target


def _source_record_id(value: Any) -> Any:
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def _notification_source_reference(notification, module_key: str, module_label: str, target_context: dict[str, Any]) -> dict[str, Any]:
    source_url = safe_notification_link_url(getattr(notification, "link_url", None))
    for field_name, model_name, label in SOURCE_REFERENCE_FIELDS:
        value = target_context.get(field_name)
        if value in (None, ""):
            continue

        record_id = _source_record_id(value)
        return {
            "model": model_name,
            "record_id": record_id,
            "label": f"{label} #{record_id}",
            "module_key": module_key,
            "module_label": module_label,
            "url": source_url,
            "source_field": field_name,
        }

    notification_id = getattr(notification, "id", None)
    return {
        "model": "Notification",
        "record_id": notification_id,
        "label": f"Notification #{notification_id}" if notification_id else "Notification",
        "module_key": module_key,
        "module_label": module_label,
        "url": source_url,
        "source_field": "notification_id",
    }


def build_notification_view(notification) -> dict[str, Any]:
    module_key, module_label = _module_for(notification)
    is_action_required = _action_required(notification)
    is_gar_related = bool(
        getattr(notification, "is_governance_related", False)
        or getattr(notification, "gar_category", None)
    )
    target_context = getattr(notification, "extracted_data", None) or {}
    workflow_stage = _workflow_stage(notification)
    source_reference = _notification_source_reference(
        notification,
        module_key,
        module_label,
        target_context,
    )

    return {
        "notification": notification,
        "module_key": module_key,
        "module_label": module_label,
        "workflow_stage": workflow_stage["stage"],
        "workflow_action": workflow_stage["action"],
        "workflow_audience": workflow_stage["audience"],
        "priority_rank": _priority_rank(notification),
        "is_action_required": is_action_required,
        "is_gar_related": is_gar_related,
        "tone": _tone(notification, is_action_required),
        "sort_date": getattr(notification, "created_at", None) or datetime.min,
        "target_context": target_context,
        "source_reference": source_reference,
        "source_label": source_reference["label"],
    }


def _date_sort_value(value: datetime) -> int:
    return (
        value.toordinal() * 86_400_000_000
        + value.hour * 3_600_000_000
        + value.minute * 60_000_000
        + value.second * 1_000_000
        + value.microsecond
    )


def build_notification_views(notifications) -> list[dict[str, Any]]:
    views = [build_notification_view(notification) for notification in notifications]
    views.sort(
        key=lambda item: (
            not item["is_action_required"],
            bool(item["notification"].is_read),
            -item["priority_rank"],
            -_date_sort_value(item["sort_date"]),
        )
    )
    return views


def notification_module_options(notifications) -> list[dict[str, str]]:
    modules = {}
    for notification in notifications:
        key, label = _module_for(notification)
        modules[key] = label

    return [
        {"key": key, "label": label}
        for key, label in sorted(modules.items(), key=lambda item: item[1])
    ]


def notification_stage_options(views: list[dict[str, Any]]) -> list[str]:
    stages = {
        item["workflow_stage"]
        for item in views
        if item.get("workflow_stage")
    }
    return sorted(stages)


def notification_summary(views: list[dict[str, Any]]) -> dict[str, Any]:
    module_counter = Counter(item["module_label"] for item in views)
    stage_counter = Counter(item["workflow_stage"] for item in views)
    action_count = sum(1 for item in views if item["is_action_required"])
    gar_count = sum(1 for item in views if item["is_gar_related"])
    high_priority_count = sum(1 for item in views if item["priority_rank"] >= 4)

    return {
        "action_count": action_count,
        "gar_count": gar_count,
        "high_priority_count": high_priority_count,
        "information_count": max(len(views) - action_count, 0),
        "module_counts": module_counter,
        "stage_counts": stage_counter,
    }


def notification_view_payload(item: dict[str, Any]) -> dict[str, Any]:
    notification = item["notification"]
    created_at = getattr(notification, "created_at", None)
    read_at = getattr(notification, "read_at", None)

    return {
        "id": notification.id,
        "message": notification.message,
        "type": notification.type,
        "is_read": bool(notification.is_read),
        "read_at": read_at.isoformat() if read_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "link_url": notification.link_url,
        "safe_link_url": safe_notification_link_url(notification.link_url),
        "priority_level": notification.priority_level or "Normal",
        "priority_rank": item["priority_rank"],
        "module_key": item["module_key"],
        "module_label": item["module_label"],
        "workflow_stage": item["workflow_stage"],
        "workflow_action": item["workflow_action"],
        "workflow_audience": item["workflow_audience"],
        "is_action_required": item["is_action_required"],
        "is_gar_related": item["is_gar_related"],
        "tone": item["tone"],
        "gar_category": notification.gar_category,
        "suggested_action": notification.suggested_action,
        "target_context": item["target_context"],
        "source_reference": item["source_reference"],
        "source_label": item["source_label"],
    }
