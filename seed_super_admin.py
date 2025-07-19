from app import create_app
from app.extensions import db
from app.models import User, Role
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    role = Role.query.filter_by(name='Super Admin').first()
    if not role:
        role = Role(name='Super Admin')
        db.session.add(role)
        db.session.commit()
        print("✅ Created 'Super Admin' role")

    existing_user = User.query.filter_by(email='superadmin@logixpm.com').first()
    if existing_user:
        print("⚠️ Super Admin already exists:", existing_user.email)
    else:
        user = User(
            full_name='Super Admin',
            email='superadmin@logixpm.com',
            password=generate_password_hash('Admin123!', method='pbkdf2:sha256'),
            role_id=role.id,
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        print("✅ Super Admin seeded: superadmin@logixpm.com | Password: Admin123!")
