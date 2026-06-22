r"""Architecture smoke check for LogixPM.

This script is intentionally lightweight: it validates app-factory loading,
blueprint registration, and critical route presence without touching the
database or mutating runtime data.

Run from the project root:
    .\venv\Scripts\python.exe scripts\architecture_smoke_check.py
"""

from __future__ import annotations

import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


EXPECTED_BLUEPRINTS = {
    "auth",
    "settings",
    "super_admin",
    "property_manager",
    "contractor",
    "director",
    "finance",
    "assistant",
    "admin_portal",
    "members",
    "notifications",
    "unit_bp",
    "client_key_info",
    "super_admin_contracts",
    "super_admin_simple_contracts",
}

LEGACY_BLUEPRINTS_THAT_SHOULD_NOT_REGISTER = {
    "admin",
}

CRITICAL_ENDPOINTS = {
    "auth.login",
    "auth.logout",
    "super_admin.dashboard",
    "super_admin.manage_clients",
    "super_admin.view_client",
    "super_admin.generate_client_units",
    "super_admin.manage_users",
    "super_admin_contracts.contracts_overview",
    "super_admin.work_orders",
    "super_admin.work_orders_feed",
    "super_admin.gar_insights",
    "super_admin.gar_capabilities_feed",
    "super_admin.gar_insights_feed",
    "super_admin.gar_inquiry",
    "super_admin.convert_member_request_to_work_order",
    "super_admin.assign_work_order_contractor",
    "unit_bp.list",
    "unit_bp.view",
    "unit_bp.edit",
    "unit_bp.work_order_review",
    "unit_bp.work_order_completion_review",
    "unit_bp.reopen_request_approve",
    "unit_bp.reopen_request_reject",
    "finance.dashboard",
    "finance.manage_clients",
    "finance.gar_feed",
    "finance.gar_inquiry",
    "assistant.dashboard",
    "assistant.manage_clients",
    "assistant.work_orders",
    "assistant.work_orders_feed",
    "assistant.gar_feed",
    "assistant.gar_inquiry",
    "assistant.convert_member_request",
    "assistant.assign_work_order_contractor",
    "admin_portal.dashboard",
    "admin_portal.manage_clients",
    "admin_portal.work_orders",
    "admin_portal.work_orders_feed",
    "admin_portal.work_orders_repeated_returns",
    "admin_portal.gar_feed",
    "admin_portal.gar_inquiry",
    "admin_portal.convert_member_request",
    "admin_portal.assign_work_order_contractor",
    "director.gar_feed",
    "director.gar_inquiry",
    "property_manager.work_orders",
    "property_manager.work_orders_feed",
    "property_manager.gar_feed",
    "property_manager.gar_inquiry",
    "property_manager.convert_member_request",
    "property_manager.assign_work_order_contractor",
    "members.dashboard",
    "members.works",
    "members.works_feed",
    "members.gar_feed",
    "members.gar_inquiry",
    "members.create_maintenance_request",
    "members.request_reopen",
    "members.submit_work_order_feedback",
    "notifications.index",
    "notifications.feed",
    "notifications.open",
    "contractor.work_orders",
    "contractor.work_orders_feed",
    "contractor.gar_feed",
    "contractor.gar_inquiry",
    "contractor.update_work_order",
}

EXPECTED_PACKAGE_ORIGINS = {
    "app.routes.auth": Path("app/routes/auth/__init__.py"),
    "app.routes.super_admin": Path("app/routes/super_admin/__init__.py"),
}

EXPECTED_MODEL_TABLES = {
    "app.models.works.work_order_lifecycle_event.WorkOrderLifecycleEvent": "work_order_lifecycle_events",
}


def _missing(expected: Iterable[str], actual: Iterable[str]) -> list[str]:
    actual_set = set(actual)
    return sorted(item for item in expected if item not in actual_set)


def main() -> int:
    from app import create_app

    app = create_app()
    blueprints = set(app.blueprints.keys())
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}

    failures: list[str] = []

    missing_blueprints = _missing(EXPECTED_BLUEPRINTS, blueprints)
    if missing_blueprints:
        failures.append(
            "Missing expected blueprints: " + ", ".join(missing_blueprints)
        )

    registered_legacy = sorted(
        blueprint for blueprint in LEGACY_BLUEPRINTS_THAT_SHOULD_NOT_REGISTER
        if blueprint in blueprints
    )
    if registered_legacy:
        failures.append(
            "Legacy blueprints unexpectedly registered: "
            + ", ".join(registered_legacy)
        )

    missing_endpoints = _missing(CRITICAL_ENDPOINTS, endpoints)
    if missing_endpoints:
        failures.append(
            "Missing critical endpoints: " + ", ".join(missing_endpoints)
        )

    for module_name, expected_relative_path in EXPECTED_PACKAGE_ORIGINS.items():
        spec = importlib.util.find_spec(module_name)
        origin = Path(spec.origin).resolve() if spec and spec.origin else None
        expected_origin = (PROJECT_ROOT / expected_relative_path).resolve()
        if origin != expected_origin:
            failures.append(
                f"{module_name} resolves to {origin}, expected {expected_origin}"
            )

    for dotted_path, expected_table in EXPECTED_MODEL_TABLES.items():
        module_name, class_name = dotted_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        model_class = getattr(module, class_name, None)
        actual_table = getattr(model_class, "__tablename__", None)
        if actual_table != expected_table:
            failures.append(
                f"{dotted_path} table is {actual_table}, expected {expected_table}"
            )

    print("Architecture smoke check")
    print(f"- Blueprints registered: {len(blueprints)}")
    print(f"- URL rules registered: {len(list(app.url_map.iter_rules()))}")
    print(f"- Critical endpoints checked: {len(CRITICAL_ENDPOINTS)}")
    print(f"- Package origins checked: {len(EXPECTED_PACKAGE_ORIGINS)}")
    print(f"- Model tables checked: {len(EXPECTED_MODEL_TABLES)}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
