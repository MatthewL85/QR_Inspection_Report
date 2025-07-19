from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    if not User.query.filter_by(email="admin@example.com").first():
        test_user = User(
            full_name="Test Admin",
            email="admin@example.com",
            password_hash=generate_password_hash("password123"),
            role="Admin",
            company_id=None  # adjust if needed
        )
        db.session.add(test_user)
        db.session.commit()
        print("✅ Test user created: admin@example.com / password123")
    else:
        print("⚠️ User already exists.")
