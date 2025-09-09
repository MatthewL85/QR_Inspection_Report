from app.models.core.user import User
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


def authenticate_user(email, password):
    """
    Authenticate a user by verifying their email and password.
    Returns the User object if successful, else None.
    """
    user = User.query.filter_by(email=email).first()

    if user:
        print(f"✅ Found user: {user.email} | Role: {user.role.name if user.role else 'None'}")
    else:
        print("❌ No user found with that email.")

    if user and check_password_hash(user.password_hash, password):
        if user.is_active:
            print("✅ Password match. User is active.")
            return user
        else:
            print("⚠️ User is inactive.")
    else:
        print("❌ Password mismatch or user not found.")

    return None


def create_user(full_name, email, password, role_id=None, company_id=None):
    """
    Create and persist a new user with the given details.
    """
    if user_exists(email):
        raise ValueError(f"A user with email '{email}' already exists.")

    password_hash = generate_password_hash(password)
    new_user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        role_id=role_id,
        company_id=company_id,
        is_active=True
    )

    db.session.add(new_user)
    db.session.commit()
    print(f"✅ Created user: {new_user.email}")
    return new_user


def user_exists(email):
    """
    Check if a user with the given email already exists.
    """
    return User.query.filter_by(email=email).first() is not None
