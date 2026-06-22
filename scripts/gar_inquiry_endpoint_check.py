r"""Exercise role-scoped GAR inquiry HTTP endpoints.

This check creates temporary users for the current GAR-facing roles, signs in
through Flask's test-client session, calls each inquiry endpoint, verifies the
standard response envelope, then removes the temporary records.

Run from the project root:
    .\venv\Scripts\python.exe scripts\gar_inquiry_endpoint_check.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _email(marker: str, name: str) -> str:
    return f"{name}.{marker.lower()}@example.invalid"


def _delete_by_ids(model, ids: list[int]) -> None:
    if ids:
        model.query.filter(model.id.in_(ids)).delete(synchronize_session=False)


def _cleanup_stale_records(models: dict[str, object]) -> None:
    Company = models["Company"]
    Client = models["Client"]
    Contractor = models["Contractor"]
    Member = models["Member"]
    Unit = models["Unit"]
    UnitMembership = models["UnitMembership"]
    User = models["User"]

    users = User.query.filter(User.username.ilike("garendpoint%")).all()
    companies = Company.query.filter(Company.subdomain.ilike("garendpoint%")).all()
    contractors = Contractor.query.filter(Contractor.company_name.ilike("GARENDPOINT%")).all()
    clients = Client.query.filter(Client.name.ilike("GARENDPOINT%")).all()
    units = Unit.query.filter(Unit.unit_label.ilike("GARENDPOINT%")).all()
    members = Member.query.filter(Member.first_name.ilike("GARENDPOINT%")).all()

    user_ids = [item.id for item in users]
    company_ids = [item.id for item in companies]
    contractor_ids = [item.id for item in contractors]
    client_ids = [item.id for item in clients]
    unit_ids = [item.id for item in units]
    member_ids = [item.id for item in members]

    UnitMembership.query.filter(
        (UnitMembership.member_id.in_(member_ids or [0]))
        | (UnitMembership.unit_id.in_(unit_ids or [0]))
    ).delete(synchronize_session=False)
    _delete_by_ids(Member, member_ids)
    _delete_by_ids(Unit, unit_ids)
    _delete_by_ids(Client, client_ids)
    _delete_by_ids(User, user_ids)
    _delete_by_ids(Contractor, contractor_ids)
    _delete_by_ids(Company, company_ids)


def main() -> int:
    from app import create_app
    from app.extensions import db
    from app.models.client.client import Client
    from app.models.contractor.contractor import Contractor
    from app.models.core.role import Role
    from app.models.core.user import User
    from app.models.members.member import Member
    from app.models.members.unit import Unit
    from app.models.members.unit_membership import UnitMembership
    from app.models.onboarding.company import Company

    app = create_app()
    marker = f"GARENDPOINT{datetime.now(UTC).strftime('%y%m%d%H%M%S')}"
    created_role_ids: list[int] = []
    ids: dict[str, list[int]] = {
        "companies": [],
        "clients": [],
        "contractors": [],
        "members": [],
        "units": [],
        "unit_memberships": [],
        "users": [],
    }
    failures: list[str] = []

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

    def expect_envelope(endpoint: str, actor: User, question: str, expected_result_type: str | None = None) -> None:
        with app.test_client() as client:
            sign_in(client, actor)
            with app.test_request_context():
                from flask import url_for

                url = url_for(endpoint, question=question)
            response = client.get(url)
            if response.status_code != 200:
                failures.append(f"{endpoint} returned HTTP {response.status_code}")
                return

            payload = response.get_json(silent=True) or {}
            if payload.get("context_type") != "gar_inquiry_response":
                failures.append(f"{endpoint} did not return GAR inquiry response envelope")
            source_policy = payload.get("source_policy", {})
            if not source_policy.get("must_use_source_records"):
                failures.append(f"{endpoint} did not require source records")
            if source_policy.get("allow_model_only_answer"):
                failures.append(f"{endpoint} allowed model-only answers")
            if "readiness" not in payload:
                failures.append(f"{endpoint} did not include readiness")
            if expected_result_type:
                result_type = payload.get("source_query_result", {}).get("context_type")
                if result_type != expected_result_type:
                    failures.append(
                        f"{endpoint} returned source result {result_type}, expected {expected_result_type}"
                    )

    with app.app_context():
        _cleanup_stale_records(
            {
                "Company": Company,
                "Client": Client,
                "Contractor": Contractor,
                "Member": Member,
                "Unit": Unit,
                "UnitMembership": UnitMembership,
                "User": User,
            }
        )
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

            super_admin = user("Super Admin", "Super Admin", company.id, "super_admin")
            admin = user("Admin", "Admin", company.id, "admin")
            pm = user("PM", "Property Manager", company.id, "pm")
            assistant = user("Assistant", "Assistant Property Manager", company.id, "assistant")
            finance = user("Finance", "Financial Controller", company.id, "finance")
            director = user("Director", "Director", company.id, "director")
            contractor_user = user("Contractor", "Contractor", company.id, "contractor")
            member_user = user("Member", "Member", company.id, "member")

            client_record = Client(
                company_id=company.id,
                name=f"{marker} Test Development",
                property_name=f"{marker} Inquiry Test",
                client_type="OMC",
                address_line1="GAR Endpoint House",
                city="Dublin",
                country="Ireland",
                assigned_pm_id=pm.id,
                assigned_assistant_id=assistant.id,
                assigned_fc_id=finance.id,
            )
            db.session.add(client_record)
            db.session.flush()
            ids["clients"].append(client_record.id)

            unit = Unit(
                company_id=company.id,
                client_id=client_record.id,
                unit_label=f"{marker} A-001",
                unit_number="A-001",
                unit_type="Apartment",
                unit_category="Residential",
                block_name="Block A",
                status="Active",
            )
            db.session.add(unit)
            db.session.flush()
            ids["units"].append(unit.id)

            contractor = Contractor(
                company_name=f"{marker} Contractor Ltd",
                email=_email(marker, "contractor_company"),
                phone="0100000000",
                business_type="General Maintenance",
                is_active=True,
                consent_to_contact=True,
            )
            db.session.add(contractor)
            db.session.flush()
            ids["contractors"].append(contractor.id)
            contractor_user.contractor_id = contractor.id

            member = Member(
                user_id=member_user.id,
                company_id=company.id,
                client_id=client_record.id,
                first_name=marker,
                last_name="Member",
                email=member_user.email,
                is_owner=True,
            )
            db.session.add(member)
            db.session.flush()
            ids["members"].append(member.id)

            membership = UnitMembership(
                unit_id=unit.id,
                member_id=member.id,
                role="owner",
                is_primary=True,
                is_current=True,
            )
            db.session.add(membership)
            db.session.flush()
            ids["unit_memberships"].append(membership.id)
            db.session.commit()

            cases = (
                ("super_admin.gar_inquiry", super_admin, "What notifications need my attention?", "gar_notification_source_query"),
                ("admin_portal.gar_inquiry", admin, "Who is active in the team directory?", "gar_team_source_query"),
                ("property_manager.gar_inquiry", pm, "What open works need attention?", "gar_works_source_query"),
                ("assistant.gar_inquiry", assistant, "What open maintenance requests need attention?", "gar_works_source_query"),
                ("finance.gar_inquiry", finance, "Tell me the debtors in this portfolio", None),
                ("director.gar_inquiry", director, "Which developments have governance attention signals?", "gar_governance_source_query"),
                ("contractor.gar_inquiry", contractor_user, "What assigned work orders are in my contractor queue?", "gar_contractor_works_source_query"),
                ("members.gar_inquiry", member_user, "What work orders and maintenance requests need my attention?", "gar_member_works_source_query"),
            )
            for endpoint, actor, question, expected_result_type in cases:
                expect_envelope(endpoint, actor, question, expected_result_type)

        except Exception as exc:
            if not failures:
                failures.append(str(exc))
        finally:
            db.session.rollback()
            _delete_by_ids(UnitMembership, ids["unit_memberships"])
            _delete_by_ids(Member, ids["members"])
            _delete_by_ids(Unit, ids["units"])
            _delete_by_ids(Client, ids["clients"])
            _delete_by_ids(User, ids["users"])
            _delete_by_ids(Contractor, ids["contractors"])
            _delete_by_ids(Company, ids["companies"])
            if created_role_ids:
                Role.query.filter(Role.id.in_(created_role_ids)).delete(synchronize_session=False)
            db.session.commit()

    print("GAR inquiry endpoint check")
    print(f"- Temporary marker: {marker}")
    print("- Role endpoints checked: super admin, admin, PM, assistant, finance, director, contractor, member")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
