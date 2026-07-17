"""Validate onboarding, import and bulk-invite control contracts."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_REFERENCES = {
    "docs/onboarding_data_import_matrix.md": (
        "Onboarding and Data Import Matrix",
        "Core Rule",
        "Scope",
        "Import Ownership Matrix",
        "Import Readiness Checklist",
        "Data Quality Rules",
        "Portal and Membership Onboarding",
        "Document and Media Onboarding",
        "External Data Migration",
        "No imported or onboarded data becomes operational until it has an owning module",
        "Do not key cross-module links off email address",
        "Use stable identifiers such as",
        "unit_uid",
        "organisation_uid",
        "Portal codes and invites must be tied to a membership",
        "Bulk portal invites are allowed only after owner and resident records have been validated",
        "Documents, photos, videos and evidence must attach to the correct source record",
        "GAR may assist parsing or summarising imports",
        "Finance Logix imports are deferred",
        "HR Logix imports are deferred",
        "batch id",
        "No direct database edits should be used as the normal onboarding path",
        "imported records become visible in dashboards before role access",
        "scripts\\onboarding_data_import_contract_check.py",
    ),
    "docs/stabilisation_security_closeout.md": (
        "docs/onboarding_data_import_matrix.md",
        "onboarding, import and portal-invite contracts",
        "scripts\\onboarding_data_import_contract_check.py",
    ),
    "docs/platform_stabilisation_register.md": (
        "onboarding, import, duplicate-check and data-quality boundaries",
        "scripts\\onboarding_data_import_contract_check.py",
    ),
    "scripts/platform_documentation_contract_check.py": (
        "onboarding_data_import_contract_check.py",
    ),
}


def main() -> int:
    failures: list[str] = []

    for relative_path, required_phrases in REQUIRED_REFERENCES.items():
        path = PROJECT_ROOT / relative_path
        if not path.exists():
            failures.append(f"Missing required file: {relative_path}")
            continue

        content = path.read_text(encoding="utf-8")
        for phrase in required_phrases:
            if phrase not in content:
                failures.append(f"{relative_path} is missing: {phrase}")

    print("Onboarding/data import contract check")
    print(f"- Files checked: {len(REQUIRED_REFERENCES)}")
    print(f"- References checked: {sum(len(v) for v in REQUIRED_REFERENCES.values())}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
