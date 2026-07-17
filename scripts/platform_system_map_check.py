"""Check the active platform still matches the LogixPM system map.

This is intentionally a lightweight architecture gate. It does not prove every
workflow works; it confirms the main module spine, dashboard entry points and
cross-module identifiers are still present before new module work is added.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


REQUIRED_FILES = {
    "Core Platform": (
        "app/models/core/user.py",
        "app/models/core/role.py",
        "app/models/core/document.py",
        "app/models/core/media_file.py",
        "app/models/core/notification.py",
        "app/models/core/organisation_connection.py",
        "app/models/onboarding/company.py",
        "app/services/core/module_registry.py",
        "app/services/core/organisation_identity.py",
    ),
    "Client / Property Management Logix": (
        "app/models/client/client.py",
        "app/routes/super_admin/client/manage_client.py",
        "app/routes/super_admin/client/add_client.py",
        "app/routes/super_admin/client/edit_client.py",
        "app/services/unit_generation_service.py",
    ),
    "Unit / Property Asset Spine": (
        "app/models/members/unit.py",
        "app/models/members/unit_membership.py",
        "app/models/members/unit_access_invite.py",
        "app/routes/unit.py",
        "app/services/unit_service.py",
        "app/services/unit_access_service.py",
    ),
    "Members Logix": (
        "app/models/members/member.py",
        "app/models/members/resident.py",
        "app/models/maintenance/maintenance_request.py",
        "app/routes/members/__init__.py",
        "app/services/members/works_context.py",
    ),
    "Works Logix": (
        "app/models/works/work_order.py",
        "app/models/works/work_order_lifecycle_event.py",
        "app/models/works/work_order_completion.py",
        "app/models/works/work_order_reopen_request.py",
        "app/models/works/work_order_progress_update.py",
        "app/routes/super_admin/work_orders/work_orders.py",
        "app/services/works/workflow_service.py",
        "app/services/works/work_order_docket_service.py",
    ),
    "Contractor Logix": (
        "app/models/contractor/contractor.py",
        "app/models/contractor/contractor_assignment.py",
        "app/models/contractor/contractor_calendar_entry.py",
        "app/models/contractor/job_docket.py",
        "app/routes/contractor.py",
        "app/services/contractor/job_docket_service.py",
    ),
    "Finance Logix": (
        "app/models/finance/budget.py",
        "app/models/finance/invoice.py",
        "app/models/finance/payment.py",
        "app/models/finance/service_charge.py",
        "app/routes/finance.py",
    ),
    "Director Logix": (
        "app/models/director/director_area_assignment.py",
        "app/routes/director.py",
    ),
    "HR Logix": (
        "app/models/hr/hr_profile.py",
        "app/models/hr/leave_request.py",
        "app/models/hr/performance_review.py",
    ),
    "Contract Manager": (
        "app/models/contracts/contract.py",
        "app/models/contracts/client_contract.py",
        "app/routes/super_admin/contracts/contracts.py",
        "app/services/contract/renewal_alerts.py",
    ),
    "GAR AI Layer": (
        "app/services/gar/context.py",
        "app/services/gar/source_queries.py",
        "app/services/gar/role_digest.py",
        "app/services/gar/capability_registry.py",
    ),
}


EXPECTED_TOKENS = {
    "app/models/onboarding/company.py": ("organisation_uid",),
    "app/models/core/organisation_connection.py": (
        "class ModuleSubscription",
        "class OrganisationConnectionInvite",
        "class OrganisationConnection",
    ),
    "app/models/members/unit.py": ("unit_uid", "client_id"),
    "app/models/members/unit_membership.py": (
        "user_id",
        "unit_id",
        "client_id",
        "access_start",
        "access_end",
    ),
    "app/models/works/work_order.py": (
        "client_id",
        "unit_id",
        "contractor_id",
        "organisation_connection_id",
    ),
    "app/models/contractor/job_docket.py": (
        "work_order_id",
        "contractor_id",
        "company_id",
        "client_id",
        "unit_id",
    ),
    "app/services/core/module_registry.py": (
        "ModuleContract",
        "organisation_connection_id",
        "unit_id",
        "work_order_id",
    ),
    "app/services/gar/source_queries.py": (
        "source_references",
        "visibility",
    ),
}


ARCHIVE_DIRS = ("legacy_archive", "Old_QR")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    from app import create_app
    from app.services.core.module_registry import module_contracts

    failures: list[str] = []
    warnings: list[str] = []
    files_checked = 0

    for module_name, relative_files in REQUIRED_FILES.items():
        for relative_file in relative_files:
            files_checked += 1
            path = PROJECT_ROOT / relative_file
            if not path.exists():
                failures.append(f"{module_name}: missing {relative_file}")

    for relative_file, tokens in EXPECTED_TOKENS.items():
        path = PROJECT_ROOT / relative_file
        if not path.exists():
            continue
        content = read_text(path)
        for token in tokens:
            if token not in content:
                failures.append(f"{relative_file}: expected token not found: {token}")

    app = create_app()
    routes_by_endpoint = {rule.endpoint: rule.rule for rule in app.url_map.iter_rules()}
    contracts = module_contracts()

    for contract in contracts:
        if not contract.owned_data:
            failures.append(f"{contract.key}: module contract has no owned_data")
        if not contract.shared_links:
            failures.append(f"{contract.key}: module contract has no shared_links")
        if contract.dashboard_endpoint and contract.dashboard_endpoint not in routes_by_endpoint:
            failures.append(
                f"{contract.key}: dashboard endpoint missing: {contract.dashboard_endpoint}"
            )

    for archive_dir in ARCHIVE_DIRS:
        path = PROJECT_ROOT / archive_dir
        if path.exists():
            warnings.append(
                f"{archive_dir} exists and should remain excluded from active module work"
            )

    print("Platform system map check")
    print(f"- Module contracts declared: {len(contracts)}")
    print(f"- Source-of-truth files checked: {files_checked}")
    print(f"- Dashboard endpoints available: {sum(1 for c in contracts if c.dashboard_endpoint)}")
    print(f"- Registered Flask routes: {len(routes_by_endpoint)}")

    if warnings:
        print("\nWarnings")
        for warning in warnings:
            print(f"- {warning}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
