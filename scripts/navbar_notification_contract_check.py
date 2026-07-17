"""Verify shared navbars use the source-backed notification context."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


NAVBAR_TEMPLATES = (
    PROJECT_ROOT / "app/templates/_partials/navbar.html",
    PROJECT_ROOT / "app/templates/navbar.html",
)

REQUIRED_NAVBAR_TOKENS = (
    "unread_notification_count",
    "unread_notification_views",
    "item.module_label",
    "item.workflow_stage",
    "item.source_label",
    "notification-count",
    "notifications.open",
    "notifications.index",
    "notifications.mark_all_read",
)


def _route_map(app) -> dict[str, set[str]]:
    routes: dict[str, set[str]] = {}
    for rule in app.url_map.iter_rules():
        routes.setdefault(rule.endpoint, set()).add(str(rule.rule))
    return routes


def _check_routes(routes: dict[str, set[str]], failures: list[str]) -> int:
    expected = {
        "notifications.index": "/notifications/",
        "notifications.feed": "/notifications/feed.json",
        "notifications.open": "/notifications/<int:notification_id>/open",
        "notifications.mark_read": "/notifications/<int:notification_id>/mark-read",
        "notifications.mark_all_read": "/notifications/mark-all-read",
    }
    for endpoint, route in expected.items():
        if endpoint not in routes:
            failures.append(f"Missing notification endpoint: {endpoint}")
            continue
        if route not in routes[endpoint]:
            failures.append(f"{endpoint} expected route {route}, got {sorted(routes[endpoint])}")
    return len(expected)


def _check_navbars(failures: list[str]) -> int:
    checked = 0
    for template in NAVBAR_TEMPLATES:
        if not template.exists():
            failures.append(f"Navbar template missing: {template}")
            continue
        checked += 1
        text = template.read_text(encoding="utf-8", errors="replace")
        for token in REQUIRED_NAVBAR_TOKENS:
            if token not in text:
                failures.append(f"{template.name} missing notification token: {token}")
        if "for notification in unread_notifications" in text:
            failures.append(f"{template.name} still renders raw notification objects instead of source-aware views")
        if 'method="post" action="{{ url_for(\'notifications.mark_all_read\') }}"' not in text:
            failures.append(f"{template.name} must keep mark-all-read as a POST form")
    return checked


def _check_context_processor(failures: list[str]) -> None:
    app_init = PROJECT_ROOT / "app/__init__.py"
    text = app_init.read_text(encoding="utf-8", errors="replace")
    required = (
        "def inject_unread_notifications()",
        "build_nav_notification_context",
        "unread_notification_count",
        "unread_notification_views",
        "unread_notification_action_views",
        "unread_notification_action_count",
        "unread_notification_gar_count",
    )
    for token in required:
        if token not in text:
            failures.append(f"Notification context processor missing token: {token}")
    if "Notification.query.filter_by" in text[text.find("def inject_unread_notifications()"):]:
        failures.append("Notification context processor bypasses the notification feed service")


def _check_service_contract(failures: list[str]) -> None:
    service_file = PROJECT_ROOT / "app/services/core/notification_feed.py"
    text = service_file.read_text(encoding="utf-8", errors="replace")
    required = (
        "def build_nav_notification_context",
        "build_notification_context(",
        "NotificationFilters(status=\"unread\")",
        "\"unread_notification_count\"",
        "\"unread_notifications\"",
        "\"unread_notification_views\"",
        "\"unread_notification_action_views\"",
        "\"unread_notification_action_count\"",
        "\"unread_notification_gar_count\"",
    )
    for token in required:
        if token not in text:
            failures.append(f"Notification feed service missing nav token: {token}")


def main() -> int:
    from app import create_app

    app = create_app()
    failures: list[str] = []

    routes_checked = _check_routes(_route_map(app), failures)
    navbars_checked = _check_navbars(failures)
    _check_context_processor(failures)
    _check_service_contract(failures)

    if failures:
        print("Navbar notification contract check")
        for failure in failures:
            print(f"- {failure}")
        print("\nFAILED")
        return 1

    print("Navbar notification contract check")
    print(f"- Notification routes checked: {routes_checked}")
    print(f"- Navbar templates checked: {navbars_checked}")
    print("- Source-backed navbar context checked: yes")
    print("- POST-only mark-all-read checked: yes")
    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
