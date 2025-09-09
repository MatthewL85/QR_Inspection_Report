# 📍 app/routes/super_admin/user/bulk_deactivate_users.py

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required

from app.models.core.user import User
from app.extensions import db
from app.routes.super_admin import super_admin_bp

from app.decorators.role import super_admin_required
from app.decorators.permissions import has_permission

@super_admin_bp.route('/users/bulk-deactivate', methods=['POST'], endpoint='bulk_deactivate_users')
@login_required
@super_admin_required
@has_permission('manage_users')
def bulk_deactivate_users():
    """🚫 Bulk deactivation route for Super Admin to disable selected users."""
    
    user_ids = request.form.getlist('selected_users')

    if not user_ids:
        flash("⚠️ No users were selected for deactivation.", "warning")
        return redirect(url_for('super_admin.manage_users'))

    deactivated_count = 0

    for user_id in user_ids:
        user = User.query.get(user_id)
        if user and user.is_active:
            user.is_active = False
            deactivated_count += 1

    db.session.commit()

    flash(f"✅ {deactivated_count} user(s) successfully deactivated.", "success")
    return redirect(url_for('super_admin.manage_users'))
