"""Validate high-risk module access and settings ownership boundaries.

This check protects the current stabilisation rule: modules may connect through
shared IDs and governed services, but users must not use settings links or weak
route guards to enter another module/company workspace.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.services.core.module_settings_registry import module_settings_registry_for_role


app = create_app()

MANAGEMENT_ROLES_WITHOUT_CONTRACTOR = (
    "Property Manager",
    "Assistant",
    "Financial Controller",
)

CONTRACTOR_FORBIDDEN_MODULES = {
    "property_management_logix",
    "works_logix",
    "finance_logix",
    "members_logix",
    "director_logix",
}

MEMBER_FORBIDDEN_MODULES = {
    "property_management_logix",
    "works_logix",
    "contractor_logix",
    "finance_logix",
    "director_logix",
}

REQUIRED_ENDPOINT_PREFIXES = {
    "contractor.contractor_settings": "/contractor/settings",
    "contractor.contractor_settings_profile": "/contractor/settings/company-profile",
    "contractor.contractor_settings_connections": "/contractor/settings/connections",
    "contractor.contractor_document_templates": "/contractor/settings/document-templates",
    "contractor.contractor_settings_bank_accounts": "/contractor/settings/bank-accounts",
    "contractor.contractor_settings_insurance": "/contractor/settings/insurance",
    "finance.settings_connections": "/finance/settings/connections",
    "settings.module_settings_index": "/settings/modules",
}

CONTRACTOR_TEMPLATE_FORBIDDEN_SETTINGS_LINKS = (
    "url_for('settings.profile",
    'url_for("settings.profile',
    "url_for('settings.branding",
    'url_for("settings.branding',
    "url_for('settings.document_templates",
    'url_for("settings.document_templates',
    "url_for('settings.bank",
    'url_for("settings.bank',
    "url_for('settings.insurance",
    'url_for("settings.insurance',
    "url_for('settings.connections",
    'url_for("settings.connections',
)


def _visible_keys_for_role(role_name: str) -> set[str]:
    return {item["key"] for item in module_settings_registry_for_role(role_name)}


def _rules_by_endpoint() -> dict[str, list[str]]:
    endpoint_rules: dict[str, list[str]] = {}
    for rule in app.url_map.iter_rules():
        endpoint_rules.setdefault(rule.endpoint, []).append(rule.rule)
    return endpoint_rules


def _check_registry_visibility(failures: list[str]) -> None:
    for role_name in MANAGEMENT_ROLES_WITHOUT_CONTRACTOR:
        visible = _visible_keys_for_role(role_name)
        if "contractor_logix" in visible:
            failures.append(f"{role_name} registry exposes contractor_logix")

    contractor_visible = _visible_keys_for_role("Contractor")
    forbidden_for_contractor = sorted(CONTRACTOR_FORBIDDEN_MODULES & contractor_visible)
    if forbidden_for_contractor:
        failures.append(
            "Contractor registry exposes management modules: "
            + ", ".join(forbidden_for_contractor)
        )

    for role_name in ("Member", "Resident"):
        visible = _visible_keys_for_role(role_name)
        forbidden = sorted(MEMBER_FORBIDDEN_MODULES & visible)
        if forbidden:
            failures.append(f"{role_name} registry exposes restricted modules: {', '.join(forbidden)}")


def _check_endpoint_ownership(failures: list[str]) -> None:
    endpoint_rules = _rules_by_endpoint()
    for endpoint, required_prefix in REQUIRED_ENDPOINT_PREFIXES.items():
        rules = endpoint_rules.get(endpoint)
        if not rules:
            failures.append(f"Missing expected endpoint: {endpoint}")
            continue
        if not any(rule.startswith(required_prefix) for rule in rules):
            failures.append(
                f"{endpoint} is not owned by expected route prefix {required_prefix}: {rules}"
            )


def _check_contractor_template_links(failures: list[str]) -> None:
    template_root = PROJECT_ROOT / "app" / "templates" / "contractor"
    for path in template_root.rglob("*.html"):
        content = path.read_text(encoding="utf-8")
        for forbidden in CONTRACTOR_TEMPLATE_FORBIDDEN_SETTINGS_LINKS:
            if forbidden in content:
                failures.append(
                    f"Contractor template links to shared settings endpoint in {path.relative_to(PROJECT_ROOT)}: {forbidden}"
                )


def _check_contractor_route_guards(failures: list[str]) -> None:
    path = PROJECT_ROOT / "app" / "routes" / "contractor.py"
    content = path.read_text(encoding="utf-8")

    route_pattern = re.compile(
        r"(?P<decorators>(?:@[^\n]+\n)+)def (?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\(",
        re.MULTILINE,
    )
    guarded = 0
    contractor_routes = 0
    for match in route_pattern.finditer(content):
        decorators = match.group("decorators")
        if "@contractor_bp." not in decorators:
            continue
        contractor_routes += 1
        if "@login_required(role='Contractor')" in decorators or '@login_required(role="Contractor")' in decorators:
            guarded += 1
            continue
        failures.append(
            f"Contractor route {match.group('name')} is missing login_required(role='Contractor')"
        )

    if contractor_routes == 0:
        failures.append("No contractor routes were detected for guard validation")

    print(f"- Contractor routes checked: {contractor_routes}")
    print(f"- Contractor routes with Contractor guard: {guarded}")


def main() -> int:
    failures: list[str] = []

    _check_registry_visibility(failures)
    _check_endpoint_ownership(failures)
    _check_contractor_template_links(failures)
    _check_contractor_route_guards(failures)

    print("Module access/security boundary check")
    print(f"- Registry roles checked: {len(MANAGEMENT_ROLES_WITHOUT_CONTRACTOR) + 3}")
    print(f"- Required endpoint ownership checks: {len(REQUIRED_ENDPOINT_PREFIXES)}")
    print(f"- Contractor templates scanned: {len(list((PROJECT_ROOT / 'app' / 'templates' / 'contractor').rglob('*.html')))}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
