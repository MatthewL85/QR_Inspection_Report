"""Run the Phase 3 cross-module readiness checks as one suite."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECK_TIMEOUT_SECONDS = int(os.environ.get("PHASE3_CHECK_TIMEOUT_SECONDS", "180"))
FAILED_CHECK_RETRIES = int(os.environ.get("PHASE3_FAILED_CHECK_RETRIES", "1"))


CHECKS = (
    ("Architecture", "architecture_smoke_check.py"),
    ("Module Contracts", "module_contract_check.py"),
    ("Module Route Boundaries", "module_route_boundary_check.py"),
    ("Module Dependency Boundaries", "module_dependency_boundary_check.py"),
    ("Module Service Contract", "module_service_contract_check.py"),
    ("Module Access and Settings Ownership", "module_access_security_boundary_check.py"),
    ("Module Settings Registry", "module_settings_registry_check.py"),
    ("Contractor Document Template Boundary", "contractor_document_template_boundary_check.py"),
    ("Platform System Map", "platform_system_map_check.py"),
    ("Archive Inventory Strict", "archive_inventory_check.py --strict"),
    ("Legacy Archive Isolation", "legacy_archive_isolation_check.py"),
    ("Core Platform Identity", "core_platform_identity_check.py"),
    ("Organisation Connection Boundary", "organisation_connection_boundary_check.py"),
    ("Migration Integrity", "migration_integrity_check.py"),
    ("Admin Portal Access Contract", "admin_portal_access_contract_check.py"),
    ("Platform Documentation Contract", "platform_documentation_contract_check.py"),
    ("Module Completion Register", "module_completion_register_check.py"),
    ("Manual Coverage", "manual_coverage_check.py"),
    ("Phase 3 Manual Contract", "phase3_manual_contract_check.py"),
    ("Phase 3 Runner Contract", "phase3_runner_contract_check.py"),
    ("App Feed Contract", "app_feed_contract_check.py"),
    ("App Shell Readiness", "app_shell_readiness_check.py"),
    ("App Health Feed Contract", "app_health_feed_contract_check.py"),
    ("App Home Feed Contract", "app_home_feed_contract_check.py"),
    ("App Capabilities Feed Contract", "app_capabilities_feed_contract_check.py"),
    ("App Company Setup Feed Contract", "app_company_setup_feed_contract_check.py"),
    ("App Mobile Surface", "app_mobile_surface_check.py"),
    ("Workflow Action Contract", "workflow_action_contract_check.py"),
    ("Notification Contract", "notification_contract_check.py"),
    ("Notification Role Visibility Contract", "notification_role_visibility_contract_check.py"),
    ("Navbar Notification Contract", "navbar_notification_contract_check.py"),
    ("Role Dashboard Surface Contract", "role_dashboard_surface_check.py"),
    ("Role Dashboard Login/Render Smoke", "dashboard_review_login_check.py"),
    ("Operational Surface Render Smoke", "operational_surface_render_check.py"),
    ("Key Site Information Contract", "key_site_info_contract_check.py"),
    ("Role Dashboard Notification Contract", "role_dashboard_notification_contract_check.py"),
    ("Works Command Centre Contract", "works_command_centre_contract_check.py"),
    ("Queue Surface Contract", "queue_surface_contract_check.py"),
    ("Contractor Standalone Docket Contract", "contractor_standalone_docket_check.py"),
    ("Media Evidence Spine", "media_evidence_spine_check.py"),
    ("Works Evidence Audit Contract", "works_evidence_audit_contract_check.py"),
    ("Contractor Evidence Propagation Contract", "contractor_evidence_propagation_check.py"),
    ("Role Dashboard Attention Contract", "role_dashboard_attention_contract_check.py"),
    ("Template References", "template_reference_check.py"),
    ("URL References", "url_for_reference_check.py"),
    ("GAR Context", "gar_context_check.py"),
    ("GAR Role Visibility Contract", "gar_role_visibility_contract_check.py"),
    ("GAR Source Adapter Contract", "gar_source_adapter_contract_check.py"),
    ("GAR Inquiry Endpoints", "gar_inquiry_endpoint_check.py"),
    ("Works Access Control", "works_access_control_check.py"),
    ("Works Lifecycle Flow", "works_lifecycle_flow_check.py"),
)

SLOW_SMOKE_CHECKS = {
    "Role Dashboard Login/Render Smoke",
    "Operational Surface Render Smoke",
}


def main() -> int:
    failures: list[tuple[str, str]] = []
    total_started_at = time.perf_counter()
    args = set(sys.argv[1:])
    quick_mode = "--quick" in args
    smoke_only_mode = "--smoke-only" in args
    list_mode = "--list" in args

    unknown_args = sorted(arg for arg in args if arg not in {"--quick", "--smoke-only", "--list"})
    if unknown_args:
        print("Unknown argument(s): " + ", ".join(unknown_args))
        print("Supported modes: --quick, --smoke-only, --list")
        return 2
    if quick_mode and smoke_only_mode:
        print("Use either --quick or --smoke-only, not both.")
        return 2

    if smoke_only_mode:
        checks = tuple(check for check in CHECKS if check[0] in SLOW_SMOKE_CHECKS)
    elif quick_mode:
        checks = tuple(check for check in CHECKS if check[0] not in SLOW_SMOKE_CHECKS)
    else:
        checks = CHECKS

    print("Phase 3 readiness check")
    print(f"- Project root: {PROJECT_ROOT}")
    mode = "smoke-only" if smoke_only_mode else "quick" if quick_mode else "full"
    print(f"- Mode: {mode}")
    print(f"- Checks queued: {len(checks)}")
    print(f"- Per-check timeout: {CHECK_TIMEOUT_SECONDS}s")
    print(f"- Failed-check retries: {FAILED_CHECK_RETRIES}")
    if quick_mode:
        skipped = ", ".join(sorted(SLOW_SMOKE_CHECKS))
        print(f"- Skipped slow smoke checks: {skipped}")
    if smoke_only_mode:
        print("- Running only role dashboard and operational render smoke checks")
    if list_mode:
        print("\nChecks:")
        for index, (label, script_name) in enumerate(checks, start=1):
            print(f"{index:02d}. {label}: {script_name}")
        return 0

    for label, script_name in checks:
        script_parts = script_name.split()
        script_path = PROJECT_ROOT / "scripts" / script_parts[0]
        script_args = script_parts[1:]
        started_at = time.perf_counter()
        print(f"\n== {label} ==", flush=True)

        attempt = 0
        result_code: int | None = None
        while attempt <= FAILED_CHECK_RETRIES:
            if attempt:
                print(f"-- retrying {label} (attempt {attempt + 1})", flush=True)

            try:
                result = subprocess.run(
                    [sys.executable, str(script_path), *script_args],
                    cwd=PROJECT_ROOT,
                    text=True,
                    check=False,
                    timeout=CHECK_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired:
                elapsed = time.perf_counter() - started_at
                print(f"TIMEOUT after {elapsed:.1f}s", flush=True)
                failures.append((label, f"timeout after {CHECK_TIMEOUT_SECONDS}s"))
                result_code = None
                break

            result_code = result.returncode
            if result_code == 0:
                break
            if attempt >= FAILED_CHECK_RETRIES:
                break
            attempt += 1

        elapsed = time.perf_counter() - started_at
        print(f"-- {label} finished in {elapsed:.1f}s", flush=True)

        if result_code:
            failures.append((label, f"exit code {result_code}"))

    if failures:
        print("\nFAILED")
        for label, reason in failures:
            print(f"- {label}: {reason}")
        return 1

    total_elapsed = time.perf_counter() - total_started_at
    print(f"\nPASSED in {total_elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
