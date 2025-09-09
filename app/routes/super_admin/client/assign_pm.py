# 📍 app/routes/super_admin/client/assign_pm.py

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models.client.client import Client
from app.models.core.user import User
from app.models.core.role import Role
from app.routes.super_admin import super_admin_bp
from app.decorators.role import super_admin_required


@super_admin_bp.route('/clients/<int:client_id>/assign/', methods=['GET', 'POST'], endpoint='assign_pm')
@login_required
@super_admin_required
def assign_pm(client_id):
    client = Client.query.get_or_404(client_id)

    # 🔍 Use role name to avoid hardcoding role_id=3
    pm_role = Role.query.filter_by(name='Property Manager').first()
    if not pm_role:
        flash('❌ Property Manager role not found.', 'danger')
        return redirect(url_for('super_admin.manage_clients'))

    pms = User.query.filter_by(role_id=pm_role.id, is_active=True).order_by(User.full_name).all()

    if request.method == 'POST':
        pm_id = request.form.get('property_manager_id')
        selected_pm = User.query.get(pm_id)

        if selected_pm and selected_pm.role_id == pm_role.id:
            client.property_manager_id = selected_pm.id
            db.session.commit()
            flash(f'✅ {selected_pm.full_name} assigned to {client.name} as Property Manager.', 'success')
            return redirect(url_for('super_admin.manage_clients'))
        else:
            flash('⚠️ Invalid or unauthorized Property Manager selected.', 'warning')

    return render_template(
        'super_admin/client/assign_pm.html',
        client=client,
        pms=pms
    )
