# 📁 app/config.py

import os
from dotenv import load_dotenv

# Load .env variables
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '..', '.env'))  # Load from project root

class Config:
    # 🔐 Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback_dev_secret_key')

    # 🗄️ Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 📁 Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads/contracts')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'mov', 'avi'}
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB max upload size

    # ✅ CSRF Protection
    WTF_CSRF_ENABLED = True

    # ✉️ Email Settings (use env for real deployment)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 'yes']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME') or 'your_email@example.com'
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD') or 'your_app_password'
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER') or 'noreply@logixpm.io'
    WKHTMLTOPDF_BINARY = os.getenv("WKHTMLTOPDF_BINARY")
    WEASYPRINT_ENABLED = os.getenv("WEASYPRINT_ENABLED", "1") == "1"

    BABEL_DEFAULT_LOCALE = "en"
    BABEL_DEFAULT_TIMEZONE = "UTC"

