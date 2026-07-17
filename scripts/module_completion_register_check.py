"""Validate the unfinished module completion register stays enforceable."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = PROJECT_ROOT / "docs" / "module_completion_register.md"
READINESS_PATH = PROJECT_ROOT / "scripts" / "phase3_readiness_check.py"

CROSS_CUTTING_RULES = {
    "Module access/security boundaries": (
        "Guarded",
        "module_access_security_boundary_check.py",
    ),
    "Module settings ownership": (
        "Guarded",
        "module_settings_registry_check.py",
    ),
    "Organisation identity and connections": (
        "Guarded",
        "organisation_connection_boundary_check.py",
    ),
    "Document template ownership": (
        "Guarded",
        "contractor_document_template_boundary_check.py",
    ),
    "Media and evidence spine": (
        "Guarded",
        "media_evidence_spine_check.py",
    ),
    "Manual and validation coverage": (
        "Guarded",
        "manual_coverage_check.py",
        "phase3_manual_contract_check.py",
        "platform_documentation_contract_check.py",
    ),
    "Legacy/archive isolation": (
        "Guarded",
        "legacy_archive_isolation_check.py",
    ),
}

REQUIRED_MODULE_ROWS = (
    "Core Platform",
    "Property Management Logix",
    "Unit / Property Asset Spine",
    "Works Logix",
    "Contractor Logix",
    "Members Logix",
    "Finance Logix",
    "Director Logix",
    "HR Logix",
    "GAR AI Layer",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _row_for(content: str, label: str) -> str | None:
    prefix = f"| {label} |"
    for line in content.splitlines():
        if line.startswith(prefix):
            return line
    return None


def main() -> int:
    failures: list[str] = []

    if not REGISTER_PATH.exists():
        print("Module completion register check")
        print("\nFAILED")
        print("- Missing docs/module_completion_register.md")
        return 1

    register = _read(REGISTER_PATH)
    readiness = _read(READINESS_PATH) if READINESS_PATH.exists() else ""

    for label, required_fragments in CROSS_CUTTING_RULES.items():
        row = _row_for(register, label)
        if row is None:
            failures.append(f"Missing cross-cutting register row: {label}")
            continue
        for fragment in required_fragments:
            if fragment not in row:
                failures.append(f"{label} row is missing: {fragment}")

    for module_name in REQUIRED_MODULE_ROWS:
        if f"| {module_name} |" not in register:
            failures.append(f"Missing module register row: {module_name}")

    if "Module Completion Register" not in readiness:
        failures.append("Phase 3 readiness runner is missing Module Completion Register.")
    if "module_completion_register_check.py" not in readiness:
        failures.append("Phase 3 readiness runner is missing module_completion_register_check.py.")

    print("Module completion register check")
    print(f"- Cross-cutting rows checked: {len(CROSS_CUTTING_RULES)}")
    print(f"- Module rows checked: {len(REQUIRED_MODULE_ROWS)}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
