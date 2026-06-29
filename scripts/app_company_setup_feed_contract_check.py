"""Verify the company setup readiness feed remains a safe read-only app contract."""

from __future__ import annotations

from datetime import UTC, datetime
import sys
from pathlib import Path
from werkzeug.security import generate_password_hash


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


REQUIRED_TOP_LEVEL_KEYS = (
    "context_type",
    "contract_version",
    "read_only",
    "scope",
    "readiness",
    "governed_actions",
    "mutation_policy",
    "source_references",
)
REQUIRED_SCOPE_KEYS = ("company_id", "company_name", "organisation_uid", "server_side_visibility")
REQUIRED_READINESS_KEYS = (
    "company_id",
    "organisation_uid",
    "identity_ready",
    "enabled_module_count",
    "active_connection_count",
    "has_connections",
    "enabled_module_names",
    "modules",
)
REQUIRED_MODULE_KEYS = (
    "key",
    "name",
    "contract_status",
    "is_enabled",
    "subscription_status",
    "requires_connection",
    "dashboard_endpoint",
)
REQUIRED_ACTION_KEYS = (
    "key",
    "label",
    "method",
    "endpoint",
    "url",
    "requires_csrf",
    "required_roles",
    "mutates",
    "source_service",
)
REQUIRED_ACTIONS = {
    "enable_module",
    "link_contractor_organisation",
    "create_connection_invite",
    "accept_connection_invite",
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
    marker = f"COMPSETUP{datetime.now(UTC).strftime('%y%m%d%H%M%S')}"
    password = f"{marker}-Password1!"
    ids: dict[str, list[int]] = {"companies": [], "users": []}
    created_role_ids: list[int] = []

    rule = next((item for item in app.url_map.iter_rules() if item.endpoint == "app_home.company_setup_feed"), None)
    if not rule:
        failures.append("Missing app_home.company_setup_feed route")
    else:
        if rule.rule != "/app/company-setup/feed.json":
            failures.append(f"app_home.company_setup_feed route changed to {rule.rule}")
        if "GET" not in (rule.methods or set()):
            failures.append("app_home.company_setup_feed does not allow GET")
        if {"POST", "PUT", "PATCH", "DELETE"}.intersection(rule.methods or set()):
            failures.append("app_home.company_setup_feed allows a mutating method")

    def _role(name: str) -> Role:
        existing = Role.query.filter_by(name=name).first()
        if existing:
            return existing
        role = Role(name=name, description=f"Temporary role for {marker}")
        db.session.add(role)
        db.session.flush()
        created_role_ids.append(role.id)
        return role

    def _sign_in(client, actor: User) -> None:
        login_response = client.post(
            "/auth/login",
            data={
                "identifier": actor.email,
                "password": password,
            },
        )
        if login_response.status_code not in {302, 303}:
            failures.append(
                f"Test login failed with HTTP {login_response.status_code}"
            )

    def _delete_by_ids(model, item_ids: list[int]) -> None:
        if item_ids:
            model.query.filter(model.id.in_(item_ids)).delete(synchronize_session=False)

    with app.app_context():
        Company.query.filter(Company.subdomain.ilike("compsetup%")).delete(synchronize_session=False)
        User.query.filter(User.username.ilike("compsetup%")).delete(synchronize_session=False)
        db.session.commit()

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
            ids["companies"].append(company.id)

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
            ids["users"].append(user.id)
            db.session.commit()

            with app.test_client() as client:
                unauthenticated = client.get("/app/company-setup/feed.json")
                if unauthenticated.status_code not in {302, 401}:
                    failures.append(
                        f"Unauthenticated company setup feed should redirect or reject, got HTTP {unauthenticated.status_code}"
                    )

            with app.test_client() as client:
                _sign_in(client, user)
                home_response = client.get("/app/home/feed.json")
                if home_response.status_code != 200:
                    failures.append(
                        "/app/home/feed.json preflight returned "
                        f"HTTP {home_response.status_code} -> {home_response.headers.get('Location')}"
                    )
                response = client.get("/app/company-setup/feed.json")
                if response.status_code != 200:
                    failures.append(
                        "/app/company-setup/feed.json returned "
                        f"HTTP {response.status_code} -> {response.headers.get('Location')}"
                    )
                payload = response.get_json(silent=True) or {}

            for key in REQUIRED_TOP_LEVEL_KEYS:
                if key not in payload:
                    failures.append(f"company setup payload missing: {key}")
            if payload.get("context_type") != "company_setup_readiness":
                failures.append(f"Unexpected context_type: {payload.get('context_type')}")
            if payload.get("contract_version") != "phase3-company-setup-readiness-v1":
                failures.append(f"Unexpected contract_version: {payload.get('contract_version')}")
            if payload.get("read_only") is not True:
                failures.append("Company setup feed must be read-only")

            scope = payload.get("scope") or {}
            for key in REQUIRED_SCOPE_KEYS:
                if key not in scope:
                    failures.append(f"company setup scope missing: {key}")
            if scope.get("company_id") != company.id:
                failures.append("Company setup scope did not preserve company_id")
            if not scope.get("organisation_uid"):
                failures.append("Company setup scope missing organisation_uid")
            if scope.get("server_side_visibility") is not True:
                failures.append("Company setup feed must mark server-side visibility")

            readiness = payload.get("readiness") or {}
            for key in REQUIRED_READINESS_KEYS:
                if key not in readiness:
                    failures.append(f"company setup readiness missing: {key}")
            if readiness.get("company_id") != company.id:
                failures.append("Company setup readiness did not preserve company_id")
            if readiness.get("identity_ready") is not True:
                failures.append("Company setup readiness should mark identity ready")
            if not readiness.get("organisation_uid"):
                failures.append("Company setup readiness missing organisation_uid")
            modules = readiness.get("modules") or []
            if len(modules) < 10:
                failures.append("Company setup readiness module list is unexpectedly low")
            module_keys = {module.get("key") for module in modules if isinstance(module, dict)}
            for required_module in ("core", "works", "contractor", "members", "gar_ai"):
                if required_module not in module_keys:
                    failures.append(f"company setup readiness missing module: {required_module}")
            for module in modules:
                for key in REQUIRED_MODULE_KEYS:
                    if key not in module:
                        failures.append(f"company setup module {module.get('key')} missing: {key}")

            sources = payload.get("source_references") or []
            if not any(source.get("model") == "Company" and source.get("record_id") == company.id for source in sources):
                failures.append("Company setup source_references missing Company")
            if not any(source.get("model") == "ModuleContract" for source in sources):
                failures.append("Company setup source_references missing ModuleContract")
            if not any(source.get("model") == "OrganisationConnection" for source in sources):
                failures.append("Company setup source_references missing OrganisationConnection")

            actions = payload.get("governed_actions") or []
            action_keys = {action.get("key") for action in actions if isinstance(action, dict)}
            missing_actions = REQUIRED_ACTIONS - action_keys
            if missing_actions:
                failures.append(f"Company setup governed_actions missing: {', '.join(sorted(missing_actions))}")
            for action in actions:
                for key in REQUIRED_ACTION_KEYS:
                    if key not in action:
                        failures.append(f"Company setup action {action.get('key')} missing: {key}")
                if action.get("method") != "POST":
                    failures.append(f"Company setup action {action.get('key')} must use POST")
                if action.get("requires_csrf") is not True:
                    failures.append(f"Company setup action {action.get('key')} must require CSRF")
                if "Super Admin" not in (action.get("required_roles") or []):
                    failures.append(f"Company setup action {action.get('key')} must require Super Admin")
                if not str(action.get("url") or "").startswith("/super-admin/organisation-connections"):
                    failures.append(f"Company setup action {action.get('key')} URL is outside setup boundary")

            mutation_policy = payload.get("mutation_policy") or {}
            if mutation_policy.get("feed_allows_mutation") is not False:
                failures.append("Company setup feed must not allow mutations")
            if mutation_policy.get("requires_governed_post_route") is not True:
                failures.append("Company setup mutations must require governed POST routes")
            if mutation_policy.get("requires_csrf") is not True:
                failures.append("Company setup mutations must require CSRF")
            if mutation_policy.get("requires_super_admin") is not True:
                failures.append("Company setup mutations must require Super Admin")
            if mutation_policy.get("gar_may_execute_actions") is not False:
                failures.append("GAR must not execute company setup actions")

        finally:
            db.session.rollback()
            _delete_by_ids(User, ids["users"])
            _delete_by_ids(Company, ids["companies"])
            if created_role_ids:
                Role.query.filter(Role.id.in_(created_role_ids)).delete(synchronize_session=False)
            db.session.commit()

    print("App company setup feed contract check")
    print("- Route checked: /app/company-setup/feed.json")
    print("- Read-only method checked: yes")
    print("- Authenticated company scope checked: yes")
    print("- Source references checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
