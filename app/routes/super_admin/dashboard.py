# app/routes/super_admin/dashboard.py

from flask import Blueprint, render_template
from app.decorators import super_admin_required

super_admin_bp = Blueprint('super_admin', __name__, url_prefix='/super-admin')

@super_admin_bp.route('/dashboard', endpoint='dashboard')
@super_admin_required
def dashboard():
    return render_template('super_admin/dashboard.html')
