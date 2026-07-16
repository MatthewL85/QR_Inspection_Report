"""Validate that architecture, manual and stabilisation documents stay discoverable.

This is intentionally small: it protects the documentation entry points that
keep LogixPM understandable as the module ecosystem grows.
"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = (
    "README.md",
    "docs/platform_architecture.md",
    "docs/platform_stabilisation_register.md",
    "docs/module_completion_register.md",
    "docs/role_dashboard_surface_standard.md",
    "docs/module_contracts.md",
    "docs/manual/index.md",
)

REQUIRED_REFERENCES = {
    "README.md": (
        "docs/platform_architecture.md",
        "docs/platform_stabilisation_register.md",
        "docs/module_completion_register.md",
        "docs/role_dashboard_surface_standard.md",
        "docs/module_contracts.md",
        "docs/manual/index.md",
        "phase3_readiness_check.py --quick",
        "platform_documentation_contract_check.py",
    ),
    "docs/manual/index.md": (
        "Architecture And Governance Notes",
        "docs/platform_architecture.md",
        "docs/platform_stabilisation_register.md",
        "docs/module_completion_register.md",
        "docs/role_dashboard_surface_standard.md",
        "docs/module_contracts.md",
        "platform_documentation_contract_check.py",
        "module_service_contract_check.py",
    ),
    "docs/platform_architecture.md": (
        "Related Control Documents",
        "docs/platform_stabilisation_register.md",
        "docs/module_completion_register.md",
        "docs/role_dashboard_surface_standard.md",
        "docs/module_contracts.md",
        "docs/manual/index.md",
        "phase3_readiness_check.py --quick",
        "phase3_readiness_check.py --smoke-only",
        "phase3_runner_contract_check.py",
        "platform_documentation_contract_check.py",
        "module_completion_register_check.py",
        "module_settings_registry_check.py",
        "legacy_archive_isolation_check.py",
        "media_evidence_spine_check.py",
        "contractor_document_template_boundary_check.py",
        "organisation_connection_boundary_check.py",
        "module_service_contract_check.py",
    ),
    "docs/platform_stabilisation_register.md": (
        "Non-Negotiable Build Rules",
        "Verification Gates",
        "docs/module_completion_register.md",
        "phase3_readiness_check.py --quick",
        "phase3_readiness_check.py --smoke-only",
        "phase3_runner_contract_check.py",
        "platform_documentation_contract_check.py",
        "module_completion_register_check.py",
        "module_access_security_boundary_check.py",
        "module_settings_registry_check.py",
        "legacy_archive_isolation_check.py",
        "media_evidence_spine_check.py",
        "contractor_document_template_boundary_check.py",
        "organisation_connection_boundary_check.py",
        "module_service_contract_check.py",
    ),
    "docs/module_completion_register.md": (
        "Unfinished Module Completion Register",
        "Module Completion Register",
        "Module access/security boundaries",
        "Module settings ownership",
        "Organisation identity and connections",
        "Document template ownership",
        "manual_coverage_check.py",
        "phase3_manual_contract_check.py",
        "platform_documentation_contract_check.py",
        "module_completion_register_check.py",
        "module_settings_registry_check.py",
        "legacy_archive_isolation_check.py",
        "media_evidence_spine_check.py",
        "contractor_document_template_boundary_check.py",
        "organisation_connection_boundary_check.py",
        "Contractor Logix",
        "Finance Logix",
        "GAR AI Layer",
    ),
    "docs/role_dashboard_surface_standard.md": (
        "Every primary dashboard should",
        "avoid long duplicated lists",
        "queue_surface_contract_check.py",
        "key_site_info_contract_check.py",
    ),
    "docs/module_contracts.md": (
        "Dependency Rule",
        "source-backed service or feed",
        "module_dependency_boundary_check.py",
        "module_service_contract_check.py",
    ),
}


def main() -> int:
    failures: list[str] = []

    for relative_path in REQUIRED_FILES:
        if not (PROJECT_ROOT / relative_path).exists():
            failures.append(f"Missing required documentation file: {relative_path}")

    for relative_path, required_phrases in REQUIRED_REFERENCES.items():
        path = PROJECT_ROOT / relative_path
        if not path.exists():
            continue

        content = path.read_text(encoding="utf-8")
        for phrase in required_phrases:
            if phrase not in content:
                failures.append(f"{relative_path} is missing: {phrase}")

    print("Platform documentation contract check")
    print(f"- Required files checked: {len(REQUIRED_FILES)}")
    print(f"- Document references checked: {sum(len(v) for v in REQUIRED_REFERENCES.values())}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
