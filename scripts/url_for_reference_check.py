"""Check that literal url_for() references point at registered endpoints.

This is intentionally conservative: it checks only string-literal endpoint
names and skips dynamic or relative blueprint references that need runtime
context.
"""

from __future__ import annotations

import ast
import importlib
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
TEMPLATE_DIR = APP_DIR / "templates"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


TEMPLATE_URL_FOR_RE = re.compile(r"url_for\(\s*(['\"])(?P<endpoint>[^'\"]+)\1")
JINJA_TEMPLATE_REF_RE = re.compile(
    r"{%\s*(?:extends|include|import)\s+(['\"])(?P<template>[^'\"]+)\1"
    r"|{%\s*from\s+(['\"])(?P<from_template>[^'\"]+)\3"
)


class UrlForVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.references: list[tuple[int, str]] = []
        self.rendered_templates: list[str] = []
        self.dynamic_count = 0

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        is_url_for = (
            isinstance(func, ast.Name)
            and func.id == "url_for"
        ) or (
            isinstance(func, ast.Attribute)
            and func.attr == "url_for"
        )

        if is_url_for and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                self.references.append((node.lineno, first_arg.value))
            else:
                self.dynamic_count += 1

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
                self.rendered_templates.append(first_arg.value)

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


def active_view_files(flask_app) -> list[Path]:
    paths: set[Path] = set()

    for endpoint, view_func in flask_app.view_functions.items():
        if endpoint == "static":
            continue
        module_name = getattr(view_func, "__module__", "")
        path = module_name_to_path(module_name)
        if path:
            paths.add(path)

    return sorted(paths)


def check_endpoint(endpoint: str, valid_endpoints: set[str]) -> bool | None:
    if endpoint == "static":
        return True
    if endpoint.startswith("."):
        return None
    return endpoint in valid_endpoints


def is_guarded_optional_reference(path: Path, endpoint: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="cp1252")

    return (
        f"'{endpoint}' in current_app.view_functions" in text
        or f'"{endpoint}" in current_app.view_functions' in text
    )


def read_template_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1252").splitlines()


def template_dependency_closure(template_names: set[str]) -> set[Path]:
    pending = list(template_names)
    paths: set[Path] = set()
    seen_names: set[str] = set()

    while pending:
        template_name = pending.pop()
        if template_name in seen_names:
            continue
        seen_names.add(template_name)

        path = TEMPLATE_DIR / template_name
        if not path.exists():
            continue

        paths.add(path)
        for line in read_template_lines(path):
            for match in JINJA_TEMPLATE_REF_RE.finditer(line):
                dependency = match.group("template") or match.group("from_template")
                if dependency and dependency not in seen_names:
                    pending.append(dependency)

    return paths


def template_references(paths: set[Path]) -> tuple[list[tuple[Path, int, str]], int]:
    references: list[tuple[Path, int, str]] = []
    skipped_relative = 0

    for path in sorted(paths):
        for lineno, line in enumerate(read_template_lines(path), start=1):
            for match in TEMPLATE_URL_FOR_RE.finditer(line):
                endpoint = match.group("endpoint")
                if endpoint.startswith("."):
                    skipped_relative += 1
                    continue
                references.append((path, lineno, endpoint))

    return references, skipped_relative


def main() -> int:
    from app import create_app

    flask_app = create_app()
    valid_endpoints = set(flask_app.view_functions)
    missing: list[tuple[Path, int, str, str]] = []
    python_checked = 0
    template_checked = 0
    skipped_dynamic = 0
    skipped_relative = 0
    skipped_guarded_optional = 0
    rendered_templates: set[str] = set()
    skipped_parse_errors: list[tuple[Path, str]] = []

    for path in active_view_files(flask_app):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            tree = ast.parse(path.read_text(encoding="cp1252"))
        except SyntaxError as exc:
            skipped_parse_errors.append((path, str(exc)))
            continue

        visitor = UrlForVisitor(path)
        visitor.visit(tree)
        skipped_dynamic += visitor.dynamic_count
        rendered_templates.update(visitor.rendered_templates)

        for lineno, endpoint in visitor.references:
            result = check_endpoint(endpoint, valid_endpoints)
            if result is None:
                skipped_relative += 1
                continue
            python_checked += 1
            if not result:
                missing.append((path, lineno, endpoint, "python"))

    active_template_paths = template_dependency_closure(rendered_templates)
    refs, template_relative_count = template_references(active_template_paths)
    skipped_relative += template_relative_count
    for path, lineno, endpoint in refs:
        result = check_endpoint(endpoint, valid_endpoints)
        if result is None:
            skipped_relative += 1
            continue
        template_checked += 1
        if not result:
            if is_guarded_optional_reference(path, endpoint):
                skipped_guarded_optional += 1
                continue
            missing.append((path, lineno, endpoint, "template"))

    print("URL reference check")
    print(f"- Active endpoints registered: {len(valid_endpoints)}")
    print(f"- Python url_for calls checked: {python_checked}")
    print(f"- Template url_for calls checked: {template_checked}")
    print(f"- Active rendered templates checked: {len(active_template_paths)}")
    print(f"- Dynamic references skipped: {skipped_dynamic}")
    print(f"- Relative blueprint references skipped: {skipped_relative}")
    print(f"- Guarded optional references skipped: {skipped_guarded_optional}")
    print(f"- Python files skipped for syntax errors: {len(skipped_parse_errors)}")

    if skipped_parse_errors:
        for path, error in skipped_parse_errors:
            rel = path.relative_to(ROOT)
            print(f"  SKIPPED {rel}: {error}")

    if missing:
        print("\nMissing endpoints:")
        for path, lineno, endpoint, source_type in missing:
            rel = path.relative_to(ROOT)
            print(f"- {rel}:{lineno} [{source_type}] -> {endpoint}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
