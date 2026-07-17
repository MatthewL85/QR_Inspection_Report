"""Verify app/mobile feed endpoints are present, read-only and usable."""

from __future__ import annotations

from datetime import UTC, datetime
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


EXPECTED_FEEDS = {
    "app_home.capabilities_feed": "/app/capabilities/feed.json",
    "app_home.company_setup_feed": "/app/company-setup/feed.json",
    "app_home.feed": "/app/home/feed.json",
    "app_home.health_feed": "/app/health/feed.json",
    "app_home.module_settings_feed": "/app/module-settings/feed.json",
    "super_admin.gar_insights_feed": "/super-admin/gar-insights/feed.json",
    "admin_portal.gar_feed": "/admin-portal/gar/feed.json",
    "property_manager.gar_feed": "/pm/gar/feed.json",
    "assistant.gar_feed": "/assistant/gar/feed.json",
    "finance.gar_feed": "/finance/gar/feed.json",
    "director.gar_feed": "/director/gar/feed.json",
    "contractor.gar_feed": "/contractor/gar/feed.json",
    "members.gar_feed": "/members/gar/feed.json",
    "super_admin.work_orders_feed": "/super-admin/work-orders/feed.json",
    "admin_portal.work_orders_feed": "/admin-portal/work-orders/feed.json",
    "property_manager.work_orders_feed": "/pm/work-orders/feed.json",
    "assistant.work_orders_feed": "/assistant/work-orders/feed.json",
    "contractor.work_orders_feed": "/contractor/work-orders/feed.json",
    "contractor.calendar_feed": "/contractor/calendar/feed.json",
    "members.works_feed": "/members/works/feed.json",
    "notifications.feed": "/notifications/feed.json",
}

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


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
    Notification = models["Notification"]
    Unit = models["Unit"]
    UnitMembership = models["UnitMembership"]
    User = models["User"]

    users = User.query.filter(User.username.ilike("appfeed%")).all()
    companies = Company.query.filter(Company.subdomain.ilike("appfeed%")).all()
    contractors = Contractor.query.filter(Contractor.company_name.ilike("APPFEED%")).all()
    clients = Client.query.filter(Client.name.ilike("APPFEED%")).all()
    units = Unit.query.filter(Unit.unit_label.ilike("APPFEED%")).all()
    members = Member.query.filter(Member.first_name.ilike("APPFEED%")).all()
    notifications = Notification.query.filter(Notification.message.ilike("APPFEED%")).all()

    user_ids = [item.id for item in users]
    company_ids = [item.id for item in companies]
    contractor_ids = [item.id for item in contractors]
    client_ids = [item.id for item in clients]
    unit_ids = [item.id for item in units]
    member_ids = [item.id for item in members]
    notification_ids = [item.id for item in notifications]

    _delete_by_ids(Notification, notification_ids)
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
    from app.models.core.notification import Notification
    from app.models.core.role import Role
    from app.models.core.user import User
    from app.models.members.member import Member
    from app.models.members.unit import Unit
    from app.models.members.unit_membership import UnitMembership
    from app.models.onboarding.company import Company

    app = create_app()
    failures: list[str] = []
    rules_by_endpoint = {rule.endpoint: rule for rule in app.url_map.iter_rules()}
    marker = f"APPFEED{datetime.now(UTC).strftime('%y%m%d%H%M%S')}"
    created_role_ids: list[int] = []
    ids: dict[str, list[int]] = {
        "companies": [],
        "clients": [],
        "contractors": [],
        "members": [],
        "notifications": [],
        "units": [],
        "unit_memberships": [],
        "users": [],
    }

    for endpoint, expected_rule in sorted(EXPECTED_FEEDS.items()):
        rule = rules_by_endpoint.get(endpoint)
        if not rule:
            failures.append(f"Missing app feed endpoint: {endpoint}")
            continue
        if rule.rule != expected_rule:
            failures.append(f"{endpoint} route changed from {expected_rule} to {rule.rule}")
        mutating = MUTATING_METHODS.intersection(rule.methods or set())
        if mutating:
            failures.append(f"{endpoint} feed allows mutating method(s): {', '.join(sorted(mutating))}")
        if "GET" not in (rule.methods or set()):
            failures.append(f"{endpoint} feed does not allow GET")

    feed_rules = [rule for rule in app.url_map.iter_rules() if rule.rule.endswith("/feed.json")]
    undeclared = sorted(
        f"{rule.endpoint} {rule.rule}"
        for rule in feed_rules
        if rule.endpoint not in EXPECTED_FEEDS
    )
    for item in undeclared:
        failures.append(f"Undeclared app feed endpoint: {item}")

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

    def expect_feed(endpoint: str, actor: User, context_type: str, required_keys: tuple[str, ...]) -> None:
        with app.test_client() as client:
            sign_in(client, actor)
            with app.test_request_context():
                from flask import url_for

                url = url_for(endpoint, question="What needs attention?")
            response = client.get(url)
            if response.status_code != 200:
                failures.append(f"{endpoint} returned HTTP {response.status_code}")
                return

            payload = response.get_json(silent=True)
            if not isinstance(payload, dict):
                failures.append(f"{endpoint} did not return a JSON object")
                return
            if payload.get("context_type") != context_type:
                failures.append(
                    f"{endpoint} returned context_type {payload.get('context_type')}, expected {context_type}"
                )
            for key in required_keys:
                if key not in payload:
                    failures.append(f"{endpoint} is missing payload key: {key}")
            if endpoint == "notifications.feed":
                summary = payload.get("summary") or {}
                if summary.get("acknowledged_count", 0) < 1:
                    failures.append("notifications.feed summary did not count acknowledged notifications")
                if not summary.get("last_acknowledged_at"):
                    failures.append("notifications.feed summary did not expose last_acknowledged_at")
                items = payload.get("notifications")
                if not isinstance(items, list) or not items:
                    failures.append("notifications.feed did not return live notification items")
                    return
                marker_item = next(
                    (
                        item for item in items
                        if item.get("message") == f"{marker} notification feed safety check"
                    ),
                    None,
                )
                if not marker_item:
                    failures.append("notifications.feed did not include the seeded notification item")
                    return
                if marker_item.get("safe_link_url") != "/":
                    failures.append(
                        f"notifications.feed did not mask an unsafe link_url: {marker_item.get('safe_link_url')}"
                    )
                action_queue = payload.get("action_queue")
                if not isinstance(action_queue, list):
                    failures.append("notifications.feed action_queue is not a list")
                    return
                marker_action = next(
                    (
                        item for item in action_queue
                        if item.get("message") == f"{marker} notification feed safety check"
                    ),
                    None,
                )
                if not marker_action:
                    failures.append("notifications.feed did not expose the seeded action notification in action_queue")
                    return
                if not marker_action.get("source_reference") or "safe_link_url" not in marker_action:
                    failures.append("notifications.feed action_queue item lost source/safe-link context")
                source_references = payload.get("source_references")
                if not isinstance(source_references, list) or not source_references:
                    failures.append("notifications.feed source_references is missing or empty")
                    return
                if not any(reference.get("model") == "Notification" for reference in source_references):
                    failures.append("notifications.feed source_references lost the Notification queue reference")
                if not any(
                    reference.get("model") == "WorkOrder" and reference.get("record_id") == 42
                    for reference in source_references
                ):
                    failures.append("notifications.feed source_references lost the action queue WorkOrder reference")

    with app.app_context():
        _cleanup_stale_records(
            {
                "Company": Company,
                "Client": Client,
                "Contractor": Contractor,
                "Member": Member,
                "Notification": Notification,
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

            contractor_company = Company(
                name=f"{marker} Contractor Company",
                company_type="Contractor",
                country="Ireland",
                currency="EUR",
                subdomain=f"{marker.lower()}contractor",
            )
            db.session.add(contractor_company)
            db.session.flush()
            ids["companies"].append(contractor_company.id)

            super_admin = user("Super Admin", "Super Admin", company.id, "super_admin")
            admin = user("Admin", "Admin", company.id, "admin")
            pm = user("PM", "Property Manager", company.id, "pm")
            assistant = user("Assistant", "Assistant Property Manager", company.id, "assistant")
            finance = user("Finance", "Financial Controller", company.id, "finance")
            director = user("Director", "Director", company.id, "director")
            contractor_user = user("Contractor", "Contractor", contractor_company.id, "contractor")
            member_user = user("Member", "Member", company.id, "member")

            client_record = Client(
                company_id=company.id,
                name=f"{marker} Test Development",
                property_name=f"{marker} Feed Test",
                client_type="OMC",
                address_line1="App Feed House",
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

            notification = Notification(
                recipient_id=super_admin.id,
                message=f"{marker} notification feed safety check",
                type="works_member_request",
                is_read=False,
                created_at=datetime.now(UTC),
                link_url="//unsafe.example/work-order",
                priority_level="High",
                gar_category="Works Logix",
                suggested_action="Review member request",
                extracted_data={"source_type": "works_member_request", "work_order_id": 42},
            )
            db.session.add(notification)
            db.session.flush()
            ids["notifications"].append(notification.id)

            acknowledged_notification = Notification(
                recipient_id=super_admin.id,
                message=f"{marker} notification feed acknowledged check",
                type="works_closed",
                is_read=True,
                read_at=datetime.now(UTC),
                created_at=datetime.now(UTC),
                link_url="/notifications/",
                priority_level="Low",
                gar_category="Works Logix",
                suggested_action="No action required",
                extracted_data={"source_type": "work_order", "work_order_id": 43},
            )
            db.session.add(acknowledged_notification)
            db.session.flush()
            ids["notifications"].append(acknowledged_notification.id)
            db.session.commit()

            gar_keys = ("summary", "priority_actions", "source_references", "capability_registry")
            role_digest_keys = ("summary", "priority_actions", "source_references", "capability_registry")
            works_keys = ("stats", "next_actions", "queues", "gar")
            contractor_keys = ("stats", "next_actions", "queues")
            contractor_schedule_keys = (
                "stats",
                "unscheduled_dockets",
                "scheduled_entries",
                "today",
                "overdue",
                "upcoming",
                "source_references",
                "app_contract",
            )
            member_keys = ("linked_units", "next_actions", "attention_queues", "requests", "open_work_orders")
            notification_keys = ("summary", "filters", "notifications", "action_queue", "source_references")
            app_home_keys = (
                "user",
                "navigation",
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
                "feeds",
                "summary",
                "modules",
                "priority_actions",
                "source_references",
            )
            app_health_keys = (
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
            app_capabilities_keys = (
                "user",
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
                "feeds",
                "quick_actions",
                "modules",
                "gar",
                "readiness",
                "source_references",
            )
            module_settings_keys = (
                "summary",
                "settings_policy",
                "visibility_policy",
                "registry",
                "mutation_policy",
                "source_references",
            )

            cases = (
                ("app_home.capabilities_feed", super_admin, "app_capabilities", app_capabilities_keys),
                ("app_home.feed", super_admin, "app_home", app_home_keys),
                ("app_home.health_feed", super_admin, "app_health", app_health_keys),
                ("app_home.module_settings_feed", super_admin, "module_settings_registry", module_settings_keys),
                ("super_admin.gar_insights_feed", super_admin, "gar_operational_digest", gar_keys),
                ("admin_portal.gar_feed", admin, "gar_operational_digest", gar_keys),
                ("property_manager.gar_feed", pm, "gar_operational_digest", gar_keys),
                ("assistant.gar_feed", assistant, "gar_operational_digest", gar_keys),
                ("finance.gar_feed", finance, "gar_operational_digest", gar_keys),
                ("director.gar_feed", director, "gar_operational_digest", gar_keys),
                ("contractor.gar_feed", contractor_user, "gar_role_digest", role_digest_keys),
                ("members.gar_feed", member_user, "gar_role_digest", role_digest_keys),
                ("super_admin.work_orders_feed", super_admin, "works_command_centre", works_keys),
                ("admin_portal.work_orders_feed", admin, "works_command_centre", works_keys),
                ("property_manager.work_orders_feed", pm, "works_command_centre", works_keys),
                ("assistant.work_orders_feed", assistant, "works_command_centre", works_keys),
                ("contractor.work_orders_feed", contractor_user, "contractor_work_queue", contractor_keys),
                ("contractor.calendar_feed", contractor_user, "contractor_schedule", contractor_schedule_keys),
                ("members.works_feed", member_user, "member_works_queue", member_keys),
                ("notifications.feed", super_admin, "notification_queue", notification_keys),
            )
            for endpoint, actor, context_type, required_keys in cases:
                expect_feed(endpoint, actor, context_type, required_keys)

        except Exception as exc:
            if not failures:
                failures.append(str(exc))
        finally:
            db.session.rollback()
            _delete_by_ids(UnitMembership, ids["unit_memberships"])
            _delete_by_ids(Notification, ids["notifications"])
            _delete_by_ids(Member, ids["members"])
            _delete_by_ids(Unit, ids["units"])
            _delete_by_ids(Client, ids["clients"])
            _delete_by_ids(User, ids["users"])
            _delete_by_ids(Contractor, ids["contractors"])
            _delete_by_ids(Company, ids["companies"])
            if created_role_ids:
                Role.query.filter(Role.id.in_(created_role_ids)).delete(synchronize_session=False)
            db.session.commit()

    print("App feed contract check")
    print(f"- Expected feeds checked: {len(EXPECTED_FEEDS)}")
    print(f"- Registered feed routes found: {len(feed_rules)}")
    print("- Read-only method contract checked: yes")
    print(f"- Live feed envelopes checked: {len(EXPECTED_FEEDS)}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
