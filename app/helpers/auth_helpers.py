from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User

def user_exists(email):
    return User.query.filter_by(email=email).first() is not None

def create_user(email, password, role, company_id=None, full_name=None):
    hashed_password = generate_password_hash(password)
    new_user = User(
        email=email,
        password_hash=hashed_password,
        role=role,
        company_id=company_id,
        full_name=full_name
    )
    db.session.add(new_user)
    db.session.commit()

def authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        return user
    return None
