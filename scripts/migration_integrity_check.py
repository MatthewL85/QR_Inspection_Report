"""Verify Alembic migration files remain importable and revision-linked."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSIONS_DIR = ROOT / "migrations" / "versions"

EXPECTED_RECENT_CHAIN = (
    ("b5e6f7a8c9d0", "add_standalone_job_dockets.py"),
    ("c6d7e8f9a0b1", "add_external_work_order_reference.py"),
    ("d7e8f9a0b1c2", "add_standalone_docket_evidence.py"),
    ("e8f9a0b1c2d3", "add_company_work_order_prefix.py"),
    ("f9a0b1c2d3e4", "add_private_job_docket_work_logs.py"),
    ("a0b1c2d3e4f5", "add_core_document_templates.py"),
)

EXPECTED_RECENT_TOKENS = {
    "d7e8f9a0b1c2": ("evidence_links", "attachments_count"),
    "e8f9a0b1c2d3": ("work_order_prefix", "ix_companies_work_order_prefix"),
    "f9a0b1c2d3e4": (
        "job_docket_private_work_logs",
        "visibility_scope",
        "contractor_private",
    ),
    "a0b1c2d3e4f5": (
        "core_document_templates",
        "module_key",
        "document_type",
        "logo_mode",
    ),
}


@dataclass(frozen=True)
class MigrationRevision:
    path: Path
    revision: str
    down_revisions: tuple[str, ...]
    content: str


def _literal_assignment(tree: ast.Module, name: str) -> object:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"missing assignment: {name}")


def _normalise_down_revision(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (tuple, list)):
        return tuple(str(item) for item in value if item)
    raise ValueError(f"unsupported down_revision value: {value!r}")


def _load_revisions(failures: list[str]) -> list[MigrationRevision]:
    revisions: list[MigrationRevision] = []
    for path in sorted(VERSIONS_DIR.glob("*.py"), key=lambda item: item.name.lower()):
        try:
            content = path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(path))
            revision = _literal_assignment(tree, "revision")
            down_revision = _literal_assignment(tree, "down_revision")
        except Exception as exc:  # noqa: BLE001 - report every migration parse issue.
            failures.append(f"{path.name}: unable to parse revision metadata: {exc}")
            continue

        if not isinstance(revision, str) or not revision.strip():
            failures.append(f"{path.name}: revision must be a non-empty string")
            continue

        try:
            normalised_down = _normalise_down_revision(down_revision)
        except ValueError as exc:
            failures.append(f"{path.name}: {exc}")
            continue

        revisions.append(
            MigrationRevision(
                path=path,
                revision=revision,
                down_revisions=normalised_down,
                content=content,
            )
        )
    return revisions


def main() -> int:
    failures: list[str] = []
    revisions = _load_revisions(failures)
    by_revision: dict[str, MigrationRevision] = {}
    duplicate_revisions: dict[str, list[str]] = {}

    for migration in revisions:
        if migration.revision in by_revision:
            duplicate_revisions.setdefault(
                migration.revision,
                [by_revision[migration.revision].path.name],
            ).append(migration.path.name)
        by_revision[migration.revision] = migration

    for revision, paths in sorted(duplicate_revisions.items()):
        failures.append(f"Duplicate Alembic revision {revision}: {', '.join(paths)}")

    known_revisions = set(by_revision)
    for migration in revisions:
        for parent in migration.down_revisions:
            if parent not in known_revisions:
                failures.append(
                    f"{migration.path.name}: down_revision {parent} does not exist in migrations/versions"
                )

    children: dict[str, list[str]] = {}
    for migration in revisions:
        for parent in migration.down_revisions:
            children.setdefault(parent, []).append(migration.revision)
    heads = sorted(revision for revision in known_revisions if revision not in children)
    roots = sorted(migration.revision for migration in revisions if not migration.down_revisions)

    for index, (revision, filename_hint) in enumerate(EXPECTED_RECENT_CHAIN):
        migration = by_revision.get(revision)
        if not migration:
            failures.append(f"Missing recent migration revision {revision}")
            continue
        if filename_hint not in migration.path.name:
            failures.append(
                f"Recent migration {revision} has unexpected filename: {migration.path.name}"
            )
        if index > 0:
            expected_parent = EXPECTED_RECENT_CHAIN[index - 1][0]
            if migration.down_revisions != (expected_parent,):
                failures.append(
                    f"Recent migration {revision} should follow {expected_parent}, "
                    f"got {migration.down_revisions or 'root'}"
                )

    for revision, tokens in EXPECTED_RECENT_TOKENS.items():
        migration = by_revision.get(revision)
        if not migration:
            continue
        for token in tokens:
            if token not in migration.content:
                failures.append(f"Recent migration {revision} is missing token: {token}")

    latest_expected_revision = EXPECTED_RECENT_CHAIN[-1][0]
    if latest_expected_revision not in heads:
        failures.append(
            f"Recent platform migration head {latest_expected_revision} is not an Alembic head"
        )

    print("Migration integrity check")
    print(f"- Migration files parsed: {len(revisions)}")
    print(f"- Revision roots found: {len(roots)}")
    print(f"- Revision heads found: {len(heads)}")
    print("- Recent Contractor/Works chain checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
