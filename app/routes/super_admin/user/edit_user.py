# 📄 app/routes/super_admin/user/edit_user.py

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from app.models import db, User
from app.forms.super_admin.edit_user_form import EditUserForm
from app.decorators.role import super_admin_required
from app.decorators.permissions import has_permission
from app.routes.super_admin import super_admin_bp
# from app.utils.audit import log_audit_change  # 🔍 Uncomment if/when implemented


@super_admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'], endpoint='edit_user')
@login_required
@super_admin_required
def edit_user(user_id):
    """✏️ Super Admin route to edit an existing user."""

    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    form.populate_choices()

    if form.validate_on_submit():
        changes = {}

        if user.full_name != form.full_name.data.strip():
            changes['full_name'] = (user.full_name, form.full_name.data.strip())
            user.full_name = form.full_name.data.strip()

        if user.email != form.email.data.lower():
            changes['email'] = (user.email, form.email.data.lower())
            user.email = form.email.data.lower()

        if form.password.data:
            user.password_hash = generate_password_hash(form.password.data)
            changes['password'] = ('[updated]', '[updated]')

        if user.role_id != form.role_id.data:
            changes['role_id'] = (user.role_id, form.role_id.data)
            user.role_id = form.role_id.data

        if user.company_id != form.company_id.data:
            changes['company_id'] = (user.company_id, form.company_id.data)
            user.company_id = form.company_id.data

        db.session.commit()

        # Optional: Log audit trail of what changed
        # if changes:
        #     log_audit_change(user_id=current_user.id, target='User', target_id=user.id, changes=changes)

        flash('✅ User details updated successfully.', 'success')
        return redirect(url_for('super_admin.manage_users'))

    return render_template('super_admin/user/edit_user.html', form=form, user=user)
