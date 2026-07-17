"""Guard that historical archive folders stay out of active runtime work."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROTECTED_TOKENS = ("legacy_archive", "Old_QR")

REQUIRED_FILES = (
    PROJECT_ROOT / "docs" / "architecture" / "archive_strategy.md",
    PROJECT_ROOT / "docs" / "legacy_cleanup_register.md",
    PROJECT_ROOT / "scripts" / "archive_inventory_check.py",
)

ACTIVE_SCAN_ROOTS = (
    PROJECT_ROOT / "app",
    PROJECT_ROOT / "migrations",
    PROJECT_ROOT / "scripts",
    PROJECT_ROOT / "run.py",
    PROJECT_ROOT / "Procfile",
    PROJECT_ROOT / "requirements.txt",
)

ALLOWED_REFERENCE_FILES = {
    PROJECT_ROOT / "scripts" / "archive_inventory_check.py",
    PROJECT_ROOT / "scripts" / "legacy_archive_isolation_check.py",
    PROJECT_ROOT / "scripts" / "phase3_readiness_check.py",
    PROJECT_ROOT / "scripts" / "platform_system_map_check.py",
    PROJECT_ROOT / "scripts" / "platform_documentation_contract_check.py",
}

SKIP_DIR_NAMES = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "legacy_archive",
    "node_modules",
    "Old_QR",
    "__pycache__",
    "venv",
}


def _safe_read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _walk_active_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    if not root.exists():
        return []

    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def _active_token_references() -> list[str]:
    references: list[str] = []
    for scan_root in ACTIVE_SCAN_ROOTS:
        for path in _walk_active_files(scan_root):
            if path.resolve() in ALLOWED_REFERENCE_FILES:
                continue

            content = _safe_read_text(path)
            if content is None:
                continue

            for token in PROTECTED_TOKENS:
                if token in content:
                    references.append(
                        f"{path.relative_to(PROJECT_ROOT)} references {token}"
                    )

    return sorted(set(references))


def _readiness_has_guard() -> bool:
    path = PROJECT_ROOT / "scripts" / "phase3_readiness_check.py"
    content = _safe_read_text(path) or ""
    return (
        "Archive Inventory Strict" in content
        and "archive_inventory_check.py --strict" in content
        and "Legacy Archive Isolation" in content
        and "legacy_archive_isolation_check.py" in content
    )


def main() -> int:
    failures: list[str] = []

    for path in REQUIRED_FILES:
        if not path.exists():
            failures.append(f"Missing archive governance file: {path.relative_to(PROJECT_ROOT)}")

    if not _readiness_has_guard():
        failures.append(
            "Phase 3 readiness runner does not include the legacy archive isolation guard."
        )

    references = _active_token_references()
    failures.extend(references)

    print("Legacy/archive isolation check")
    print(f"- Required archive governance files checked: {len(REQUIRED_FILES)}")
    print(f"- Active scan roots checked: {len(ACTIVE_SCAN_ROOTS)}")
    print(f"- Protected tokens: {', '.join(PROTECTED_TOKENS)}")
    print(f"- Active references found: {len(references)}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
