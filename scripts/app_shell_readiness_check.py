"""Verify Phase 3E app/PWA shell readiness.

This is intentionally a shell contract, not a separate mobile application.
Future PWA/native surfaces must use the same governed feeds and workflow routes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


REQUIRED_FEEDS = {
    "app_home.capabilities_feed": "/app/capabilities/feed.json",
    "app_home.feed": "/app/home/feed.json",
    "app_home.health_feed": "/app/health/feed.json",
    "notifications.feed": "/notifications/feed.json",
    "members.works_feed": "/members/works/feed.json",
    "members.gar_feed": "/members/gar/feed.json",
    "contractor.work_orders_feed": "/contractor/work-orders/feed.json",
    "contractor.gar_feed": "/contractor/gar/feed.json",
    "super_admin.work_orders_feed": "/super-admin/work-orders/feed.json",
    "super_admin.gar_insights_feed": "/super-admin/gar-insights/feed.json",
}

REQUIRED_TEMPLATE_TOKENS = (
    'rel="manifest"',
    "manifest.webmanifest",
    "apple-mobile-web-app-capable",
    "apple-touch-icon",
    "register_app_shell.js",
)


def _check_manifest(failures: list[str]) -> None:
    manifest_path = PROJECT_ROOT / "app/static/manifest.webmanifest"
    if not manifest_path.exists():
        failures.append("Missing app/static/manifest.webmanifest")
        return

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"manifest.webmanifest is invalid JSON: {exc}")
        return

    expected = {
        "name": "LogixPM",
        "short_name": "LogixPM",
        "start_url": "/auth/login",
        "scope": "/",
        "display": "standalone",
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            failures.append(f"manifest {key} changed from {value!r} to {manifest.get(key)!r}")

    if not manifest.get("theme_color"):
        failures.append("manifest is missing theme_color")
    if not isinstance(manifest.get("icons"), list) or len(manifest["icons"]) < 2:
        failures.append("manifest should expose at least two app icons")


def _check_static_shell_files(failures: list[str]) -> None:
    service_worker = PROJECT_ROOT / "app/static/app-shell-sw.js"
    register_script = PROJECT_ROOT / "app/static/js/register_app_shell.js"

    if not service_worker.exists():
        failures.append("Missing app/static/app-shell-sw.js")
    else:
        text = service_worker.read_text(encoding="utf-8")
        for token in ("install", "activate", "fetch", "/static/"):
            if token not in text:
                failures.append(f"Service worker missing token: {token}")

    if not register_script.exists():
        failures.append("Missing app/static/js/register_app_shell.js")
    else:
        text = register_script.read_text(encoding="utf-8")
        for token in ("serviceWorker", "/app-shell-sw.js", "scope: \"/\""):
            if token not in text:
                failures.append(f"App shell registration missing token: {token}")


def _check_templates(failures: list[str]) -> None:
    templates = (
        PROJECT_ROOT / "app/templates/base.html",
        PROJECT_ROOT / "app/templates/layouts/super_admin_base.html",
        PROJECT_ROOT / "app/templates/layouts/auth_base.html",
    )
    for template in templates:
        if not template.exists():
            failures.append(f"Missing layout template: {template}")
            continue
        text = template.read_text(encoding="utf-8", errors="replace")
        for token in REQUIRED_TEMPLATE_TOKENS:
            if token not in text:
                failures.append(f"{template.name} missing app-shell token: {token}")


def _check_routes(failures: list[str]) -> None:
    from app import create_app

    app = create_app()
    rules = {rule.endpoint: rule for rule in app.url_map.iter_rules()}

    service_worker_rule = next((rule for rule in app.url_map.iter_rules() if rule.rule == "/app-shell-sw.js"), None)
    if not service_worker_rule:
        failures.append("Missing /app-shell-sw.js service-worker route")
    elif {"POST", "PUT", "PATCH", "DELETE"}.intersection(service_worker_rule.methods or set()):
        failures.append("/app-shell-sw.js allows a mutating method")

    for endpoint, expected_rule in REQUIRED_FEEDS.items():
        rule = rules.get(endpoint)
        if not rule:
            failures.append(f"Missing app-ready feed endpoint: {endpoint}")
            continue
        if rule.rule != expected_rule:
            failures.append(f"{endpoint} route changed from {expected_rule} to {rule.rule}")
        if "GET" not in (rule.methods or set()):
            failures.append(f"{endpoint} does not allow GET")
        if {"POST", "PUT", "PATCH", "DELETE"}.intersection(rule.methods or set()):
            failures.append(f"{endpoint} feed allows mutating methods")

    with app.test_client() as client:
        response = client.get("/app-shell-sw.js")
        if response.status_code != 200:
            failures.append(f"/app-shell-sw.js returned HTTP {response.status_code}")
        if response.headers.get("Service-Worker-Allowed") != "/":
            failures.append("/app-shell-sw.js did not set Service-Worker-Allowed: /")
        if "javascript" not in response.headers.get("Content-Type", ""):
            failures.append("/app-shell-sw.js did not return JavaScript content")


def main() -> int:
    failures: list[str] = []
    _check_manifest(failures)
    _check_static_shell_files(failures)
    _check_templates(failures)
    _check_routes(failures)

    print("App shell readiness check")
    print("- Manifest checked: yes")
    print("- Service worker shell checked: yes")
    print(f"- App-ready feeds checked: {len(REQUIRED_FEEDS)}")
    print("- Layout install metadata checked: 3")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
