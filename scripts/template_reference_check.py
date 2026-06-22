"""Check that literal render_template() calls point at existing templates.

This is intentionally conservative: it only checks string-literal template names.
Dynamic template names are skipped because they need route-specific context.
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
TEMPLATE_DIR = APP_DIR / "templates"
SEARCH_DIRS = [APP_DIR / "routes", APP_DIR / "services"]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TemplateVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.references: list[tuple[int, str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        is_render_template = (
            isinstance(func, ast.Name)
            and func.id == "render_template"
        ) or (
            isinstance(func, ast.Attribute)
            and func.attr == "render_template"
        )

        if is_render_template and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                self.references.append((node.lineno, first_arg.value))

        self.generic_visit(node)


def module_name_to_path(module_name: str) -> Path | None:
    try:
        module = importlib.import_module(module_name)
    except Exception:
        return None

    module_file = getattr(module, "__file__", None)
    if not module_file:
        return None

    path = Path(module_file).resolve()
    if path.suffix != ".py":
        return None
    if APP_DIR not in path.parents and path != APP_DIR:
        return None
    return path


def active_view_files() -> list[Path]:
    from app import create_app

    flask_app = create_app()
    paths: set[Path] = set()

    for endpoint, view_func in flask_app.view_functions.items():
        if endpoint == "static":
            continue
        module_name = getattr(view_func, "__module__", "")
        path = module_name_to_path(module_name)
        if path:
            paths.add(path)

    return sorted(paths)


def main() -> int:
    missing: list[tuple[Path, int, str]] = []
    checked = 0
    skipped_parse_errors: list[tuple[Path, str]] = []

    for path in active_view_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            tree = ast.parse(path.read_text(encoding="cp1252"))
        except SyntaxError as exc:
            skipped_parse_errors.append((path, str(exc)))
            continue

        visitor = TemplateVisitor(path)
        visitor.visit(tree)

        for lineno, template_name in visitor.references:
            checked += 1
            if not (TEMPLATE_DIR / template_name).exists():
                missing.append((path, lineno, template_name))

    print("Template reference check")
    print(f"- Literal render_template calls checked: {checked}")
    print(f"- Python files skipped for syntax errors: {len(skipped_parse_errors)}")

    if skipped_parse_errors:
        for path, error in skipped_parse_errors:
            rel = path.relative_to(ROOT)
            print(f"  SKIPPED {rel}: {error}")

    if missing:
        print("\nMissing templates:")
        for path, lineno, template_name in missing:
            rel = path.relative_to(ROOT)
            print(f"- {rel}:{lineno} -> {template_name}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
