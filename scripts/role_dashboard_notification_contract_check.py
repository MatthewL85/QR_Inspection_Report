"""Verify role dashboards use the shared source-backed notification strip."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


ROLE_DASHBOARD_TEMPLATES = {
    "super_admin": PROJECT_ROOT / "app/templates/super_admin/dashboard.html",
    "admin": PROJECT_ROOT / "app/templates/admin_portal/dashboard.html",
    "property_manager": PROJECT_ROOT / "app/templates/property_manager/property_manager_dashboard.html",
    "assistant": PROJECT_ROOT / "app/templates/assistant/dashboard.html",
    "finance": PROJECT_ROOT / "app/templates/finance/dashboard.html",
    "director": PROJECT_ROOT / "app/templates/director_dashboard.html",
    "contractor": PROJECT_ROOT / "app/templates/contractor_dashboard.html",
    "members": PROJECT_ROOT / "app/templates/members/dashboard.html",
}

REQUIRED_DASHBOARD_TOKENS = (
    "dashboard_notification_title",
    "notifications/_dashboard_action_strip.html",
)

REQUIRED_PARTIAL_TOKENS = (
    "unread_notification_action_views",
    "unread_notification_action_count",
    "notifications.index",
    "notifications.open",
    "item.module_label",
    "item.workflow_stage",
    "item.source_label",
)


def main() -> int:
    failures: list[str] = []
    dashboards_checked = 0

    for role_name, template in ROLE_DASHBOARD_TEMPLATES.items():
        if not template.exists():
            failures.append(f"{role_name} dashboard template is missing: {template}")
            continue
        dashboards_checked += 1
        text = template.read_text(encoding="utf-8", errors="replace")
        for token in REQUIRED_DASHBOARD_TOKENS:
            if token not in text:
                failures.append(f"{role_name} dashboard missing notification token: {token}")

    partial = PROJECT_ROOT / "app/templates/notifications/_dashboard_action_strip.html"
    if not partial.exists():
        failures.append("Dashboard notification strip partial is missing")
    else:
        partial_text = partial.read_text(encoding="utf-8", errors="replace")
        for token in REQUIRED_PARTIAL_TOKENS:
            if token not in partial_text:
                failures.append(f"Dashboard notification strip partial missing token: {token}")
        if "dashboard_notification_items = unread_notification_views" in partial_text:
            failures.append("Dashboard notification strip must use action-only notification views")

    print("Role dashboard notification contract check")
    print(f"- Role dashboard templates checked: {dashboards_checked}")
    print("- Shared notification action strip checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
