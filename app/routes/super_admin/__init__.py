from flask import Blueprint

super_admin_bp = Blueprint('super_admin', __name__)

# Optional: Register routes here or in separate files
from app.routes.super_admin import dashboard
