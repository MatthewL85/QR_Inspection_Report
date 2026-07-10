from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


REQUIRED_MODULE_KEYS = {
    "core_platform",
    "property_management_logix",
    "works_logix",
    "contractor_logix",
    "finance_logix",
    "hr_logix",
    "members_logix",
    "director_logix",
    "gar_ai",
}

REQUIRED_TEMPLATE_OWNERSHIP = {
    ("works_logix", "work_order"): "Property Management Logix",
    ("contractor_logix", "job_docket"): "Contractor Logix",
    ("contractor_logix", "payment_request"): "Contractor Logix",
    ("finance_logix", "invoice"): "Finance Logix",
    ("gar", "gar_report"): "GAR AI",
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise AssertionError(f"Missing {label}: {token}")


def main() -> None:
    from app import create_app
    from app.services.core.document_template_service import DOCUMENT_TEMPLATE_OWNERSHIP
    from app.services.core.module_settings_registry import (
        can_view_module_settings_centre,
        module_settings_registry,
        module_settings_registry_for_role,
    )

    app = create_app()
    endpoints = set(app.view_functions)
    registry = module_settings_registry()
    keys = {item["key"] for item in registry}
    missing = sorted(REQUIRED_MODULE_KEYS.difference(keys))
    if missing:
        raise AssertionError(f"Missing module settings registry keys: {', '.join(missing)}")

    for item in registry:
        if not item["settings_sections"]:
            raise AssertionError(f"{item['key']} has no settings sections")
        if not item["shared_foundations"]:
            raise AssertionError(f"{item['key']} has no shared foundations")
        if "standalone_ready" not in item or "connected_ready" not in item:
            raise AssertionError(f"{item['key']} missing standalone/connected readiness")

    contractor_keys = {item["key"] for item in module_settings_registry_for_role("Contractor")}
    if "contractor_logix" not in contractor_keys:
        raise AssertionError("Contractor role must see Contractor Logix settings")
    if "property_management_logix" in contractor_keys or "finance_logix" in contractor_keys:
        raise AssertionError("Contractor role must not see management or finance settings")
    member_keys = {item["key"] for item in module_settings_registry_for_role("Member")}
    if "members_logix" not in member_keys or "contractor_logix" in member_keys:
        raise AssertionError("Member role visibility should be portal-scoped")
    if can_view_module_settings_centre(type("Actor", (), {"role_name": "Contractor"})()):
        raise AssertionError("Contractor users must not access the combined settings centre")

    for key, expected_owner in REQUIRED_TEMPLATE_OWNERSHIP.items():
        ownership = DOCUMENT_TEMPLATE_OWNERSHIP.get(key)
        if not ownership:
            raise AssertionError(f"Missing document template ownership for {key}")
        if ownership.get("owner_module") != expected_owner:
            raise AssertionError(
                f"{key} owner should be {expected_owner}, got {ownership.get('owner_module')}"
            )

    if "settings.module_settings_index" not in endpoints:
        raise AssertionError("Missing settings.module_settings_index endpoint")

    template = read("app/templates/settings/modules/index.html")
    sidebar = read("app/templates/_partials/super_admin_sidebar.html")
    company_profile = read("app/templates/settings/company_profile/index.html")
    docs = "\n".join(
        [
            read("docs/manual/core_platform.md"),
            read("docs/manual/documents_logix.md"),
            read("docs/module_boundaries.md"),
        ]
    )

    for token in [
        "Module Settings Registry",
        "Standalone",
        "Connected",
        "Document Templates",
        "Shared Links",
        "Role Scope",
        "Full registry admin-only",
    ]:
        require(template, token, "module settings template")

    require(sidebar, "Module Settings", "settings sidebar")
    require(sidebar, "settings.module_settings_index", "settings sidebar endpoint")
    require(company_profile, "Open Module Settings Registry", "company profile link")

    for token in [
        "Module Settings Registry",
        "Core Platform owns shared foundations",
        "Each module owns its own operational settings",
        "shared engine does not transfer ownership",
        "role-aware settings visibility",
    ]:
        require(docs, token, "manual coverage")

    print("module settings registry check passed")


if __name__ == "__main__":
    main()
