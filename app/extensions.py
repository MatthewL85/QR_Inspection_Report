# 📦 app/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer

# 🔌 Core Extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

# 🔐 Secure Token Generator (for password reset, verification, etc.)
serializer = URLSafeTimedSerializer("temporary-placeholder-key")  # This is overridden in create_app()

# 🧠 Login Manager Setup
def register_login_loader(app):
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'  # Bootstrap alert class
