"""Verify role dashboards share the current LogixPM surface contract."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


ROLE_SURFACES = {
    "super_admin": {
        "endpoint": "super_admin.dashboard",
        "route": "/super-admin/dashboard",
        "template": "app/templates/super_admin/dashboard.html",
        "tokens": ("Super Admin Dashboard", "GAR AI Centre", "notifications/_dashboard_action_strip.html", "Works Attention Queue"),
    },
    "admin": {
        "endpoint": "admin_portal.dashboard",
        "route": "/admin-portal/dashboard",
        "template": "app/templates/admin_portal/dashboard.html",
        "tokens": ("Admin Portal", "notifications/_dashboard_action_strip.html", "Works Attention Queue"),
    },
    "property_manager": {
        "endpoint": "property_manager.pm_dashboard",
        "route": "/pm/dashboard",
        "template": "app/templates/property_manager/property_manager_dashboard.html",
        "tokens": ("Property Manager Dashboard", "notifications/_dashboard_action_strip.html", "Works Attention Queue"),
    },
    "assistant": {
        "endpoint": "assistant.dashboard",
        "route": "/assistant/dashboard",
        "template": "app/templates/assistant/dashboard.html",
        "tokens": ("Assistant Workspace", "notifications/_dashboard_action_strip.html", "Works Attention Queue"),
    },
    "finance": {
        "endpoint": "finance.dashboard",
        "route": "/finance/dashboard",
        "template": "app/templates/finance/dashboard.html",
        "tokens": ("Finance Logix", "notifications/_dashboard_action_strip.html", "gar/_ask_panel.html", "Payment Request Intake", "Finance Client View"),
    },
    "director": {
        "endpoint": "director.dashboard",
        "route": "/director/dashboard",
        "template": "app/templates/director_dashboard.html",
        "tokens": ("Director Logix", "notifications/_dashboard_action_strip.html", "gar/_ask_panel.html", "CAPEX Requests"),
    },
    "contractor": {
        "endpoint": "contractor.contractor_dashboard",
        "route": "/contractor/dashboard",
        "template": "app/templates/contractor_dashboard.html",
        "tokens": ("Contractor Logix", "notifications/_dashboard_action_strip.html", "gar/_ask_panel.html", "Open Work Queue"),
    },
    "members": {
        "endpoint": "members.dashboard",
        "route": "/members/dashboard",
        "template": "app/templates/members/dashboard.html",
        "tokens": ("Members Logix", "notifications/_dashboard_action_strip.html", "gar/_ask_panel.html", "My Linked Units"),
    },
}

LEGACY_SHELL_TOKENS = ("<!DOCTYPE html>", "<html", "<head", "<body")


def main() -> int:
    from app import create_app

    app = create_app()
    routes_by_endpoint = {rule.endpoint: rule.rule for rule in app.url_map.iter_rules()}
    failures: list[str] = []

    for role, surface in ROLE_SURFACES.items():
        endpoint = surface["endpoint"]
        if routes_by_endpoint.get(endpoint) != surface["route"]:
            failures.append(f"{role}: expected {endpoint} at {surface['route']}, got {routes_by_endpoint.get(endpoint)}")

        template = PROJECT_ROOT / surface["template"]
        if not template.exists():
            failures.append(f"{role}: missing dashboard template {surface['template']}")
            continue

        content = template.read_text(encoding="utf-8", errors="replace")
        shared_shell_tokens = (
            "{% extends 'base.html' %}",
            '{% extends "base.html" %}',
            "{% extends 'layouts/super_admin_base.html' %}",
            '{% extends "layouts/super_admin_base.html" %}',
        )
        if not any(token in content for token in shared_shell_tokens):
            failures.append(f"{role}: dashboard must extend the shared base shell")
        for legacy_token in LEGACY_SHELL_TOKENS:
            if legacy_token in content:
                failures.append(f"{role}: dashboard contains legacy standalone shell token {legacy_token}")
        for token in surface["tokens"]:
            if token not in content:
                failures.append(f"{role}: dashboard missing required surface token {token}")

    print("Role dashboard surface check")
    print(f"- Role dashboards checked: {len(ROLE_SURFACES)}")
    print("- Shared shell checked: yes")
    print("- Notification/GAR/dashboard tokens checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
