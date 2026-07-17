"""Verify role dashboards expose the same Works/GAR attention contract.

This keeps Super Admin, Property Manager and Assistant dashboards aligned with
the Works Logix command centre. The dashboards can look different by role, but
they should all surface the same source-backed attention queues, next actions,
GAR quality signals and route back to the governed Works pages.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


ROLE_DASHBOARDS = {
    "super_admin": {
        "dashboard_endpoint": "super_admin.dashboard",
        "dashboard_route": "/super-admin/dashboard",
        "work_orders_endpoint": "super_admin.work_orders",
        "work_orders_route": "/super-admin/work-orders",
        "feed_endpoint": "super_admin.work_orders_feed",
        "feed_route": "/super-admin/work-orders/feed.json",
        "repeated_returns_endpoint": "super_admin.work_orders_repeated_returns",
        "repeated_returns_route": "/super-admin/work-orders/repeated-returns",
        "route_file": PROJECT_ROOT / "app/routes/super_admin/dashboard.py",
        "template_file": PROJECT_ROOT / "app/templates/super_admin/dashboard.html",
        "required_route_tokens": (
            "build_command_centre(company_id=company_id, filters=WorksFilters())",
            'works_stats=works_context.get("stats", {})',
            'works_operational_queues=works_context.get("operational_queues", {})',
            'works_next_actions=works_context.get("next_actions", [])',
            "works_gar_contractor_quality=works_gar_contractor_quality",
        ),
    },
    "property_manager": {
        "dashboard_endpoint": "property_manager.pm_dashboard",
        "dashboard_route": "/pm/dashboard",
        "work_orders_endpoint": "property_manager.work_orders",
        "work_orders_route": "/pm/work-orders",
        "feed_endpoint": "property_manager.work_orders_feed",
        "feed_route": "/pm/work-orders/feed.json",
        "repeated_returns_endpoint": "property_manager.work_orders_repeated_returns",
        "repeated_returns_route": "/pm/work-orders/repeated-returns",
        "route_file": PROJECT_ROOT / "app/routes/property_manager.py",
        "template_file": PROJECT_ROOT / "app/templates/property_manager/property_manager_dashboard.html",
        "required_route_tokens": (
            "build_command_centre(",
            "allowed_client_ids=tuple(client_ids)",
            "role_context=\"property_manager\"",
            'works_stats=works_context.get("stats", {})',
            'works_operational_queues=works_context.get("operational_queues", {})',
            'works_next_actions=works_context.get("next_actions", [])',
            "works_gar_contractor_quality=works_gar_contractor_quality",
        ),
    },
    "assistant": {
        "dashboard_endpoint": "assistant.dashboard",
        "dashboard_route": "/assistant/dashboard",
        "work_orders_endpoint": "assistant.work_orders",
        "work_orders_route": "/assistant/work-orders",
        "feed_endpoint": "assistant.work_orders_feed",
        "feed_route": "/assistant/work-orders/feed.json",
        "repeated_returns_endpoint": "assistant.work_orders_repeated_returns",
        "repeated_returns_route": "/assistant/work-orders/repeated-returns",
        "route_file": PROJECT_ROOT / "app/routes/assistant.py",
        "template_file": PROJECT_ROOT / "app/templates/assistant/dashboard.html",
        "required_route_tokens": (
            "build_command_centre(",
            "allowed_client_ids=_assigned_client_ids()",
            "assistant_manager_cover",
            "assigned_assistant",
            'works_stats=works_context.get("stats", {})',
            'works_operational_queues=works_context.get("operational_queues", {})',
            'works_next_actions=works_context.get("next_actions", [])',
            "works_gar_contractor_quality=works_gar_contractor_quality",
        ),
    },
    "admin": {
        "dashboard_endpoint": "admin_portal.dashboard",
        "dashboard_route": "/admin-portal/dashboard",
        "work_orders_endpoint": "admin_portal.work_orders",
        "work_orders_route": "/admin-portal/work-orders",
        "feed_endpoint": "admin_portal.work_orders_feed",
        "feed_route": "/admin-portal/work-orders/feed.json",
        "repeated_returns_endpoint": "admin_portal.work_orders_repeated_returns",
        "repeated_returns_route": "/admin-portal/work-orders/repeated-returns",
        "route_file": PROJECT_ROOT / "app/routes/admin_portal.py",
        "template_file": PROJECT_ROOT / "app/templates/admin_portal/dashboard.html",
        "required_route_tokens": (
            "build_command_centre(company_id=company_id, filters=WorksFilters())",
            "role_context=\"admin\"",
            'works_stats=works_context.get("stats", {})',
            'works_operational_queues=works_context.get("operational_queues", {})',
            'works_next_actions=works_context.get("next_actions", [])',
            "works_gar_contractor_quality=works_gar_contractor_quality",
        ),
    },
}


REQUIRED_TEMPLATE_TOKENS = (
    "Works Attention Queue",
    "works_stats.attention_total",
    "works_operational_queues.items()",
    "works-attention-grid",
    "works-attention-card",
    "_gar_quality_signals.html",
    "_next_actions.html",
    "notifications/_dashboard_action_strip.html",
    "works_next_actions_prefix",
    "works_next_actions_repeated_returns_prefix",
)

REQUIRED_NOTIFICATION_PARTIAL_TOKENS = (
    "unread_notification_action_views",
    "unread_notification_action_count",
    "notifications.index",
    "notifications.open",
    "item.module_label",
    "item.workflow_stage",
    "item.source_label",
)


def _normalise(text: str) -> str:
    return " ".join(text.split())


def _route_map(app) -> dict[str, set[str]]:
    routes: dict[str, set[str]] = {}
    for rule in app.url_map.iter_rules():
        routes.setdefault(rule.endpoint, set()).add(str(rule.rule))
    return routes


def _check_route_map(routes: dict[str, set[str]], failures: list[str]) -> int:
    checked = 0
    for role_name, contract in ROLE_DASHBOARDS.items():
        for endpoint_key, route_key in (
            ("dashboard_endpoint", "dashboard_route"),
            ("work_orders_endpoint", "work_orders_route"),
            ("feed_endpoint", "feed_route"),
            ("repeated_returns_endpoint", "repeated_returns_route"),
        ):
            endpoint = contract[endpoint_key]
            expected_route = contract[route_key]
            checked += 1
            if endpoint not in routes:
                failures.append(f"{role_name} missing endpoint {endpoint}")
                continue
            if expected_route not in routes[endpoint]:
                failures.append(
                    f"{role_name} endpoint {endpoint} expected route {expected_route}, got {sorted(routes[endpoint])}"
                )
    return checked


def _check_source_files(failures: list[str]) -> tuple[int, int]:
    route_files_checked = 0
    templates_checked = 0

    for role_name, contract in ROLE_DASHBOARDS.items():
        route_file = contract["route_file"]
        template_file = contract["template_file"]

        if not route_file.exists():
            failures.append(f"{role_name} route file missing: {route_file}")
            continue
        route_text = _normalise(route_file.read_text(encoding="utf-8", errors="replace"))
        route_files_checked += 1
        for token in contract["required_route_tokens"]:
            if _normalise(token) not in route_text:
                failures.append(f"{role_name} route does not expose dashboard Works/GAR token: {token}")

        if not template_file.exists():
            failures.append(f"{role_name} template missing: {template_file}")
            continue
        template_text = template_file.read_text(encoding="utf-8", errors="replace")
        templates_checked += 1
        for token in REQUIRED_TEMPLATE_TOKENS:
            if token not in template_text:
                failures.append(f"{role_name} dashboard template missing Works attention token: {token}")

        work_endpoint = contract["work_orders_endpoint"]
        repeated_endpoint = contract["repeated_returns_endpoint"]
        if work_endpoint not in template_text:
            failures.append(f"{role_name} dashboard does not link to {work_endpoint}")
        if repeated_endpoint not in template_text:
            failures.append(f"{role_name} dashboard does not link to {repeated_endpoint}")

    return route_files_checked, templates_checked


def _check_notification_partial(failures: list[str]) -> None:
    partial = PROJECT_ROOT / "app/templates/notifications/_dashboard_action_strip.html"
    if not partial.exists():
        failures.append("Dashboard notification action strip partial is missing")
        return
    text = partial.read_text(encoding="utf-8", errors="replace")
    for token in REQUIRED_NOTIFICATION_PARTIAL_TOKENS:
        if token not in text:
            failures.append(f"Dashboard notification action strip missing token: {token}")


def main() -> int:
    from app import create_app

    app = create_app()
    failures: list[str] = []

    routes_checked = _check_route_map(_route_map(app), failures)
    route_files_checked, templates_checked = _check_source_files(failures)
    _check_notification_partial(failures)

    if failures:
        print("Role dashboard attention contract check")
        for failure in failures:
            print(f"- {failure}")
        print("\nFAILED")
        return 1

    print("Role dashboard attention contract check")
    print(f"- Role dashboards checked: {len(ROLE_DASHBOARDS)}")
    print(f"- Dashboard/Works routes checked: {routes_checked}")
    print(f"- Dashboard route files checked: {route_files_checked}")
    print(f"- Dashboard templates checked: {templates_checked}")
    print("- Shared Works/GAR attention surface: yes")
    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
