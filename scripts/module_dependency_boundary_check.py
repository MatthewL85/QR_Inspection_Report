"""Validate module dependency boundaries stay explicit and service-led."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SERVICE_ROOT = PROJECT_ROOT / "app" / "services"
MODEL_ROOT = PROJECT_ROOT / "app" / "models"

KNOWN_SERVICE_MODULES = {
    "capex",
    "contract",
    "core",
    "dashboard",
    "gar",
    "members",
    "works",
}

ALLOWED_SERVICE_DEPENDENCIES = {
    ("contract", "contract"),
    ("core", "core"),
    ("core", "gar"),
    ("dashboard", "contract"),
    ("gar", "contract"),
    ("gar", "core"),
    ("gar", "members"),
    ("gar", "works"),
    ("members", "members"),
    ("members", "works"),
    ("works", "gar"),
    ("works", "works"),
}

SKIP_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache"}


def python_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [
        path
        for path in root.rglob("*.py")
        if not any(part in SKIP_DIRS for part in path.parts)
    ]


def module_for_service_path(path: Path) -> str | None:
    try:
        relative = path.relative_to(SERVICE_ROOT)
    except ValueError:
        return None
    if not relative.parts:
        return None
    module = relative.parts[0]
    return module if module in KNOWN_SERVICE_MODULES else None


def imported_modules(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return set()

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def service_module_from_import(import_name: str) -> str | None:
    prefix = "app.services."
    if not import_name.startswith(prefix):
        return None
    remainder = import_name[len(prefix) :]
    module = remainder.split(".", 1)[0]
    return module if module in KNOWN_SERVICE_MODULES else None


def main() -> int:
    failures: list[str] = []
    service_edges: set[tuple[str, str]] = set()
    service_files_checked = 0
    model_files_checked = 0

    for path in python_files(SERVICE_ROOT):
        service_files_checked += 1
        source_module = module_for_service_path(path)
        imports = imported_modules(path)

        for import_name in imports:
            if import_name == "app.routes" or import_name.startswith("app.routes."):
                failures.append(
                    f"Service file imports routes: {path.relative_to(PROJECT_ROOT)} -> {import_name}"
                )

            target_module = service_module_from_import(import_name)
            if source_module and target_module:
                edge = (source_module, target_module)
                service_edges.add(edge)
                if edge not in ALLOWED_SERVICE_DEPENDENCIES:
                    failures.append(
                        "Undeclared service dependency: "
                        f"{source_module} -> {target_module} in {path.relative_to(PROJECT_ROOT)}"
                    )

    for path in python_files(MODEL_ROOT):
        model_files_checked += 1
        imports = imported_modules(path)
        for import_name in imports:
            if import_name == "app.routes" or import_name.startswith("app.routes."):
                failures.append(
                    f"Model file imports routes: {path.relative_to(PROJECT_ROOT)} -> {import_name}"
                )
            if import_name == "app.services" or import_name.startswith("app.services."):
                failures.append(
                    f"Model file imports services: {path.relative_to(PROJECT_ROOT)} -> {import_name}"
                )

    print("Module dependency boundary check")
    print(f"- Service files checked: {service_files_checked}")
    print(f"- Model files checked: {model_files_checked}")
    print(f"- Declared service dependency edges observed: {len(service_edges)}")
    for source, target in sorted(service_edges):
        print(f"  - {source} -> {target}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
