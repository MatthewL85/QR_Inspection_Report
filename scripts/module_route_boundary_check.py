"""Verify active module route namespaces stay separated."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


MODULE_ROUTE_PREFIXES = {
    "admin_portal": "/admin-portal",
    "assistant": "/assistant",
    "contractor": "/contractor",
    "finance": "/finance",
    "members": "/members",
    "notifications": "/notifications",
    "property_manager": "/pm",
    "unit_bp": "/units",
    "super_admin": "/super-admin",
}

GAR_FEED_PREFIXES = {
    "admin_portal.gar_feed": "/admin-portal/gar/",
    "assistant.gar_feed": "/assistant/gar/",
    "contractor.gar_feed": "/contractor/gar/",
    "finance.gar_feed": "/finance/gar/",
    "members.gar_feed": "/members/gar/",
    "property_manager.gar_feed": "/pm/gar/",
    "super_admin.gar_insights_feed": "/super-admin/gar-insights/",
}


def main() -> int:
    from app import create_app
    from app.services.core.module_registry import module_contracts

    app = create_app()
    failures: list[str] = []
    module_routes_checked = 0
    dashboard_endpoints_checked = 0
    rules_by_endpoint = {rule.endpoint: rule for rule in app.url_map.iter_rules()}

    for rule in app.url_map.iter_rules():
        module_key = rule.endpoint.split(".", 1)[0]
        expected_prefix = MODULE_ROUTE_PREFIXES.get(module_key)
        if not expected_prefix:
            continue
        module_routes_checked += 1
        if not rule.rule.startswith(expected_prefix):
            failures.append(
                f"{rule.endpoint} is registered at {rule.rule}, expected prefix {expected_prefix}"
            )

    for contract in module_contracts():
        if not contract.dashboard_endpoint:
            continue
        dashboard_endpoints_checked += 1
        if contract.dashboard_endpoint not in rules_by_endpoint:
            failures.append(
                f"{contract.key} dashboard endpoint is missing: {contract.dashboard_endpoint}"
            )

    for endpoint, expected_prefix in sorted(GAR_FEED_PREFIXES.items()):
        rule = rules_by_endpoint.get(endpoint)
        if not rule:
            failures.append(f"Missing GAR feed endpoint for boundary check: {endpoint}")
            continue
        if not rule.rule.startswith(expected_prefix):
            failures.append(
                f"{endpoint} is registered at {rule.rule}, expected GAR prefix {expected_prefix}"
            )

    print("Module route boundary check")
    print(f"- Module route prefixes checked: {module_routes_checked}")
    print(f"- Dashboard endpoints checked: {dashboard_endpoints_checked}")
    print(f"- GAR feed namespace checks: {len(GAR_FEED_PREFIXES)}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
