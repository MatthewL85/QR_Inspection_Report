"""Verify the Phase 3 notification intelligence contract."""

from __future__ import annotations

from datetime import UTC, datetime
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


EXPECTED_WORKFLOW_STAGES = {
    "works_member_request": ("Member Request", "Works / Assistant"),
    "works_assignment": ("Contractor Assigned", "Contractor"),
    "works_completion": ("Completion Submitted", "Member / Resident"),
    "works_completion_review": ("PM Review", "PM / Admin"),
    "works_member_feedback": ("Member Feedback", "PM / Admin"),
    "works_reopen_request": ("Reopen Requested", "PM / Admin"),
    "works_returned": ("Returned", "Contractor"),
    "works_quality_review": ("Quality Review", "PM / Admin"),
    "works_closed": ("Closed", "Member / Resident"),
    "contract_renewal": ("Renewal Alert", "Management"),
}

EXPECTED_ACTION_TYPES = {
    "works_member_request",
    "works_assignment",
    "works_completion",
    "works_completion_review",
    "works_member_feedback",
    "works_reopen_request",
    "works_returned",
    "works_quality_review",
    "contract_renewal",
}

EXPECTED_PAYLOAD_KEYS = {
    "id",
    "message",
    "type",
    "is_read",
    "read_at",
    "created_at",
    "link_url",
    "safe_link_url",
    "priority_level",
    "priority_rank",
    "module_key",
    "module_label",
    "workflow_stage",
    "workflow_action",
    "workflow_audience",
    "is_action_required",
    "is_gar_related",
    "tone",
    "gar_category",
    "suggested_action",
    "target_context",
    "source_reference",
    "source_label",
}


def _sample_notification(notification_id: int, notification_type: str):
    from app.models.core.notification import Notification

    return Notification(
        id=notification_id,
        recipient_id=10,
        message=f"Sample {notification_type}",
        type=notification_type,
        is_read=False,
        created_at=datetime(2026, 1, notification_id, tzinfo=UTC),
        link_url=f"/sample/{notification_id}",
        priority_level="High" if notification_type == "works_quality_review" else "Normal",
        gar_category="Works Logix" if notification_type.startswith("works_") else "Contract Manager",
        suggested_action="Review required" if notification_type in EXPECTED_ACTION_TYPES else "",
        extracted_data={
            "source_type": notification_type,
            "work_order_id": notification_id if notification_type.startswith("works_") else None,
            "action_target": f"/sample/{notification_id}",
        },
    )


def _check_routes(failures: list[str]) -> None:
    from app import create_app

    app = create_app()
    rules = {rule.endpoint: rule for rule in app.url_map.iter_rules()}

    expected_routes = {
        "notifications.feed": ("GET", "/notifications/feed.json"),
        "notifications.mark_read": ("POST", "/notifications/<int:notification_id>/mark-read"),
        "notifications.mark_all_read": ("POST", "/notifications/mark-all-read"),
    }

    for endpoint, (expected_method, expected_rule) in expected_routes.items():
        rule = rules.get(endpoint)
        if not rule:
            failures.append(f"Missing notification endpoint: {endpoint}")
            continue
        if rule.rule != expected_rule:
            failures.append(f"{endpoint} route changed from {expected_rule} to {rule.rule}")
        methods = set(rule.methods or set())
        if expected_method not in methods:
            failures.append(f"{endpoint} does not allow {expected_method}")

        if endpoint == "notifications.feed":
            if {"POST", "PUT", "PATCH", "DELETE"}.intersection(methods):
                failures.append("notifications.feed allows a mutating method")
        else:
            if "GET" in methods:
                failures.append(f"{endpoint} allows GET but mark-read actions must be POST-only")


def _check_safe_notification_targets(failures: list[str]) -> None:
    from app import create_app
    from app.routes.notifications import _safe_notification_target, _safe_return_target
    from app.services.core.notification_intelligence import safe_notification_link_url

    app = create_app()
    with app.test_request_context():
        safe_cases = {
            "/units/1?tab=works": "/units/1?tab=works",
            "/super-admin/work-orders#member-request-1": "/super-admin/work-orders#member-request-1",
        }
        unsafe_cases = (
            "",
            "units/1",
            "//evil.example/path",
            "https://evil.example/path",
            "http://evil.example/path",
            "mailto:test@example.com",
        )

        for source, expected in safe_cases.items():
            actual = _safe_notification_target(source)
            if actual != expected:
                failures.append(f"Safe notification target changed: {source} -> {actual}")

        for source in unsafe_cases:
            actual = _safe_notification_target(source)
            if actual != "/auth/profile":
                failures.append(f"Unsafe notification target did not fall back safely: {source} -> {actual}")

            payload_target = safe_notification_link_url(source, "/fallback")
            if payload_target != "/fallback":
                failures.append(f"Unsafe feed notification target did not fall back safely: {source} -> {payload_target}")

        return_cases = {
            "/notifications/?status=all": "/notifications/?status=all",
            "http://localhost/units/1?tab=works": "/units/1?tab=works",
        }
        for source, expected in return_cases.items():
            actual = _safe_return_target(source, "/fallback")
            if actual != expected:
                failures.append(f"Safe notification return target changed: {source} -> {actual}")

        for source in ("https://evil.example/path", "//evil.example/path", "units/1"):
            actual = _safe_return_target(source, "/fallback")
            if actual != "/fallback":
                failures.append(f"Unsafe notification return target did not fall back: {source} -> {actual}")


def _check_notification_template(failures: list[str]) -> None:
    template = (PROJECT_ROOT / "app/templates/notifications/index.html").read_text(encoding="utf-8")
    required_tokens = (
        "notification-action-card",
        "item.source_label",
        "notifications.open",
        "notification_return_url",
        'name="next"',
    )
    for token in required_tokens:
        if token not in template:
            failures.append(f"Notification Centre action queue lost template token: {token}")


def _check_read_tracking(failures: list[str]) -> None:
    from app.routes.notifications import _mark_notification_read

    notification = _sample_notification(20, "works_member_request")
    if notification.read_at is not None:
        failures.append("Sample notification unexpectedly starts with read_at")

    _mark_notification_read(notification)
    first_read_at = notification.read_at
    if not notification.is_read or first_read_at is None:
        failures.append("Notification mark-read helper did not set is_read and read_at")

    _mark_notification_read(notification)
    if notification.read_at != first_read_at:
        failures.append("Notification mark-read helper overwrote existing read_at")



def main() -> int:
    from app.services.core.notification_feed import notification_source_references
    from app.services.core.notification_intelligence import (
        build_notification_views,
        notification_summary,
        notification_view_payload,
    )

    failures: list[str] = []
    _check_routes(failures)
    _check_safe_notification_targets(failures)
    _check_notification_template(failures)
    _check_read_tracking(failures)

    notifications = [
        _sample_notification(index, notification_type)
        for index, notification_type in enumerate(EXPECTED_WORKFLOW_STAGES, start=1)
    ]
    views = build_notification_views(notifications)
    views_by_type = {item["notification"].type: item for item in views}

    for notification_type, (stage, audience) in EXPECTED_WORKFLOW_STAGES.items():
        view = views_by_type.get(notification_type)
        if not view:
            failures.append(f"Missing notification intelligence view: {notification_type}")
            continue
        if view["workflow_stage"] != stage:
            failures.append(
                f"{notification_type} stage changed from {stage} to {view['workflow_stage']}"
            )
        if view["workflow_audience"] != audience:
            failures.append(
                f"{notification_type} audience changed from {audience} to {view['workflow_audience']}"
            )
        if notification_type in EXPECTED_ACTION_TYPES and not view["is_action_required"]:
            failures.append(f"{notification_type} is no longer action-required")
        if notification_type.startswith("works_") and view["module_key"] != "works":
            failures.append(f"{notification_type} no longer maps to Works Logix")

        payload = notification_view_payload(view)
        missing_payload_keys = sorted(EXPECTED_PAYLOAD_KEYS.difference(payload))
        if missing_payload_keys:
            failures.append(
                f"{notification_type} payload is missing keys: {', '.join(missing_payload_keys)}"
            )
        if payload.get("target_context", {}).get("action_target") != f"/sample/{view['notification'].id}":
            failures.append(f"{notification_type} payload lost its action target")
        if payload.get("safe_link_url") != f"/sample/{view['notification'].id}":
            failures.append(f"{notification_type} payload safe link changed")
        if "read_at" not in payload:
            failures.append(f"{notification_type} payload lost read_at")
        source_reference = payload.get("source_reference")
        if not isinstance(source_reference, dict):
            failures.append(f"{notification_type} payload lost its source reference")
        elif notification_type.startswith("works_"):
            if source_reference.get("model") != "WorkOrder":
                failures.append(
                    f"{notification_type} source reference model changed to {source_reference.get('model')}"
                )
            if source_reference.get("record_id") != view["notification"].id:
                failures.append(f"{notification_type} source reference lost the work order id")
        if not payload.get("source_label"):
            failures.append(f"{notification_type} payload lost its source label")

    source_references = notification_source_references([
        notification_view_payload(item)
        for item in views
    ])
    if not any(reference.get("model") == "Notification" for reference in source_references):
        failures.append("Notification source references lost the queue reference")
    if not any(reference.get("model") == "WorkOrder" for reference in source_references):
        failures.append("Notification source references lost the work order references")

    summary = notification_summary(views)
    for stage, _audience in EXPECTED_WORKFLOW_STAGES.values():
        if summary["stage_counts"].get(stage, 0) < 1:
            failures.append(f"Notification summary does not count stage: {stage}")
    if summary["module_counts"].get("Works Logix", 0) < 9:
        failures.append("Notification summary does not count Works Logix notifications")
    if summary["action_count"] < len(EXPECTED_ACTION_TYPES):
        failures.append("Notification summary action count is lower than expected")
    if summary["high_priority_count"] < 1:
        failures.append("Notification summary does not identify high-priority items")

    print("Notification contract check")
    print(f"- Workflow notification types checked: {len(EXPECTED_WORKFLOW_STAGES)}")
    print("- Notification feed route checked: read-only")
    print("- Mark-read action routes checked: POST-only")
    print("- Notification open target safety checked: yes")
    print("- Notification return target safety checked: yes")
    print("- Notification read timestamp checked: yes")
    print("- Notification intelligence payload checked: yes")
    print("- Notification feed safe link checked: yes")
    print("- Notification source reference checked: yes")
    print("- Notification feed source references checked: yes")
    print("- Notification Centre source labels checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
