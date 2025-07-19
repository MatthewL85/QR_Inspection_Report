# scripts/seed_super_admin.py

from app.extensions import db
from app.models.core.user import User
from app.models.core.role import Role
from werkzeug.security import generate_password_hash
from app import create_app

def seed_super_admin():
    app = create_app()
    with app.app_context():
        existing_user = User.query.filter_by(email='superadmin@logixpm.com').first()
        if existing_user:
            print("⚠️ Super Admin already exists.")
            return

        role = Role.query.filter_by(name='Super Admin').first()
        if not role:
            print("❌ Super Admin role not found. Seed roles first.")
            return

        super_admin = User(
            full_name='System Super Admin',
            email='superadmin@logixpm.com',
            password=generate_password_hash('SuperSecure123!'),
            role_id=role.id,
            is_active=True
        )
        db.session.add(super_admin)
        db.session.commit()
        print("✅ Super Admin seeded.")

if __name__ == "__main__":
    seed_super_admin()
