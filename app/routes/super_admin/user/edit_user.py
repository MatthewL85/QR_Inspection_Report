from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from app.models import db, User
from app.forms.super_admin.edit_user_form import EditUserForm
from app.decorators.role import super_admin_required
from app.routes.super_admin import super_admin_bp
from app.services.user_profile_service import ensure_hr_profile_for_user


@super_admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'], endpoint='edit_user')
@login_required
@super_admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    form.populate_choices()

    if form.validate_on_submit():
        changes = {}

        full_name = form.full_name.data.strip()
        email = form.email.data.strip().lower()
        mobile_phone = request.form.get('mobile_phone', '').strip() or None
        direct_phone = request.form.get('direct_phone', '').strip() or None
        phone_extension = request.form.get('phone_extension', '').strip() or None

        if user.full_name != full_name:
            changes['full_name'] = (user.full_name, full_name)
            user.full_name = full_name

        if user.email != email:
            changes['email'] = (user.email, email)
            user.email = email

        if user.mobile_phone != mobile_phone:
            changes['mobile_phone'] = (user.mobile_phone, mobile_phone)
            user.mobile_phone = mobile_phone

        if user.direct_phone != direct_phone:
            changes['direct_phone'] = (user.direct_phone, direct_phone)
            user.direct_phone = direct_phone

        if user.phone_extension != phone_extension:
            changes['phone_extension'] = (user.phone_extension, phone_extension)
            user.phone_extension = phone_extension

        if form.password.data:
            user.password_hash = generate_password_hash(form.password.data)
            changes['password'] = ('[updated]', '[updated]')

        if user.role_id != form.role_id.data:
            changes['role_id'] = (user.role_id, form.role_id.data)
            user.role_id = form.role_id.data

        if user.company_id != form.company_id.data:
            changes['company_id'] = (user.company_id, form.company_id.data)
            user.company_id = form.company_id.data

        pin = (request.form.get('pin') or '').strip()
        if pin and user.pin != pin:
            changes['pin'] = ('[updated]', '[updated]')
            user.pin = pin

        is_active = bool(request.form.get('is_active'))
        if user.is_active != is_active:
            changes['is_active'] = (user.is_active, is_active)
            user.is_active = is_active

        ensure_hr_profile_for_user(user)
        db.session.commit()

        # Optional: wire audit logging here when the audit helper is formalised.
        _ = changes, current_user

        flash('User details updated successfully.', 'success')
        return redirect(url_for('super_admin.manage_users'))

    return render_template('super_admin/users/edit_user.html', form=form, user=user)
