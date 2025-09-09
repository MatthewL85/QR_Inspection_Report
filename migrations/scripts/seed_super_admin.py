from app import create_app
from app.extensions import db
from app.models.core.user import User
from app.models.core.role import Role
from werkzeug.security import generate_password_hash
from datetime import datetime

def seed_super_admin():
    app = create_app()
    with app.app_context():
        from flask import current_app
        print("🔧 Seeding into:", current_app.config['SQLALCHEMY_DATABASE_URI'], flush=True)

        # Super Admin credentials
        email = 'superadmin@logixpm.com'
        password = 'SuperSecure123!'
        pin = '000000'

        # Check if Super Admin already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"⚠️ Super Admin already exists: {existing_user.email}", flush=True)
            return

        # Find or create Super Admin role
        role = Role.query.filter_by(name='Super Admin').first()
        if not role:
            print("❌ Role 'Super Admin' not found. Please run seed_roles.py first.", flush=True)
            return

        # Create new Super Admin
        super_admin = User(
            full_name='System Super Admin',
            email=email,
            password_hash=generate_password_hash(password),
            pin=pin,
            role_id=role.id,
            is_active=True,
            created_at=datetime.utcnow()
        )

        db.session.add(super_admin)
        db.session.commit()

        print("✅ Super Admin seeded successfully!", flush=True)
        print(f"🔐 Email: {email}")
        print(f"🔐 Password: {password}")
        print(f"🔐 PIN: {pin}")

if __name__ == "__main__":
    seed_super_admin()

