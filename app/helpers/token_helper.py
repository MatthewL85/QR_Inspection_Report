from itsdangerous import URLSafeTimedSerializer
from flask import current_app


def generate_reset_token(email, salt='password-reset'):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=salt)


def verify_reset_token(token, expiration=3600, salt='password-reset'):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=salt, max_age=expiration)
        return email
    except Exception:
        return None
