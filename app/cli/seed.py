# app/cli/seed.py
from datetime import datetime
from werkzeug.security import generate_password_hash
from flask import current_app
from app.extensions import db
from app.models.onboarding.company import Company
from app.models.core.role import Role
from app.models.core.user import User

DEFAULT_ROLES = [
    ("Super Admin", True, True),
    ("Admin", True, True),
    ("Property Manager", True, True),
    ("Financial Controller", True, True),
    ("Director", True, True),
    ("Contractor", True, True),
    ("Member", True, False),
    ("Resident", True, False),
]

def upsert_roles():
    created = 0
    for name, is_active, is_assignable in DEFAULT_ROLES:
        role = Role.query.filter_by(name=name).first()
        if not role:
            role = Role(name=name, is_active=is_active, is_assignable=is_assignable)
            db.session.add(role)
            created += 1
    return created

def seed_company_and_owner(
    company_name="Bohan Hyland Estate Management",
    owner_full_name="Matthew Lavery",
    owner_email="owner@example.com",
    owner_password="Owner123!",
    subdomain="demo"
):
    # 1) Company
    company = Company.query.filter_by(name=company_name).first()
    if not company:
        company = Company(
            name=company_name,
            company_type="Property Management",
            country="Ireland",
            region="Dublin",
            city="Dublin",
            currency="EUR",
            timezone="Europe/Dublin",
            preferred_language="en",
            email="info@example.com",
            phone="+353 1 234 5678",
            website="https://example.com",
            address_line1="53A Rathgar Ave",
            postal_code="D06 K5K2",
            data_protection_compliant=True,
            consent_to_communicate=True,
            terms_agreed=True,
            is_active=True,
            onboarding_step="complete",
            onboarding_completed=True,
            subdomain=subdomain,
            plan="trial",
            created_at=datetime.utcnow(),
        )
        db.session.add(company)

    # 2) Roles
    upsert_roles()
    db.session.flush()  # ensure role ids

    super_admin_role = Role.query.filter_by(name="Super Admin").first()

    # 3) Owner user (Super Admin) linked to that company
    owner = User.query.filter_by(email=owner_email).first()
    if not owner:
        owner = User(
            full_name=owner_full_name,
            email=owner_email,
            username="owner",
            password_hash=generate_password_hash(owner_password),
            role_id=super_admin_role.id if super_admin_role else None,
            company_id=company.id,
            is_active=True,
            pin="Abc123!@",  # just for dev
        )
        db.session.add(owner)

    return company, owner

def seed_all():
    created_roles = upsert_roles()
    company, owner = seed_company_and_owner()
    db.session.commit()
    return created_roles, company, owner
