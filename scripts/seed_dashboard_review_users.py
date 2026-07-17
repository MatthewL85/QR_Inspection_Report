"""Seed local review logins for each current dashboard/user type.

This is intentionally idempotent: running it again updates the same accounts
instead of creating duplicates.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sys

from werkzeug.security import generate_password_hash


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
from app.services.user_profile_service import ensure_hr_profile_for_user


REVIEW_PASSWORD = "review2026"
MANAGEMENT_COMPANY_NAME = "Bohan Hyland Estate Management"
CONTRACTOR_COMPANY_NAME = "Review Contractor Services"
TEST_CLIENT_NAME = "Matthew Lavery"


@dataclass(frozen=True)
class ReviewAccount:
    label: str
    email: str
    username: str
    full_name: str
    role_name: str
    dashboard: str
    mobile: str
    direct: str = ""
    extension: str = ""


ACCOUNTS = (
    ReviewAccount(
        label="Super Admin",
        email="review.superadmin@logixpm.test",
        username="review_superadmin",
        full_name="Review Super Admin",
        role_name="Super Admin",
        dashboard="/super-admin/dashboard",
        mobile="+353860000001",
        direct="+35314913001",
        extension="101",
    ),
    ReviewAccount(
        label="Admin Portal",
        email="review.admin@logixpm.test",
        username="review_admin",
        full_name="Review Admin",
        role_name="Admin",
        dashboard="/admin-portal/dashboard",
        mobile="+353860000002",
        direct="+35314913002",
        extension="102",
    ),
    ReviewAccount(
        label="Property Manager",
        email="review.pm@logixpm.test",
        username="review_pm",
        full_name="Review Property Manager",
        role_name="Property Manager",
        dashboard="/pm/dashboard",
        mobile="+353860000003",
        direct="+35314913003",
        extension="103",
    ),
    ReviewAccount(
        label="Assistant",
        email="review.assistant@logixpm.test",
        username="review_assistant",
        full_name="Review Assistant",
        role_name="Assistant Property Manager",
        dashboard="/assistant/dashboard",
        mobile="+353860000004",
        direct="+35314913004",
        extension="104",
    ),
    ReviewAccount(
        label="Assistant Manager / Cover",
        email="review.assistant.manager@logixpm.test",
        username="review_assistant_manager",
        full_name="Review Assistant Manager",
        role_name="Assistant Manager",
        dashboard="/assistant/dashboard",
        mobile="+353860000005",
        direct="+35314913005",
        extension="105",
    ),
    ReviewAccount(
        label="Finance Logix",
        email="review.finance@logixpm.test",
        username="review_finance",
        full_name="Review Financial Controller",
        role_name="Financial Controller",
        dashboard="/finance/dashboard",
        mobile="+353860000006",
        direct="+35314913006",
        extension="106",
    ),
    ReviewAccount(
        label="Contractor Logix",
        email="review.contractor@logixpm.test",
        username="review_contractor",
        full_name="Review Contractor",
        role_name="Contractor",
        dashboard="/contractor/dashboard",
        mobile="+353860000007",
        direct="+35314913007",
        extension="107",
    ),
    ReviewAccount(
        label="Director Logix",
        email="review.director@logixpm.test",
        username="review_director",
        full_name="Review Director",
        role_name="Director",
        dashboard="/director/dashboard",
        mobile="+353860000008",
        direct="+35314913008",
        extension="108",
    ),
    ReviewAccount(
        label="Members Logix - Owner",
        email="review.member@logixpm.test",
        username="review_member",
        full_name="Review Member Owner",
        role_name="Member",
        dashboard="/members/dashboard",
        mobile="+353860000009",
        direct="+35314913009",
        extension="109",
    ),
    ReviewAccount(
        label="Members Logix - Resident",
        email="review.resident@logixpm.test",
        username="review_resident",
        full_name="Review Resident",
        role_name="Resident",
        dashboard="/members/dashboard",
        mobile="+353860000010",
        direct="+35314913010",
        extension="110",
    ),
)


def get_or_create_role(name: str) -> Role:
    role = Role.query.filter_by(name=name).first()
    if role:
        role.is_active = True
        role.is_assignable = True
        return role

    role = Role(
        name=name,
        description=f"Seeded review role for {name}",
        is_active=True,
        is_assignable=True,
    )
    db.session.add(role)
    db.session.flush()
    return role


def get_management_company() -> Company:
    company = Company.query.filter_by(name=MANAGEMENT_COMPANY_NAME).first()
    if company:
        return company

    company = Company.query.order_by(Company.id.asc()).first()
    if company:
        return company

    company = Company(
        name=MANAGEMENT_COMPANY_NAME,
        company_type="management",
        country="Ireland",
        region="Dublin",
        currency="EUR",
        timezone="Europe/Dublin",
        is_active=True,
        onboarding_completed=True,
        terms_agreed=True,
        consent_to_communicate=True,
    )
    db.session.add(company)
    db.session.flush()
    return company


def get_contractor_company() -> Company:
    company = Company.query.filter_by(name=CONTRACTOR_COMPANY_NAME).first()
    if company:
        company.company_type = "Contractor"
        company.is_active = True
        company.onboarding_completed = True
        return company

    company = Company(
        name=CONTRACTOR_COMPANY_NAME,
        company_type="Contractor",
        country="Ireland",
        region="Dublin",
        currency="EUR",
        timezone="Europe/Dublin",
        is_active=True,
        onboarding_completed=True,
        terms_agreed=True,
        consent_to_communicate=True,
    )
    db.session.add(company)
    db.session.flush()
    return company


def get_or_create_contractor(contractor_company: Company) -> Contractor:
    contractor = Contractor.query.filter_by(company_name=CONTRACTOR_COMPANY_NAME).first()
    if contractor:
        contractor.is_active = True
        contractor.company_id = contractor_company.id
        return contractor

    contractor = Contractor(
        company_id=contractor_company.id,
        company_name=CONTRACTOR_COMPANY_NAME,
        email="review.contractor@logixpm.test",
        phone="+35314913007",
        contact_name="Review Contractor",
        contact_email="review.contractor@logixpm.test",
        business_type="General Maintenance",
        contractor_type="Review Account",
        region="Dublin",
        coverage_area="Dublin",
        is_active=True,
        consent_to_contact=True,
        performance_rating="A",
        gar_trust_score=82,
        is_gar_preferred=True,
        source_system="Dashboard review seed",
        sync_status="Seeded",
    )
    db.session.add(contractor)
    db.session.flush()
    return contractor


def upsert_user(account: ReviewAccount, company: Company, contractor: Contractor | None = None) -> User:
    role = get_or_create_role(account.role_name)
    user = User.query.filter_by(email=account.email).first()
    if not user:
        user = User(email=account.email)
        db.session.add(user)

    user.full_name = account.full_name
    user.username = account.username
    user.password_hash = generate_password_hash(REVIEW_PASSWORD)
    user.role_id = role.id
    user.company_id = company.id
    user.contractor_id = contractor.id if contractor else None
    user.mobile_phone = account.mobile
    user.direct_phone = account.direct
    user.phone_extension = account.extension
    user.pin = "2026"
    user.is_active = True
    user.deleted_at = None
    user.email_verified = True
    user.consent_to_contact = True
    user.data_sharing_opt_in = True
    user.role_visibility_scope = "Review"
    user.parsing_status = "Seeded"
    user.gar_chat_ready = True
    db.session.flush()
    ensure_hr_profile_for_user(user)
    return user


def split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.split(" ", 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def get_review_unit(client: Client | None) -> Unit | None:
    if not client:
        return Unit.query.order_by(Unit.id.asc()).first()

    return (
        Unit.query
        .filter_by(client_id=client.id)
        .filter(Unit.is_active.is_(True))
        .order_by(Unit.block_name.asc().nullslast(), Unit.unit_number.asc().nullslast(), Unit.id.asc())
        .first()
    )


def upsert_member_profile(user: User, client: Client | None, unit: Unit | None, role: str) -> None:
    first_name, last_name = split_name(user.full_name)
    member = Member.query.filter_by(user_id=user.id).first()
    if not member:
        member = Member(user_id=user.id)
        db.session.add(member)

    member.client_id = client.id if client else getattr(unit, "client_id", None)
    member.company_id = user.company_id
    member.first_name = first_name
    member.last_name = last_name
    member.email = user.email
    member.phone = user.mobile_phone
    member.postal_address_line1 = "Review Account"
    member.postal_city = "Dublin"
    member.postal_region = "Dublin"
    member.postal_country = "Ireland"
    member.preferred_contact_method = "portal"
    member.is_owner = role == "owner"
    member.is_owner_occupier = role == "owner"
    member.is_active = True
    member.contact_consent = True
    member.data_sharing_opt_in = True
    member.source_system = "Dashboard review seed"
    db.session.flush()

    if not unit:
        return

    link = UnitMembership.query.filter_by(
        unit_id=unit.id,
        member_id=member.id,
        role=role,
    ).first()
    if not link:
        link = UnitMembership(unit_id=unit.id, member_id=member.id, role=role)
        db.session.add(link)

    link.is_primary = role == "owner"
    link.is_current = True
    link.notes = "Seeded dashboard review membership."
    if role == "owner":
        link.ownership_start_date = date(2026, 1, 1)
        link.ownership_end_date = None
    else:
        link.tenancy_start_date = date(2026, 1, 1)
        link.tenancy_end_date = None


def assign_test_client_users(users_by_role: dict[str, User], client: Client | None) -> None:
    if not client:
        return

    pm = users_by_role.get("Property Manager")
    fc = users_by_role.get("Financial Controller")
    assistant = users_by_role.get("Assistant Property Manager")

    if pm:
        client.assigned_pm_id = pm.id
    if fc:
        client.assigned_fc_id = fc.id
    if assistant and hasattr(client, "assigned_assistant_id"):
        client.assigned_assistant_id = assistant.id


def seed() -> None:
    app = create_app()
    with app.app_context():
        company = get_management_company()
        contractor_company = get_contractor_company()
        contractor = get_or_create_contractor(contractor_company)
        client = Client.query.filter(Client.name.ilike(TEST_CLIENT_NAME)).first()
        review_unit = get_review_unit(client)

        users_by_role: dict[str, User] = {}
        created_or_updated: list[tuple[ReviewAccount, User]] = []

        for account in ACCOUNTS:
            linked_contractor = contractor if account.role_name == "Contractor" else None
            user_company = contractor_company if account.role_name == "Contractor" else company
            user = upsert_user(account, user_company, linked_contractor)
            users_by_role[account.role_name] = user
            created_or_updated.append((account, user))

        assign_test_client_users(users_by_role, client)

        member_user = users_by_role.get("Member")
        resident_user = users_by_role.get("Resident")
        if member_user:
            upsert_member_profile(member_user, client, review_unit, "owner")
        if resident_user:
            upsert_member_profile(resident_user, client, review_unit, "resident")

        db.session.commit()

        print("Dashboard review users seeded")
        print(f"- Password for all review accounts: {REVIEW_PASSWORD}")
        print(f"- Company: {company.name} (id={company.id})")
        print(f"- Contractor company: {contractor_company.name} (id={contractor_company.id})")
        if client:
            print(f"- Test client linked: {client.name} (id={client.id})")
        if review_unit:
            print(f"- Members review unit: {review_unit.unit_label} (id={review_unit.id})")
        print("")
        for account, user in created_or_updated:
            print(f"{account.label}: {account.email} / {account.username} -> {account.dashboard} (user_id={user.id})")
        print("")
        print("HR Logix note: HR has data/model foundation and profiles can be created, but no dedicated /hr dashboard exists yet.")


if __name__ == "__main__":
    seed()
