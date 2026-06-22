"""Run the Phase 3 cross-module readiness checks as one suite."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


CHECKS = (
    ("Architecture", "architecture_smoke_check.py"),
    ("Module Contracts", "module_contract_check.py"),
    ("Module Route Boundaries", "module_route_boundary_check.py"),
    ("Module Dependency Boundaries", "module_dependency_boundary_check.py"),
    ("Admin Portal Access Contract", "admin_portal_access_contract_check.py"),
    ("Manual Coverage", "manual_coverage_check.py"),
    ("Phase 3 Manual Contract", "phase3_manual_contract_check.py"),
    ("App Feed Contract", "app_feed_contract_check.py"),
    ("App Shell Readiness", "app_shell_readiness_check.py"),
    ("App Health Feed Contract", "app_health_feed_contract_check.py"),
    ("App Home Feed Contract", "app_home_feed_contract_check.py"),
    ("App Capabilities Feed Contract", "app_capabilities_feed_contract_check.py"),
    ("App Mobile Surface", "app_mobile_surface_check.py"),
    ("Workflow Action Contract", "workflow_action_contract_check.py"),
    ("Notification Contract", "notification_contract_check.py"),
    ("Notification Role Visibility Contract", "notification_role_visibility_contract_check.py"),
    ("Navbar Notification Contract", "navbar_notification_contract_check.py"),
    ("Role Dashboard Notification Contract", "role_dashboard_notification_contract_check.py"),
    ("Works Command Centre Contract", "works_command_centre_contract_check.py"),
    ("Works Evidence Audit Contract", "works_evidence_audit_contract_check.py"),
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


def main() -> int:
    failures: list[tuple[str, int]] = []

    print("Phase 3 readiness check")
    print(f"- Project root: {PROJECT_ROOT}")
    print(f"- Checks queued: {len(CHECKS)}")

    for label, script_name in CHECKS:
        script_path = PROJECT_ROOT / "scripts" / script_name
        print(f"\n== {label} ==")

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip())

        if result.returncode != 0:
            failures.append((label, result.returncode))

    if failures:
        print("\nFAILED")
        for label, code in failures:
            print(f"- {label}: exit code {code}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
