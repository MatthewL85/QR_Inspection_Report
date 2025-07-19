# scripts/seed_roles.py

from app.extensions import db
from app.models.core.role import Role
from app import create_app

def seed_roles():
    app = create_app()
    with app.app_context():
        default_roles = [
            "Super Admin",
            "Admin",
            "Property Manager",
            "Contractor",
            "Contractor Team",
            "Director",
            "Resident",  # for Members Logix
            "Owner",     # optional
        ]

        created_count = 0
        for role_name in default_roles:
            existing = Role.query.filter_by(name=role_name).first()
            if not existing:
                db.session.add(Role(name=role_name))
                created_count += 1

        if created_count:
            db.session.commit()
            print(f"✅ Seeded {created_count} new roles.")
        else:
            print("ℹ️ All default roles already exist.")

if __name__ == "__main__":
    seed_roles()
