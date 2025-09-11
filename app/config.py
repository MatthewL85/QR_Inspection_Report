# 📁 app/config.py
import os
from pathlib import Path

# ----- helpers -----
def env_bool(key: str, default: bool = False) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "t", "yes", "y", "on")

def env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, default))
    except Exception:
        return default

def env_list(key: str, default=None, sep=","):
    if default is None:
        default = []
    v = os.getenv(key)
    if not v:
        return default
    return [s.strip() for s in v.split(sep) if s.strip()]

def _database_url() -> str:
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        # local fallback (sqlite) if you’re not using Postgres locally
        return "sqlite:///" + str((Path(__file__).resolve().parent / ".." / "app.db").resolve())
    # Normalize postgres:// to postgresql:// for SQLAlchemy
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url

def _extra_from_env() -> dict:
    """Collect any extra keys from env with prefix APP_CFG_* (e.g. APP_CFG_SERVER_NAME)."""
    out = {}
    for k, v in os.environ.items():
        if k.startswith("APP_CFG_"):
            out[k[len("APP_CFG_"):]] = v
    return out

# ---------- Base ----------
class BaseConfig:
    # Flask / security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    WTF_CSRF_SECRET_KEY = os.getenv("WTF_CSRF_SECRET_KEY", "dev-csrf-key-change-me")
    WTF_CSRF_ENABLED = True

    # Database
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": env_int("SQLA_POOL_RECYCLE", 280),
    }

    # Babel / i18n
    BABEL_DEFAULT_LOCALE = os.getenv("BABEL_DEFAULT_LOCALE", "en")
    BABEL_DEFAULT_TIMEZONE = os.getenv("BABEL_DEFAULT_TIMEZONE", "UTC")

    # Mail (Gmail SMTP example)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = env_int("MAIL_PORT", 587)
    MAIL_USE_TLS = env_bool("MAIL_USE_TLS", True)
    MAIL_USE_SSL = env_bool("MAIL_USE_SSL", False)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")          # your Gmail address
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")          # app password if 2FA
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", os.getenv("MAIL_USERNAME"))
    MAIL_SUPPRESS_SEND = env_bool("MAIL_SUPPRESS_SEND", False)
    MAIL_MAX_EMAILS = None

    # Uploads
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        str((Path(__file__).resolve().parent / "static" / "uploads").resolve())
    )
    MAX_CONTENT_LENGTH = env_int("MAX_CONTENT_LENGTH", 100 * 1024 * 1024)  # 100 MB

    # Allowed file extensions (images, iPhone media, video, audio, email files, docs)
    ALLOWED_EXTENSIONS = {
        # images / photos
        "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp", "heic", "heif",
        # video
        "mp4", "mov", "m4v", "avi", "mkv", "webm", "mpeg", "mpg",
        # audio
        "mp3", "m4a", "aac", "wav", "ogg",
        # email files
        "eml", "msg",
        # docs
        "pdf", "txt", "csv", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        # misc
        "json"
    }

    # HTML/PDF generation toggles
    WKHTMLTOPDF_BINARY = os.getenv("WKHTMLTOPDF_BINARY", "")
    WEASYPRINT_ENABLED = env_bool("WEASYPRINT_ENABLED", False)

    # Cookies / sessions / proxies
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    PERMANENT_SESSION_LIFETIME = env_int("PERMANENT_SESSION_LIFETIME", 60 * 60 * 24 * 31)  # 31 days
    PREFERRED_URL_SCHEME = os.getenv("PREFERRED_URL_SCHEME", "https")
    SERVER_NAME = os.getenv("SERVER_NAME")  # leave unset unless you know you need it

    # App constants
    APP_NAME = os.getenv("APP_NAME", "QR Inspection Report")
    PAGINATION_PAGE_SIZE = env_int("PAGINATION_PAGE_SIZE", 25)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ---------- Environments ----------
class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = env_bool("SQLALCHEMY_ECHO", False)
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    PREFERRED_URL_SCHEME = "http"

class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"

class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

# Back-compat
Config = ProductionConfig

# Inject APP_CFG_* overrides onto all classes
_EXTRA = _extra_from_env()
if _EXTRA:
    for _cls in (BaseConfig, DevelopmentConfig, ProductionConfig, TestingConfig):
        for _k, _v in _EXTRA.items():
            setattr(_cls, _k, _v)

# Legacy defaults spot (optional)
LEGACY_DEFAULTS = {
    # "DEFAULT_SUPERADMIN_EMAIL": "owner@example.com",
    # "DEFAULT_SUPERADMIN_PASSWORD": "ChangeMe!123",
}
for _cls in (BaseConfig, DevelopmentConfig, ProductionConfig, TestingConfig):
    for _k, _v in LEGACY_DEFAULTS.items():
        setattr(_cls, _k, _v)
