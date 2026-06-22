from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, or_

from app.extensions import db
from app.models.core.notification import Notification
from app.services.core.notification_intelligence import (
    build_notification_views,
    notification_module_options,
    notification_stage_options,
    notification_summary,
    notification_view_payload,
)


@dataclass(frozen=True)
class NotificationFilters:
    status: str = "unread"
    type: str = ""
    priority: str = ""
    module: str = ""
    stage: str = ""
    action: str = ""
    search: str = ""


def _normalise_filters(filters: NotificationFilters) -> NotificationFilters:
    status = (filters.status or "unread").strip().lower()
    if status not in {"unread", "read", "all"}:
        status = "all"

    action = (filters.action or "").strip().lower()
    if action not in {"action", "info", "gar"}:
        action = ""

    return NotificationFilters(
        status=status,
        type=(filters.type or "").strip(),
        priority=(filters.priority or "").strip(),
        module=(filters.module or "").strip(),
        stage=(filters.stage or "").strip(),
        action=action,
        search=(filters.search or "").strip(),
    )


def build_notification_context(user_id: int, filters: NotificationFilters | None = None, limit: int = 300) -> dict:
    filters = _normalise_filters(filters or NotificationFilters())
    limit = max(1, min(int(limit or 300), 300))

    query = Notification.query.filter_by(recipient_id=user_id)

    if filters.status == "unread":
        query = query.filter(Notification.is_read.is_(False))
    elif filters.status == "read":
        query = query.filter(Notification.is_read.is_(True))

    if filters.type:
        query = query.filter(Notification.type == filters.type)
    if filters.priority:
        query = query.filter(Notification.priority_level == filters.priority)
    if filters.search:
        term = f"%{filters.search}%"
        query = query.filter(or_(
            Notification.message.ilike(term),
            Notification.type.ilike(term),
            Notification.gar_category.ilike(term),
            Notification.suggested_action.ilike(term),
        ))

    notifications = (
        query
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())
        .limit(limit)
        .all()
    )
    notification_views = build_notification_views(notifications)

    if filters.module:
        notification_views = [
            item for item in notification_views
            if item["module_key"] == filters.module
        ]
    if filters.stage:
        notification_views = [
            item for item in notification_views
            if item["workflow_stage"] == filters.stage
        ]

    if filters.action == "action":
        notification_views = [
            item for item in notification_views
            if item["is_action_required"]
        ]
    elif filters.action == "info":
        notification_views = [
            item for item in notification_views
            if not item["is_action_required"]
        ]
    elif filters.action == "gar":
        notification_views = [
            item for item in notification_views
            if item["is_gar_related"]
        ]

    base_query = Notification.query.filter_by(recipient_id=user_id)
    unread_count = base_query.filter(Notification.is_read.is_(False)).count()
    read_count = base_query.filter(Notification.is_read.is_(True)).count()
    all_count = unread_count + read_count
    acknowledged_count = base_query.filter(Notification.read_at.isnot(None)).count()
    last_acknowledged_at = (
        db.session.query(func.max(Notification.read_at))
        .filter(Notification.recipient_id == user_id)
        .scalar()
    )

    available_types = [
        row[0]
        for row in (
            db.session.query(Notification.type)
            .filter(Notification.recipient_id == user_id)
            .filter(Notification.type.isnot(None))
            .distinct()
            .order_by(Notification.type.asc())
            .all()
        )
        if row[0]
    ]
    available_priorities = [
        row[0]
        for row in (
            db.session.query(Notification.priority_level)
            .filter(Notification.recipient_id == user_id)
            .filter(Notification.priority_level.isnot(None))
            .distinct()
            .order_by(Notification.priority_level.asc())
            .all()
        )
        if row[0]
    ]
    all_user_notifications = (
        Notification.query
        .filter_by(recipient_id=user_id)
        .order_by(Notification.created_at.desc())
        .limit(500)
        .all()
    )
    available_modules = notification_module_options(all_user_notifications)
    all_user_views = build_notification_views(all_user_notifications)
    available_stages = notification_stage_options(all_user_views)
    notification_stats = notification_summary(notification_views)
    action_queue_views = [
        item for item in all_user_views
        if item["is_action_required"] and not item["notification"].is_read
    ][:5]

    return {
        "notification_views": notification_views,
        "status_filter": filters.status,
        "type_filter": filters.type,
        "priority_filter": filters.priority,
        "module_filter": filters.module,
        "stage_filter": filters.stage,
        "action_filter": filters.action,
        "search_filter": filters.search,
        "available_types": available_types,
        "available_priorities": available_priorities,
        "available_modules": available_modules,
        "available_stages": available_stages,
        "notification_stats": notification_stats,
        "action_queue_views": action_queue_views,
        "unread_count": unread_count,
        "read_count": read_count,
        "all_count": all_count,
        "acknowledged_count": acknowledged_count,
        "last_acknowledged_at": last_acknowledged_at,
        "limit": limit,
    }


def notification_feed_payload(context: dict) -> dict:
    stats = context["notification_stats"]
    notification_payloads = [
        notification_view_payload(item)
        for item in context["notification_views"][:context["limit"]]
    ]
    action_payloads = [
        notification_view_payload(item)
        for item in context["action_queue_views"]
    ]
    return {
        "context_type": "notification_queue",
        "notifications": notification_payloads,
        "action_queue": action_payloads,
        "source_references": notification_source_references(notification_payloads + action_payloads),
        "summary": {
            "unread_count": context["unread_count"],
            "read_count": context["read_count"],
            "all_count": context["all_count"],
            "acknowledged_count": context["acknowledged_count"],
            "last_acknowledged_at": (
                context["last_acknowledged_at"].isoformat()
                if context["last_acknowledged_at"] else None
            ),
            "action_count": stats["action_count"],
            "gar_count": stats["gar_count"],
            "high_priority_count": stats["high_priority_count"],
            "information_count": stats["information_count"],
            "module_counts": dict(stats["module_counts"]),
            "stage_counts": dict(stats["stage_counts"]),
        },
        "filters": {
            "status": context["status_filter"],
            "type": context["type_filter"],
            "priority": context["priority_filter"],
            "module": context["module_filter"],
            "stage": context["stage_filter"],
            "action": context["action_filter"],
            "search": context["search_filter"],
            "limit": context["limit"],
        },
    }


def notification_source_references(notifications: list[dict]) -> list[dict]:
    fields = [
        "recipient_id",
        "message",
        "type",
        "is_read",
        "read_at",
        "priority_level",
        "gar_category",
        "suggested_action",
        "extracted_data",
    ]
    references = [
        {
            "model": "Notification",
            "record_id": None,
            "label": "Notification queue",
            "fields": fields,
        }
    ]
    seen = {("Notification", None)}

    for item in notifications:
        source = item.get("source_reference") or {}
        model = source.get("model")
        record_id = source.get("record_id")
        if not model or (model, record_id) in seen:
            continue
        seen.add((model, record_id))
        references.append(
            {
                "model": model,
                "record_id": record_id,
                "label": source.get("label") or f"{model} #{record_id}",
                "fields": [
                    "id",
                    "status",
                    "client_id",
                    "unit_id",
                    "created_at",
                    "updated_at",
                ],
                "module_key": source.get("module_key"),
                "module_label": source.get("module_label"),
                "source_field": source.get("source_field"),
                "url": source.get("url"),
            }
        )

    return references


def build_nav_notification_context(user_id: int, limit: int = 5) -> dict:
    """Return the compact notification payload used by shared navbars."""
    context = build_notification_context(
        user_id,
        NotificationFilters(status="unread"),
        limit=max(limit, 25),
    )
    views = context["notification_views"][:limit]
    action_views = [
        item for item in context["notification_views"]
        if item["is_action_required"]
    ][:limit]
    stats = context["notification_stats"]

    return {
        "unread_notification_count": context["unread_count"],
        "unread_notifications": [item["notification"] for item in views],
        "unread_notification_views": views,
        "unread_notification_action_views": action_views,
        "unread_notification_action_count": stats["action_count"],
        "unread_notification_gar_count": stats["gar_count"],
    }
