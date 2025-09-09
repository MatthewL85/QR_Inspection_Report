# 📍 app/routes/super_admin/client/assign_fc.py

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.decorators.role import super_admin_required
from app.routes.super_admin import super_admin_bp
from app.extensions import db
from app.models.client.client import Client
from app.models.core.user import User
from app.models.core.role import Role


@super_admin_bp.route('/clients/<int:client_id>/assign-fc', methods=['GET', 'POST'], endpoint='assign_fc')
@login_required
@super_admin_required
def assign_fc(client_id):
    client = Client.query.get_or_404(client_id)

    # 🔍 Lookup FCs by role name (not hardcoded ID)
    fc_role = Role.query.filter_by(name='Financial Controller').first()
    if not fc_role:
        flash('❌ Financial Controller role not found.', 'danger')
        return redirect(url_for('super_admin.manage_clients'))

    financial_controllers = User.query.filter_by(role_id=fc_role.id, is_active=True).order_by(User.full_name).all()

    if request.method == 'POST':
        selected_fc_id = request.form.get('financial_controller_id')
        selected_fc = User.query.get(selected_fc_id)

        if selected_fc and selected_fc.role_id == fc_role.id:
            client.financial_controller_id = selected_fc.id
            db.session.commit()
            flash(f'✅ {selected_fc.full_name} assigned to {client.name} as Financial Controller.', 'success')
            return redirect(url_for('super_admin.manage_clients'))
        else:
            flash('❌ Invalid or unauthorized selection.', 'danger')

    return render_template(
        'super_admin/client/assign_fc.html',
        client=client,
        financial_controllers=financial_controllers
    )
