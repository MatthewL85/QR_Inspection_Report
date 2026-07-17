"""Validate auditability and retention/deletion control contracts."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_REFERENCES = {
    "docs/auditability_matrix.md": (
        "Auditability Matrix",
        "Core Rule",
        "Required Audit Fields",
        "Module Audit Ownership",
        "Cross-Module Audit Rules",
        "Human Approval Rule",
        "Immutable / Controlled Amendment Rule",
        "Every business action that changes state",
        "The audit trail must link back to the source record",
        "GAR owns recommendation metadata; the module owns the action taken by a human or workflow rule",
        "Human approval is required before",
        "Completed or signed business records should not be edited in place",
        "a notification is treated as the audit trail",
        "scripts\\audit_retention_contract_check.py",
    ),
    "docs/data_retention_deletion_matrix.md": (
        "Data Retention and Deletion Matrix",
        "Core Rule",
        "Deletion Types",
        "Module Retention Rules",
        "Protected Records",
        "Active View Rule",
        "Restore Rule",
        "GAR Rule",
        "Default to archive, deactivate, supersede or controlled amendment for business records",
        "Permanent deletion should be limited to disposable drafts",
        "Do not hard delete without a formal retention/legal workflow",
        "Archive should remove noise from active dashboards without deleting history",
        "GAR should not treat an archived record as active operational work",
        "a delete action removes a record with source links",
        "active dashboard counts include archived records by default",
        "scripts\\audit_retention_contract_check.py",
    ),
    "docs/stabilisation_security_closeout.md": (
        "docs/auditability_matrix.md",
        "docs/data_retention_deletion_matrix.md",
        "audit and retention contracts",
        "scripts\\audit_retention_contract_check.py",
    ),
    "docs/platform_stabilisation_register.md": (
        "auditability and human-approval ownership for cross-module actions",
        "retention, archive, deletion and restoration boundaries",
        "scripts\\audit_retention_contract_check.py",
    ),
    "scripts/platform_documentation_contract_check.py": (
        "audit_retention_contract_check.py",
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

    print("Audit/retention contract check")
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
