"""Verify Admin Portal routes are restricted to Admin users."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


ADMIN_GET_ENDPOINTS = (
    "admin_portal.dashboard",
    "admin_portal.manage_clients",
    "admin_portal.work_orders",
    "admin_portal.work_orders_feed",
    "admin_portal.gar_feed",
)


def _email(marker: str, name: str) -> str:
    return f"{name}.{marker.lower()}@example.invalid"


def _delete_by_ids(model, ids: list[int]) -> None:
    if ids:
        model.query.filter(model.id.in_(ids)).delete(synchronize_session=False)


def main() -> int:
    from flask import url_for

    from app import create_app
    from app.extensions import db
    from app.models.core.role import Role
    from app.models.core.user import User
    from app.models.onboarding.company import Company

    app = create_app()
    marker = f"ADMINACCESS{datetime.now(UTC).strftime('%y%m%d%H%M%S')}"
    failures: list[str] = []
    created_role_ids: list[int] = []
    ids = {"companies": [], "users": []}

    def role(name: str) -> Role:
        existing = Role.query.filter_by(name=name).first()
        if existing:
            return existing
        item = Role(name=name, description=f"Temporary role for {marker}")
        db.session.add(item)
        db.session.flush()
        created_role_ids.append(item.id)
        return item

    def user(name: str, role_name: str, company_id: int, username_suffix: str) -> User:
        item = User(
            full_name=f"{marker} {name}",
            email=_email(marker, username_suffix),
            username=f"{marker.lower()}_{username_suffix}"[:50],
            password_hash="not-used",
            pin="0000",
            role_id=role(role_name).id,
            company_id=company_id,
            is_active=True,
        )
        db.session.add(item)
        db.session.flush()
        ids["users"].append(item.id)
        return item

    def sign_in(client, actor: User) -> None:
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

    with app.app_context():
        stale_users = User.query.filter(User.username.ilike("adminaccess%")).all()
        stale_companies = Company.query.filter(Company.subdomain.ilike("adminaccess%")).all()
        _delete_by_ids(User, [item.id for item in stale_users])
        _delete_by_ids(Company, [item.id for item in stale_companies])
        db.session.commit()

        try:
            company = Company(
                name=f"{marker} Management Company",
                company_type="Property Management",
                country="Ireland",
                currency="EUR",
                subdomain=marker.lower(),
            )
            db.session.add(company)
            db.session.flush()
            ids["companies"].append(company.id)

            admin = user("Admin", "Admin", company.id, "admin")
            pm = user("PM", "Property Manager", company.id, "pm")
            contractor = user("Contractor", "Contractor", company.id, "contractor")
            db.session.commit()

            for endpoint in ADMIN_GET_ENDPOINTS:
                with app.test_request_context():
                    url = url_for(endpoint, question="What needs attention?")

                with app.test_client() as client:
                    sign_in(client, admin)
                    response = client.get(url)
                    if response.status_code >= 400:
                        failures.append(f"Admin could not access {endpoint}: HTTP {response.status_code}")

                for blocked_actor in (pm, contractor):
                    with app.test_client() as client:
                        sign_in(client, blocked_actor)
                        response = client.get(url)
                        if response.status_code != 403:
                            failures.append(
                                f"{blocked_actor.role.name} reached {endpoint}: HTTP {response.status_code}"
                            )

        except Exception as exc:
            if not failures:
                failures.append(str(exc))
        finally:
            db.session.rollback()
            _delete_by_ids(User, ids["users"])
            _delete_by_ids(Company, ids["companies"])
            if created_role_ids:
                Role.query.filter(Role.id.in_(created_role_ids)).delete(synchronize_session=False)
            db.session.commit()

    print("Admin Portal access contract check")
    print(f"- Temporary marker: {marker}")
    print(f"- Admin endpoints checked: {len(ADMIN_GET_ENDPOINTS)}")
    print("- Blocked roles checked: Property Manager, Contractor")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
