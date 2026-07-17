"""Validate module service/feed integration contracts stay documented and wired."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = (
    "docs/module_contracts.md",
    "docs/platform_architecture.md",
    "docs/platform_stabilisation_register.md",
    "docs/manual/index.md",
    "scripts/module_dependency_boundary_check.py",
    "app/services/core/module_registry.py",
    "app/services/core/module_connections.py",
    "app/services/core/module_settings_registry.py",
    "app/services/works/work_order_docket_service.py",
    "app/services/contractor/job_docket_service.py",
    "app/services/members/works_context.py",
    "app/services/gar/source_queries.py",
)

REQUIRED_REFERENCES = {
    "docs/module_contracts.md": (
        "Dependency Rule",
        "source-backed service or feed",
        "Do not connect modules by importing one module's routes",
        "Routes are presentation and workflow entry points; they are not integration APIs.",
        "Do not import services from models.",
        "Allowed cross-module service dependencies must be explicit.",
        "declare the dependency",
        "module_service_contract_check.py",
    ),
    "docs/platform_architecture.md": (
        "source-backed service/feed contract",
        "module_service_contract_check.py",
        "module_dependency_boundary_check.py",
        "models stay persistence-only",
        "services do not import routes",
    ),
    "docs/platform_stabilisation_register.md": (
        "service-led integration",
        "source-backed feeds",
        "module_service_contract_check.py",
        "module_dependency_boundary_check.py",
    ),
    "docs/manual/index.md": (
        "module service/feed contract",
        "module_service_contract_check.py",
        "service/API driven",
    ),
    "scripts/phase3_readiness_check.py": (
        "Module Service Contract",
        "module_service_contract_check.py",
    ),
    "scripts/phase3_runner_contract_check.py": (
        "Module Service Contract",
    ),
}


def main() -> int:
    failures: list[str] = []

    for relative_path in REQUIRED_FILES:
        if not (PROJECT_ROOT / relative_path).exists():
            failures.append(f"Missing required service contract file: {relative_path}")

    for relative_path, required_phrases in REQUIRED_REFERENCES.items():
        path = PROJECT_ROOT / relative_path
        if not path.exists():
            failures.append(f"Missing required reference file: {relative_path}")
            continue

        content = path.read_text(encoding="utf-8")
        for phrase in required_phrases:
            if phrase not in content:
                failures.append(f"{relative_path} is missing: {phrase}")

    print("Module service contract check")
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
