# 📍 app/routes/super_admin/user/reactivate_user.py

from flask import redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

from app.models.core.user import User
from app.extensions import db
from app.routes.super_admin import super_admin_bp
from app.utils.audit import log_profile_change

from app.decorators.role import super_admin_required
from app.decorators.permissions import has_permission


@super_admin_bp.route('/users/<int:user_id>/reactivate', methods=['POST'], endpoint='reactivate_user')
@login_required
@super_admin_required
@has_permission('manage_users')
def reactivate_user(user_id):
    """♻️ Reactivate a previously deactivated (soft-deleted) user."""

    user = User.query.get_or_404(user_id)

    if user.is_active:
        flash('ℹ️ User is already active.', 'info')
        return redirect(url_for('super_admin.manage_users'))

    # 📝 Capture old values for audit logging
    old_status = user.is_active
    old_deleted_at = user.deleted_at

    # 🔄 Reactivate user
    user.is_active = True
    user.deleted_at = None
    db.session.commit()

    # 🧾 Log changes to audit log
    log_profile_change(
        user_id=user.id,
        field_name='is_active',
        old_value=old_status,
        new_value=True,
        change_reason='User reactivated by Super Admin'
    )
    log_profile_change(
        user_id=user.id,
        field_name='deleted_at',
        old_value=old_deleted_at,
        new_value=None,
        change_reason='User reactivated by Super Admin'
    )

    flash(f'✅ User {user.full_name} has been reactivated.', 'success')
    return redirect(url_for('super_admin.manage_users'))
