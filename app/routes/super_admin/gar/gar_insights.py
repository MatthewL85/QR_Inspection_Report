# 📁 app/routes/super_admin/gar/gar_insights.py

from flask import render_template
from app.routes.super_admin import super_admin_bp
from app.decorators.role import super_admin_required
from flask_login import login_required, current_user

@super_admin_bp.route('/gar-insights', endpoint='gar_insights')
@login_required
@super_admin_required
def gar_insights():
    # Placeholder for future GAR logic
    gar_flagged_documents = []  # Replace this with real query when available
    return render_template(
        'super_admin/gar/gar_insights.html',
        gar_flagged_documents=gar_flagged_documents,
        user=current_user
    )
