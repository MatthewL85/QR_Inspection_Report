"""Verify the app module settings feed remains a read-only module boundary contract."""

from __future__ import annotations

from datetime import UTC, datetime
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


REQUIRED_TOP_LEVEL_KEYS = {
    "context_type",
    "contract_version",
    "generated_at",
    "read_only",
    "scope",
    "summary",
    "settings_policy",
    "registry",
    "mutation_policy",
    "source_references",
}

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


def main() -> int:
    from app import create_app
    from app.extensions import db
    from app.models.core.role import Role
    from app.models.core.user import User
    from app.models.onboarding.company import Company

    app = create_app()
    app.config["WTF_CSRF_ENABLED"] = False
    failures: list[str] = []
    marker = f"MODSET{datetime.now(UTC).strftime('%y%m%d%H%M%S')}"
    password = f"{marker}-Password1!"
    created_ids: dict[str, list[int]] = {"companies": [], "users": [], "roles": []}

    rule = next((item for item in app.url_map.iter_rules() if item.endpoint == "app_home.module_settings_feed"), None)
    if not rule:
        failures.append("Missing app_home.module_settings_feed route")
    else:
        if rule.rule != "/app/module-settings/feed.json":
            failures.append(f"app_home.module_settings_feed route changed to {rule.rule}")
        if "GET" not in (rule.methods or set()):
            failures.append("app_home.module_settings_feed does not allow GET")
        if {"POST", "PUT", "PATCH", "DELETE"}.intersection(rule.methods or set()):
            failures.append("app_home.module_settings_feed allows a mutating method")

    def _role(name: str) -> Role:
        role = Role.query.filter_by(name=name).first()
        if role:
            return role
        role = Role(name=name, description=f"Temporary role for {marker}")
        db.session.add(role)
        db.session.flush()
        created_ids["roles"].append(role.id)
        return role

    def _sign_in(client, actor: User) -> None:
        response = client.post(
            "/auth/login",
            data={"identifier": actor.email, "password": password},
        )
        if response.status_code not in {302, 303}:
            failures.append(f"Test login failed with HTTP {response.status_code}")

    with app.app_context():
        try:
            company = Company(
                name=f"{marker} Company",
                company_type="Property Management",
                country="Ireland",
                currency="EUR",
                subdomain=marker.lower(),
            )
            db.session.add(company)
            db.session.flush()
            created_ids["companies"].append(company.id)

            user = User(
                full_name=f"{marker} Super Admin",
                email=f"{marker.lower()}@example.invalid",
                username=f"{marker.lower()}_super_admin",
                password_hash=generate_password_hash(password),
                pin="0000",
                role_id=_role("Super Admin").id,
                company_id=company.id,
                is_active=True,
            )
            db.session.add(user)
            db.session.flush()
            created_ids["users"].append(user.id)
            db.session.commit()

            with app.test_client() as client:
                unauthenticated = client.get("/app/module-settings/feed.json")
                if unauthenticated.status_code not in {302, 401}:
                    failures.append(
                        "Unauthenticated module settings feed should redirect or reject, "
                        f"got HTTP {unauthenticated.status_code}"
                    )

            with app.test_client() as client:
                _sign_in(client, user)
                response = client.get("/app/module-settings/feed.json")
                if response.status_code != 200:
                    failures.append(
                        "/app/module-settings/feed.json returned "
                        f"HTTP {response.status_code} -> {response.headers.get('Location')}"
                    )
                payload = response.get_json(silent=True) or {}

            for key in REQUIRED_TOP_LEVEL_KEYS:
                if key not in payload:
                    failures.append(f"module settings payload missing: {key}")
            if payload.get("context_type") != "module_settings_registry":
                failures.append(f"Unexpected context_type: {payload.get('context_type')}")
            if payload.get("contract_version") != "phase3-module-settings-registry-v1":
                failures.append(f"Unexpected contract_version: {payload.get('contract_version')}")
            if payload.get("read_only") is not True:
                failures.append("Module settings feed must be read-only")

            scope = payload.get("scope") or {}
            if scope.get("company_id") != company.id:
                failures.append("Module settings scope did not preserve company_id")
            if scope.get("server_side_visibility") is not True:
                failures.append("Module settings feed must mark server-side visibility")

            registry = payload.get("registry") or []
            module_keys = {item.get("key") for item in registry if isinstance(item, dict)}
            missing_modules = REQUIRED_MODULE_KEYS - module_keys
            if missing_modules:
                failures.append(f"Module settings registry missing: {', '.join(sorted(missing_modules))}")
            for item in registry:
                for key in (
                    "key",
                    "name",
                    "settings_sections",
                    "document_template_types",
                    "shared_foundations",
                    "standalone_ready",
                    "connected_ready",
                ):
                    if key not in item:
                        failures.append(f"Module settings item {item.get('key')} missing: {key}")

            policy = payload.get("settings_policy") or {}
            if policy.get("core_owns_shared_foundations") is not True:
                failures.append("Module settings feed lost core shared foundation rule")
            if policy.get("modules_own_operational_settings") is not True:
                failures.append("Module settings feed lost module ownership rule")
            if policy.get("shared_engine_does_not_transfer_document_ownership") is not True:
                failures.append("Module settings feed lost document ownership boundary rule")

            mutation_policy = payload.get("mutation_policy") or {}
            if mutation_policy.get("feed_allows_mutation") is not False:
                failures.append("Module settings feed must not mutate")
            if mutation_policy.get("settings_changes_require_module_owner_route") is not True:
                failures.append("Module settings changes must use module owner routes")
            if mutation_policy.get("requires_csrf") is not True:
                failures.append("Module settings mutations must require CSRF")
            if mutation_policy.get("gar_may_execute_actions") is not False:
                failures.append("GAR must not execute module settings actions")

            sources = payload.get("source_references") or []
            if not any(item.get("model") == "ModuleSettingsContract" for item in sources):
                failures.append("Module settings source references missing ModuleSettingsContract")
            if not any(item.get("model") == "CoreDocumentTemplate" for item in sources):
                failures.append("Module settings source references missing CoreDocumentTemplate")

        finally:
            db.session.rollback()
            if created_ids["users"]:
                User.query.filter(User.id.in_(created_ids["users"])).delete(synchronize_session=False)
            if created_ids["companies"]:
                Company.query.filter(Company.id.in_(created_ids["companies"])).delete(synchronize_session=False)
            if created_ids["roles"]:
                Role.query.filter(Role.id.in_(created_ids["roles"])).delete(synchronize_session=False)
            db.session.commit()

    print("App module settings feed contract check")
    print("- Route checked: /app/module-settings/feed.json")
    print("- Read-only method checked: yes")
    print("- Authenticated company scope checked: yes")
    print("- Module ownership policy checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
