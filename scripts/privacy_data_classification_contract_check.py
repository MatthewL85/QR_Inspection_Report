"""Validate privacy and data-classification control contracts."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_REFERENCES = {
    "docs/privacy_data_classification_matrix.md": (
        "Privacy and Data Classification Matrix",
        "Core Rule",
        "Data Classification Levels",
        "Module Handling Matrix",
        "Privacy Rules",
        "Export, Notification and AI Rules",
        "Every field, document, media item, feed and GAR source must have a clear data classification",
        "Access to a module does not automatically mean access to every data class",
        "Personal Data",
        "Sensitive Personal Data",
        "Financial Data",
        "Contractor Private",
        "Governance / Legal",
        "Security / Access",
        "Derived AI Data",
        "Contractors may receive reporter contact details only where needed",
        "Contractor private materials, time logs and internal notes must not be shown",
        "Finance data must not be copied into general dashboards",
        "HR data must stay in HR Logix",
        "GAR must not infer or expose personal, financial, HR or contractor-private details",
        "Exports must inherit the same role and organisation visibility",
        "Notifications should reveal the minimum useful detail",
        "scripts\\privacy_data_classification_contract_check.py",
    ),
    "docs/stabilisation_security_closeout.md": (
        "docs/privacy_data_classification_matrix.md",
        "privacy and data-classification contracts",
        "scripts\\privacy_data_classification_contract_check.py",
    ),
    "docs/platform_stabilisation_register.md": (
        "privacy, sensitive data and module data-classification boundaries",
        "scripts\\privacy_data_classification_contract_check.py",
    ),
    "scripts/platform_documentation_contract_check.py": (
        "privacy_data_classification_contract_check.py",
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

    print("Privacy/data classification contract check")
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
