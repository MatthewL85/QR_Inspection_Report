"""Verify Phase 3D notification visibility by role.

This check proves Works management alerts reach assigned management users and
assistant cover roles, while finance, director, contractor, member and
unassigned assistant users do not receive internal Works management alerts.
"""

from __future__ import annotations

from datetime import UTC, datetime
import sys
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
    MaintenanceRequest = models["MaintenanceRequest"]
    Member = models["Member"]
    Notification = models["Notification"]
    Unit = models["Unit"]
    User = models["User"]

    users = User.query.filter(User.username.ilike("notifvis%")).all()
    companies = Company.query.filter(Company.subdomain.ilike("notifvis%")).all()
    clients = Client.query.filter(Client.name.ilike("NOTIFVIS%")).all()
    units = Unit.query.filter(Unit.unit_label.ilike("NOTIFVIS%")).all()
    members = Member.query.filter(Member.first_name.ilike("NOTIFVIS%")).all()

    user_ids = [item.id for item in users]
    company_ids = [item.id for item in companies]
    client_ids = [item.id for item in clients]
    unit_ids = [item.id for item in units]
    member_ids = [item.id for item in members]

    _delete_by_ids(
        Notification,
        [item.id for item in Notification.query.filter(Notification.recipient_id.in_(user_ids or [0])).all()],
    )
    _delete_by_ids(MaintenanceRequest, [
        item.id for item in MaintenanceRequest.query.filter(
            (MaintenanceRequest.unit_id.in_(unit_ids or [0]))
            | (MaintenanceRequest.member_id.in_(member_ids or [0]))
        ).all()
    ])
    _delete_by_ids(Member, member_ids)
    _delete_by_ids(Unit, unit_ids)
    _delete_by_ids(Client, client_ids)
    _delete_by_ids(User, user_ids)
    _delete_by_ids(Company, company_ids)


def main() -> int:
    from app import create_app
    from app.extensions import db
    from app.models.client.client import Client
    from app.models.core.notification import Notification
    from app.models.core.role import Role
    from app.models.core.user import User
    from app.models.maintenance.maintenance_request import MaintenanceRequest
    from app.models.members.member import Member
    from app.models.members.unit import Unit
    from app.models.onboarding.company import Company
    from app.services.works.workflow_service import notify_member_request_submitted

    app = create_app()
    marker = f"NOTIFVIS{datetime.now(UTC).strftime('%y%m%d%H%M%S')}"
    failures: list[str] = []
    created_role_ids: list[int] = []
    ids: dict[str, list[int]] = {
        "companies": [],
        "clients": [],
        "members": [],
        "maintenance_requests": [],
        "notifications": [],
        "units": [],
        "users": [],
    }

    def role(name: str) -> Role:
        existing = Role.query.filter_by(name=name).first()
        if existing:
            return existing
        item = Role(name=name, description=f"Temporary role for {marker}")
        db.session.add(item)
        db.session.flush()
        created_role_ids.append(item.id)
        return item

    def user(label: str, role_name: str, company_id: int, suffix: str, *, active: bool = True) -> User:
        item = User(
            full_name=f"{marker} {label}",
            email=_email(marker, suffix),
            username=f"{marker.lower()}_{suffix}"[:50],
            password_hash="not-used",
            pin="0000",
            role_id=role(role_name).id,
            company_id=company_id,
            is_active=active,
        )
        db.session.add(item)
        db.session.flush()
        ids["users"].append(item.id)
        return item

    with app.app_context():
        _cleanup_stale_records(
            {
                "Company": Company,
                "Client": Client,
                "MaintenanceRequest": MaintenanceRequest,
                "Member": Member,
                "Notification": Notification,
                "Unit": Unit,
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

            expected_recipients = {
                "admin": user("Admin", "Admin", company.id, "admin"),
                "super_admin": user("Super Admin", "Super Admin", company.id, "super_admin"),
                "assigned_pm": user("Assigned PM", "Property Manager", company.id, "assigned_pm"),
                "assigned_assistant": user("Assigned Assistant", "Assistant Property Manager", company.id, "assigned_assistant"),
                "assistant_manager": user("Assistant Manager", "Assistant Manager", company.id, "assistant_manager"),
                "master_assistant": user("Master Assistant", "Master Assistant", company.id, "master_assistant"),
                "assistant_lead": user("Assistant Lead", "Assistant Lead", company.id, "assistant_lead"),
                "senior_assistant": user("Senior Assistant", "Senior Assistant", company.id, "senior_assistant"),
            }
            blocked_recipients = {
                "unassigned_assistant": user("Unassigned Assistant", "Assistant Property Manager", company.id, "unassigned_assistant"),
                "inactive_master_assistant": user("Inactive Master Assistant", "Master Assistant", company.id, "inactive_master", active=False),
                "finance": user("Finance", "Financial Controller", company.id, "finance"),
                "director": user("Director", "Director", company.id, "director"),
                "contractor": user("Contractor", "Contractor", company.id, "contractor"),
                "member_user": user("Member", "Member", company.id, "member"),
                "other_company_admin": user("Other Company Admin", "Admin", other_company.id, "other_admin"),
            }

            client = Client(
                company_id=company.id,
                name=f"{marker} Test Development",
                property_name=f"{marker} Visibility Test",
                client_type="OMC",
                address_line1="Notification Visibility House",
                city="Dublin",
                country="Ireland",
                assigned_pm_id=expected_recipients["assigned_pm"].id,
                assigned_assistant_id=expected_recipients["assigned_assistant"].id,
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
            )
            db.session.add(unit)
            db.session.flush()
            ids["units"].append(unit.id)

            member = Member(
                user_id=blocked_recipients["member_user"].id,
                company_id=company.id,
                client_id=client.id,
                first_name=marker,
                last_name="Member",
                email=blocked_recipients["member_user"].email,
                is_owner=True,
            )
            db.session.add(member)
            db.session.flush()
            ids["members"].append(member.id)

            maintenance_request = MaintenanceRequest(
                member_id=member.id,
                unit_id=unit.id,
                requested_by_id=blocked_recipients["member_user"].id,
                title=f"{marker} management visibility check",
                description="Temporary notification role visibility check.",
                category="General",
                urgency_level="High",
                request_channel="Members Logix",
                visibility_scope="Admin,PM",
                consent_verified=True,
                status="Pending",
            )
            db.session.add(maintenance_request)
            db.session.commit()
            ids["maintenance_requests"].append(maintenance_request.id)

            notify_member_request_submitted(maintenance_request)
            notifications = Notification.query.filter(
                Notification.type == "works_member_request",
                Notification.recipient_id.in_([user.id for user in [*expected_recipients.values(), *blocked_recipients.values()]]),
            ).all()
            ids["notifications"] = [item.id for item in notifications]
            by_recipient = {item.recipient_id: item for item in notifications}

            for label, recipient in expected_recipients.items():
                notification = by_recipient.get(recipient.id)
                if not notification:
                    failures.append(f"{label} did not receive the Works management notification")
                    continue
                target = (notification.extracted_data or {}).get("action_target") or notification.link_url or ""
                if "#member-request-" not in target:
                    failures.append(f"{label} notification did not target the member request row")

            for label, recipient in blocked_recipients.items():
                if recipient.id in by_recipient:
                    failures.append(f"{label} incorrectly received a Works management notification")

        except Exception as exc:
            if not failures:
                failures.append(str(exc))
        finally:
            db.session.rollback()
            _delete_by_ids(Notification, ids["notifications"])
            _delete_by_ids(MaintenanceRequest, ids["maintenance_requests"])
            _delete_by_ids(Member, ids["members"])
            _delete_by_ids(Unit, ids["units"])
            _delete_by_ids(Client, ids["clients"])
            _delete_by_ids(User, ids["users"])
            _delete_by_ids(Company, ids["companies"])
            if created_role_ids:
                Role.query.filter(Role.id.in_(created_role_ids)).delete(synchronize_session=False)
            db.session.commit()

    print("Notification role visibility contract check")
    print("- Works management recipients checked: assigned PM, assigned assistant, Admin, Super Admin, assistant cover roles")
    print("- Blocked recipients checked: unassigned assistant, inactive cover, finance, director, contractor, member, other company admin")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
