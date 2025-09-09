# 📍 app/routes/super_admin/client/__init__.py

from flask import Blueprint

client_bp = Blueprint('client_bp', __name__)

# 🔁 Import assignment routes
from . import assign_pm, assign_fc, assign_admin, manage_client, edit_client, add_client
from .capex import capex_add, capex_delete, capex_edit, capex_list
