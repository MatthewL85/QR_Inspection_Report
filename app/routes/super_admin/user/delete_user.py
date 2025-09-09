# 📍 app/routes/super_admin/user/delete_user.py

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime

from app.models.core.user import User
from app.extensions import db
from app.routes.super_admin import super_admin_bp

from app.decorators.role import super_admin_required
from app.decorators.permissions import has_permission

@super_admin_bp.route('/users/<int:user_id>/delete', methods=['GET', 'POST'], endpoint='delete_user')
@login_required
@super_admin_required
@has_permission('manage_users')
def delete_user(user_id):
    """🗑️ Soft delete (deactivate) a user after confirmation."""

    user = User.query.get_or_404(user_id)

    if request.method == 'POST' and request.form.get('confirm') == 'yes':
        user.is_active = False
        user.deleted_at = datetime.utcnow()
        db.session.commit()
        flash(f'✅ User {user.full_name} has been deactivated.', 'success')
        return redirect(url_for('super_admin.manage_users'))

    return render_template('super_admin/user/delete_user.html', user=user)

