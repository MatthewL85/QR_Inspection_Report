from flask import render_template
from flask_login import login_required
from app.decorators import super_admin_required
from app.routes.super_admin import super_admin_bp

@super_admin_bp.route('/upcoming-agms', endpoint='upcoming_agms')
@super_admin_required
@login_required
def upcoming_agms():
    # Optional: fetch upcoming AGM data here
    return render_template('super_admin/agms/upcoming_agms.html')
