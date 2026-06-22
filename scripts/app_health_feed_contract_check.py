"""Verify the app health/bootstrap feed remains safe and stable."""

from __future__ import annotations

from datetime import UTC, datetime
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


REQUIRED_TOP_LEVEL_KEYS = (
    "context_type",
    "status",
    "generated_at",
    "authenticated",
    "user",
    "contract_versions",
    "endpoints",
    "runtime",
    "gar",
    "source_references",
)

REQUIRED_CONTRACT_VERSION_KEYS = (
    "app_policy",
    "app_scope",
    "app_navigation",
    "app_surfaces",
    "app_deep_links",
    "app_session",
    "app_notifications",
    "app_resilience",
    "app_observability",
    "app_compatibility",
    "app_sync",
    "app_media",
    "app_capabilities",
)

REQUIRED_ENDPOINT_KEYS = (
    "health",
    "home",
    "capabilities",
    "notifications",
    "service_worker",
    "manifest",
)


def main() -> int:
    from app import create_app
    from app.extensions import db
    from app.models.core.role import Role
    from app.models.core.user import User
    from app.models.onboarding.company import Company

    app = create_app()
    failures: list[str] = []
    marker = f"APPHEALTH{datetime.now(UTC).strftime('%y%m%d%H%M%S')}"
    ids: dict[str, list[int]] = {"companies": [], "users": []}
    created_role_ids: list[int] = []

    rule = next((item for item in app.url_map.iter_rules() if item.endpoint == "app_home.health_feed"), None)
    if not rule:
        failures.append("Missing app_home.health_feed route")
    else:
        if rule.rule != "/app/health/feed.json":
            failures.append(f"app_home.health_feed route changed to {rule.rule}")
        if "GET" not in (rule.methods or set()):
            failures.append("app_home.health_feed does not allow GET")
        if {"POST", "PUT", "PATCH", "DELETE"}.intersection(rule.methods or set()):
            failures.append("app_home.health_feed allows a mutating method")

    def _role(name: str) -> Role:
        existing = Role.query.filter_by(name=name).first()
        if existing:
            return existing
        item = Role(name=name, description=f"Temporary role for {marker}")
        db.session.add(item)
        db.session.flush()
        created_role_ids.append(item.id)
        return item

    def _sign_in(client, actor: User) -> None:
        role_name = actor.role.name if actor.role else "Unassigned"
        with client.session_transaction() as sess:
            sess["_user_id"] = str(actor.id)
            sess["_fresh"] = True
            sess["user_id"] = actor.id
            sess["role"] = role_name
            sess["company_id"] = actor.company_id
            sess["user"] = {
                "id": actor.id,
                "email": actor.email,
                "role": role_name,
                "company": actor.company.name if actor.company else "",
                "name": actor.full_name,
                "full_name": actor.full_name,
            }

    def _delete_by_ids(model, item_ids: list[int]) -> None:
        if item_ids:
            model.query.filter(model.id.in_(item_ids)).delete(synchronize_session=False)

    def _check_payload(payload: dict, *, expected_authenticated: bool, expected_user_id: int | None = None) -> None:
        for key in REQUIRED_TOP_LEVEL_KEYS:
            if key not in payload:
                failures.append(f"app health payload missing: {key}")
        if payload.get("context_type") != "app_health":
            failures.append(f"Unexpected context_type: {payload.get('context_type')}")
        if payload.get("status") != "operational":
            failures.append(f"Unexpected app health status: {payload.get('status')}")
        if payload.get("authenticated") is not expected_authenticated:
            failures.append("app health authenticated flag is incorrect")

        user_payload = payload.get("user") or {}
        if expected_authenticated:
            if user_payload.get("id") != expected_user_id:
                failures.append("app health did not preserve signed-in user id")
            if user_payload.get("role_context") != "super_admin":
                failures.append(f"app health role_context changed: {user_payload.get('role_context')}")
        elif user_payload.get("id") is not None:
            failures.append("anonymous app health should not expose a user id")

        contract_versions = payload.get("contract_versions") or {}
        for key in REQUIRED_CONTRACT_VERSION_KEYS:
            if key not in contract_versions:
                failures.append(f"app health contract_versions missing: {key}")
        if contract_versions.get("app_sync") != "phase3e-app-sync-v1":
            failures.append("app health lost app sync contract version")
        if contract_versions.get("app_scope") != "phase3e-app-scope-v1":
            failures.append("app health lost app scope contract version")
        if contract_versions.get("app_surfaces") != "phase3e-app-surfaces-v1":
            failures.append("app health lost app surfaces contract version")
        if contract_versions.get("app_deep_links") != "phase3e-app-deep-links-v1":
            failures.append("app health lost app deep-links contract version")
        if contract_versions.get("app_session") != "phase3e-app-session-v1":
            failures.append("app health lost app session contract version")
        if contract_versions.get("app_notifications") != "phase3e-app-notifications-v1":
            failures.append("app health lost app notifications contract version")
        if contract_versions.get("app_resilience") != "phase3e-app-resilience-v1":
            failures.append("app health lost app resilience contract version")
        if contract_versions.get("app_observability") != "phase3e-app-observability-v1":
            failures.append("app health lost app observability contract version")
        if contract_versions.get("app_compatibility") != "phase3e-app-compatibility-v1":
            failures.append("app health lost app compatibility contract version")
        if contract_versions.get("app_media") != "phase3e-app-media-v1":
            failures.append("app health lost app media contract version")

        endpoints = payload.get("endpoints") or {}
        for key in REQUIRED_ENDPOINT_KEYS:
            if key not in endpoints:
                failures.append(f"app health endpoints missing: {key}")
        if endpoints.get("health") != "/app/health/feed.json":
            failures.append(f"app health self endpoint changed: {endpoints.get('health')}")
        if endpoints.get("service_worker") != "/app-shell-sw.js":
            failures.append("app health service worker endpoint changed")

        runtime = payload.get("runtime") or {}
        if not runtime.get("pwa_shell_available"):
            failures.append("app health must declare PWA shell availability")
        if not runtime.get("static_shell_only_offline"):
            failures.append("app health must keep offline cache to static shell only")
        if not runtime.get("read_only_feeds"):
            failures.append("app health must declare feeds read-only")
        if not runtime.get("governed_mutations"):
            failures.append("app health must require governed mutations")
        if not runtime.get("server_session_required_for_business_feeds"):
            failures.append("app health must require server session for business feeds")

        gar = payload.get("gar") or {}
        if not gar.get("role_aware") or not gar.get("source_backed_required"):
            failures.append("app health must keep GAR role-aware and source-backed")
        if gar.get("model_only_answers_allowed"):
            failures.append("app health must block model-only GAR answers")

        sources = payload.get("source_references") or []
        if not any(source.get("model") == "AppPolicy" for source in sources):
            failures.append("app health source_references missing AppPolicy")

    with app.app_context():
        Company.query.filter(Company.subdomain.ilike("apphealth%")).delete(synchronize_session=False)
        User.query.filter(User.username.ilike("apphealth%")).delete(synchronize_session=False)
        db.session.commit()

        try:
            with app.test_client() as client:
                anonymous_response = client.get("/app/health/feed.json")
                if anonymous_response.status_code != 200:
                    failures.append(f"anonymous /app/health/feed.json returned HTTP {anonymous_response.status_code}")
                _check_payload(anonymous_response.get_json(silent=True) or {}, expected_authenticated=False)

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
                password_hash="not-used",
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
                _sign_in(client, user)
                signed_in_response = client.get("/app/health/feed.json")
                if signed_in_response.status_code != 200:
                    failures.append(f"signed-in /app/health/feed.json returned HTTP {signed_in_response.status_code}")
                _check_payload(
                    signed_in_response.get_json(silent=True) or {},
                    expected_authenticated=True,
                    expected_user_id=user.id,
                )

        finally:
            db.session.rollback()
            _delete_by_ids(User, ids["users"])
            _delete_by_ids(Company, ids["companies"])
            if created_role_ids:
                Role.query.filter(Role.id.in_(created_role_ids)).delete(synchronize_session=False)
            db.session.commit()

    print("App health feed contract check")
    print("- Route checked: /app/health/feed.json")
    print("- Anonymous bootstrap checked: yes")
    print("- Signed-in bootstrap checked: yes")
    print("- Runtime, GAR and contract versions checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
