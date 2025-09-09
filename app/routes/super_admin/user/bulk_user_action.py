# 📍 app/routes/super_admin/user/bulk_user_action.py

from flask import request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime

from app.models.core.user import User
from app.extensions import db
from app.routes.super_admin import super_admin_bp

from app.decorators.role import super_admin_required
from app.decorators.permissions import has_permission

@super_admin_bp.route('/users/bulk-action', methods=['POST'], endpoint='bulk_user_action')
@login_required
@super_admin_required
@has_permission('manage_users')
def bulk_user_action():
    """🛠️ Handle bulk user actions (Deactivate or Reactivate)."""
    
    user_ids = request.form.getlist('user_ids')
    action = request.form.get('action')

    if not user_ids or action not in ['deactivate', 'reactivate']:
        flash('⚠️ Invalid bulk action.', 'warning')
        return redirect(url_for('super_admin.manage_users'))

    users = User.query.filter(User.id.in_(user_ids)).all()

    for user in users:
        if action == 'deactivate':
            user.is_active = False
            user.deleted_at = datetime.utcnow()
        elif action == 'reactivate':
            user.is_active = True
            user.deleted_at = None

    db.session.commit()
    flash(f'✅ {len(users)} user(s) successfully {action}d.', 'success')
    return redirect(url_for('super_admin.manage_users'))
