r"""Exercise Works Logix management access rules.

This check creates a temporary company, users, client, unit, work order and
reopen request, verifies the Phase 3 role/assignment rules, then deletes the
temporary records.

Run from the project root:
    .\venv\Scripts\python.exe scripts\works_access_control_check.py
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
    Unit = models["Unit"]
    User = models["User"]
    WorkOrder = models["WorkOrder"]
    WorkOrderReopenRequest = models["WorkOrderReopenRequest"]

    stale_users = User.query.filter(User.username.ilike("worksaccess%")).all()
    stale_companies = Company.query.filter(Company.subdomain.ilike("worksaccess%")).all()
    stale_clients = Client.query.filter(Client.name.ilike("WORKSACCESS%")).all()
    stale_units = Unit.query.filter(Unit.unit_label.ilike("WORKSACCESS%")).all()

    user_ids = [item.id for item in stale_users]
    company_ids = [item.id for item in stale_companies]
    client_ids = [item.id for item in stale_clients]
    unit_ids = [item.id for item in stale_units]

    stale_work_orders = WorkOrder.query.filter(
        (WorkOrder.title.ilike("WORKSACCESS%"))
        | (WorkOrder.company_id.in_(company_ids or [0]))
        | (WorkOrder.client_id.in_(client_ids or [0]))
        | (WorkOrder.unit_id.in_(unit_ids or [0]))
    ).all()
    work_order_ids = [item.id for item in stale_work_orders]

    WorkOrderReopenRequest.query.filter(
        WorkOrderReopenRequest.work_order_id.in_(work_order_ids or [0])
    ).delete(synchronize_session=False)
    _delete_by_ids(WorkOrder, work_order_ids)
    _delete_by_ids(Unit, unit_ids)
    _delete_by_ids(Client, client_ids)
    _delete_by_ids(User, user_ids)
    _delete_by_ids(Company, company_ids)


def main() -> int:
    from app import create_app
    from app.extensions import db
    from app.models.client.client import Client
    from app.models.core.role import Role
    from app.models.core.user import User
    from app.models.members.unit import Unit
    from app.models.onboarding.company import Company
    from app.models.works.work_order import WorkOrder
    from app.models.works.work_order_reopen_request import WorkOrderReopenRequest
    from app.services.works import can_manage_reopen_request, can_manage_work_order

    app = create_app()
    marker = f"WORKSACCESS{datetime.now(UTC).strftime('%y%m%d%H%M%S')}"
    created_role_ids: list[int] = []
    ids: dict[str, list[int]] = {
        "companies": [],
        "clients": [],
        "units": [],
        "users": [],
        "work_orders": [],
        "reopen_requests": [],
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

    def expect(label: str, actual: bool, expected: bool) -> None:
        if actual is not expected:
            failures.append(f"{label}: expected {expected}, got {actual}")

    with app.app_context():
        _cleanup_stale_records(
            {
                "Company": Company,
                "Client": Client,
                "Unit": Unit,
                "User": User,
                "WorkOrder": WorkOrder,
                "WorkOrderReopenRequest": WorkOrderReopenRequest,
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
            other_company = Company(
                name=f"{marker} Other Company",
                company_type="Property Management",
                country="Ireland",
                currency="EUR",
                subdomain=f"{marker.lower()}-other",
            )
            db.session.add_all([company, other_company])
            db.session.flush()
            ids["companies"].extend([company.id, other_company.id])

            admin = user("Admin", "Admin", company.id, "admin")
            super_admin = user("Super Admin", "Super Admin", company.id, "super_admin")
            assigned_pm = user("Assigned PM", "Property Manager", company.id, "assigned_pm")
            unassigned_pm = user("Unassigned PM", "Property Manager", company.id, "unassigned_pm")
            assigned_assistant = user(
                "Assigned Assistant",
                "Assistant Property Manager",
                company.id,
                "assigned_assistant",
            )
            unassigned_assistant = user(
                "Unassigned Assistant",
                "Assistant Property Manager",
                company.id,
                "unassigned_assistant",
            )
            master_assistant = user(
                "Master Assistant",
                "Master Assistant",
                company.id,
                "master_assistant",
            )
            contractor = user("Contractor", "Contractor", company.id, "contractor")
            member = user("Member", "Member", company.id, "member")
            other_company_admin = user("Other Company Admin", "Admin", other_company.id, "other_admin")

            client = Client(
                company_id=company.id,
                name=f"{marker} Test Development",
                property_name=f"{marker} Access Test",
                client_type="OMC",
                address_line1="Access Control House",
                city="Dublin",
                country="Ireland",
                region="Dublin",
                client_code=f"{marker}-CLIENT",
                assigned_pm_id=assigned_pm.id,
                assigned_assistant_id=assigned_assistant.id,
            )
            db.session.add(client)
            db.session.flush()
            ids["clients"].append(client.id)

            unit = Unit(
                company_id=company.id,
                client_id=client.id,
                unit_label=f"{marker} A-001",
                unit_number="A-001",
                unit_type="Apartment",
                unit_category="Residential",
                block_name="Block A",
                status="Active",
                occupancy_status="owner_occupied",
            )
            db.session.add(unit)
            db.session.flush()
            ids["units"].append(unit.id)

            work_order = WorkOrder(
                company_id=company.id,
                client_id=client.id,
                unit_id=unit.id,
                created_by_id=admin.id,
                title=f"{marker} access permission check",
                description="Temporary access-control smoke check.",
                status="Completed",
                source_system="Works Logix",
            )
            db.session.add(work_order)
            db.session.flush()
            ids["work_orders"].append(work_order.id)

            reopen_request = WorkOrderReopenRequest(
                work_order_id=work_order.id,
                unit_id=unit.id,
                reason="Temporary access-control smoke check.",
                status="Pending",
            )
            db.session.add(reopen_request)
            db.session.flush()
            ids["reopen_requests"].append(reopen_request.id)
            db.session.commit()

            cases = [
                ("Admin can manage", admin, True),
                ("Super Admin can manage", super_admin, True),
                ("Assigned PM can manage", assigned_pm, True),
                ("Unassigned PM cannot manage", unassigned_pm, False),
                ("Assigned assistant can manage", assigned_assistant, True),
                ("Unassigned assistant cannot manage", unassigned_assistant, False),
                ("Master Assistant can provide cover", master_assistant, True),
                ("Contractor cannot manage platform review", contractor, False),
                ("Member cannot manage platform review", member, False),
                ("Other company admin cannot manage", other_company_admin, False),
            ]

            for label, actor, expected in cases:
                expect(label, can_manage_work_order(actor, work_order, company.id), expected)
                expect(
                    f"{label} reopen request",
                    can_manage_reopen_request(actor, reopen_request, company.id),
                    expected,
                )

            expect("Missing user cannot manage", can_manage_work_order(None, work_order, company.id), False)
            expect("Missing work order cannot manage", can_manage_work_order(admin, None, company.id), False)
            expect("Missing company cannot manage", can_manage_work_order(admin, work_order, None), False)

        except Exception as exc:
            if not failures:
                failures.append(str(exc))
        finally:
            db.session.rollback()
            _delete_by_ids(WorkOrderReopenRequest, ids["reopen_requests"])
            _delete_by_ids(WorkOrder, ids["work_orders"])
            _delete_by_ids(Unit, ids["units"])
            _delete_by_ids(Client, ids["clients"])
            _delete_by_ids(User, ids["users"])
            _delete_by_ids(Company, ids["companies"])
            if created_role_ids:
                User.query.filter(User.role_id.in_(created_role_ids)).delete(synchronize_session=False)
                Role.query.filter(Role.id.in_(created_role_ids)).delete(synchronize_session=False)
            db.session.commit()

    print("Works access control check")
    print(f"- Temporary marker: {marker}")
    print("- Rules checked: admin, PM, assistant, master assistant, contractor, member, company boundary")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
