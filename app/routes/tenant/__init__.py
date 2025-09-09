# app/routes/tenant/__init__.py
from flask import Blueprint
tenant_bp = Blueprint("tenant", __name__, url_prefix="/tenant")

# and in app/__init__.py after creating app:
from app.routes.tenant import tenant_bp

