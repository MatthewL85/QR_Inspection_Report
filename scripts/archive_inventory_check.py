"""Read-only inventory for legacy/archive material in the workspace."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

LEGACY_TOKENS = (
    "old",
    "legacy",
    "archive",
    "backup",
    "deprecated",
    "historical",
    "previous",
)

SKIP_DIR_NAMES = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "node_modules",
    "__pycache__",
    "venv",
}

ACTIVE_SCAN_PATHS = [
    PROJECT_ROOT / "app",
    PROJECT_ROOT / "migrations",
    PROJECT_ROOT / "scripts",
    PROJECT_ROOT / "run.py",
    PROJECT_ROOT / "Procfile",
    PROJECT_ROOT / "requirements.txt",
]

SELF_PATH = PROJECT_ROOT / "scripts" / "archive_inventory_check.py"
GOVERNANCE_FILES = {
    PROJECT_ROOT / "docs" / "architecture" / "archive_strategy.md",
    PROJECT_ROOT / "docs" / "legacy_cleanup_register.md",
    PROJECT_ROOT / "docs" / "phase_2_legacy_review.md",
    PROJECT_ROOT / "scripts" / "platform_system_map_check.py",
    SELF_PATH,
}


def is_legacy_name(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    name = path.name.lower()
    return any(
        token in parts
        or name.startswith(f"{token}_")
        or name.endswith(f"_{token}")
        or f"_{token}_" in name
        for token in LEGACY_TOKENS
    )


def walk_files(root: Path) -> list[Path]:
    files: list[Path] = []
    if root.is_file():
        return [root]
    if not root.exists():
        return files

    for path in root.rglob("*"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def safe_read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    except OSError:
        return None


def top_level_legacy_roots() -> list[Path]:
    roots: list[Path] = []
    for path in PROJECT_ROOT.iterdir():
        if path.name in SKIP_DIR_NAMES:
            continue
        if is_legacy_name(path):
            roots.append(path)
    return sorted(roots, key=lambda item: item.name.lower())


def legacy_candidate_files() -> list[Path]:
    candidates: list[Path] = []
    for path in PROJECT_ROOT.rglob("*"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path in GOVERNANCE_FILES:
            continue
        if path.is_file() and is_legacy_name(path.relative_to(PROJECT_ROOT)):
            candidates.append(path)
    return sorted(candidates, key=lambda item: str(item).lower())


def active_references_to_roots(legacy_roots: list[Path]) -> list[str]:
    root_names = [root.name for root in legacy_roots]
    references: list[str] = []

    for scan_path in ACTIVE_SCAN_PATHS:
        for file_path in walk_files(scan_path):
            if file_path in GOVERNANCE_FILES:
                continue
            content = safe_read_text(file_path)
            if content is None:
                continue

            for root_name in root_names:
                if root_name in content:
                    rel_path = file_path.relative_to(PROJECT_ROOT)
                    references.append(f"{rel_path} references {root_name}")

    return sorted(set(references))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a failing exit code when active code references legacy roots.",
    )
    args = parser.parse_args()

    legacy_roots = top_level_legacy_roots()
    candidates = legacy_candidate_files()
    references = active_references_to_roots(legacy_roots)

    print("Archive inventory check")
    print(f"- Legacy/archive top-level roots: {len(legacy_roots)}")
    for root in legacy_roots:
        marker = "directory" if root.is_dir() else "file"
        print(f"  - {root.relative_to(PROJECT_ROOT)} ({marker})")

    print(f"- Candidate legacy/archive files found: {len(candidates)}")
    for path in candidates[:80]:
        print(f"  - {path.relative_to(PROJECT_ROOT)}")
    if len(candidates) > 80:
        print(f"  - ... {len(candidates) - 80} more not shown")

    print(f"- Active references to legacy roots: {len(references)}")
    for reference in references:
        print(f"  - {reference}")

    print("\nNo files were moved or deleted.")

    if args.strict and references:
        print("\nFAILED")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
