"""Validate the schema and migration ownership contract."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_REFERENCES = {
    "docs/schema_migration_ownership_matrix.md": (
        "Schema and Migration Ownership Matrix",
        "Core Rule",
        "Ownership Matrix",
        "Migration Rules",
        "Review Questions",
        "Red Flags",
        "Every schema change must have an owning module",
        "Manual production database edits are not a normal delivery path",
        "A migration must not mix unrelated module work",
        "source IDs, stable UIDs, audit history, media/evidence links and external sync references",
        "Finance schema must stay finance-owned and guarded until Finance close-out is complete",
        "Contractor schema must work standalone",
        "GAR schema stores derived/source references, not replacement business facts",
        "scripts\\schema_migration_contract_check.py",
        "scripts\\migration_integrity_check.py",
    ),
    "docs/deployment_environment_security_matrix.md": (
        "docs/schema_migration_ownership_matrix.md",
        "schema and migration ownership contract",
        "scripts\\schema_migration_contract_check.py",
    ),
    "docs/release_change_management_matrix.md": (
        "docs/schema_migration_ownership_matrix.md",
        "schema and migration ownership contract",
        "scripts\\schema_migration_contract_check.py",
    ),
    "docs/stabilisation_security_closeout.md": (
        "docs/schema_migration_ownership_matrix.md",
        "schema and migration ownership contract",
        "scripts\\schema_migration_contract_check.py",
    ),
    "docs/platform_stabilisation_register.md": (
        "schema and migration ownership boundaries",
        "docs/schema_migration_ownership_matrix.md",
        "scripts\\schema_migration_contract_check.py",
    ),
    "scripts/platform_documentation_contract_check.py": (
        "docs/schema_migration_ownership_matrix.md",
        "Schema and Migration Ownership Matrix",
        "schema_migration_contract_check.py",
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

    print("Schema/migration contract check")
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
