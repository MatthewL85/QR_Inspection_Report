"""Validate that declared platform modules have living manual pages."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


MANUAL_PAGE_BY_MODULE = {
    "core": "core_platform.md",
    "client_management": "client_manager.md",
    "unit_spine": "unit_information.md",
    "contract_manager": "contract_manager.md",
    "finance": "finance_logix.md",
    "works": "works_logix.md",
    "members": "members_logix.md",
    "contractor": "contractor_logix.md",
    "hr": "hr_logix.md",
    "director": "director_logix.md",
    "assistant": "assistant_workspace.md",
    "admin_portal": "admin_portal.md",
    "gar_ai": "gar_ai.md",
}


def main() -> int:
    from app.services.core.module_registry import module_contracts

    manual_dir = PROJECT_ROOT / "docs" / "manual"
    missing_pages: list[str] = []
    missing_contract_mappings: list[str] = []
    empty_pages: list[str] = []

    for contract in module_contracts():
        page_name = MANUAL_PAGE_BY_MODULE.get(contract.key)
        if not page_name:
            missing_contract_mappings.append(f"{contract.key} ({contract.name})")
            continue

        page = manual_dir / page_name
        if not page.exists():
            missing_pages.append(f"{contract.name}: docs/manual/{page_name}")
            continue

        content = page.read_text(encoding="utf-8").strip()
        if len(content) < 200:
            empty_pages.append(f"{contract.name}: docs/manual/{page_name}")

    print("Manual coverage check")
    print(f"- Module contracts checked: {len(module_contracts())}")
    print(f"- Manual mappings declared: {len(MANUAL_PAGE_BY_MODULE)}")

    if missing_contract_mappings or missing_pages or empty_pages:
        print("\nFAILED")
        for item in missing_contract_mappings:
            print(f"- Missing manual mapping: {item}")
        for item in missing_pages:
            print(f"- Missing manual page: {item}")
        for item in empty_pages:
            print(f"- Manual page too light: {item}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
