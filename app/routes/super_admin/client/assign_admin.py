# 📍 app/routes/super_admin/client/assign_admin.py

from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app.routes.super_admin.client import client_bp
from app.forms.super_admin.client.assign_admin_form import AssignAdminForm
from app.models.core.user import User
from app.models.client.client import Client
from app.models.core.role import Role
from app.extensions import db
from app.decorators import super_admin_required


@client_bp.route('/assign-admin', methods=['GET', 'POST'], endpoint='assign_admin')
@login_required
@super_admin_required
def assign_admin():
    form = AssignAdminForm()

    # 🎯 Dynamically fetch only active Admin users
    admin_role = Role.query.filter_by(name='Admin').first()
    if not admin_role:
        flash("❌ Admin role not found in system.", "danger")
        return redirect(url_for('super_admin.manage_clients'))

    form.admin_id.choices = [
        (u.id, u.full_name)
        for u in User.query.filter_by(role_id=admin_role.id, is_active=True)
        .order_by(User.full_name.asc()).all()
    ]

    form.client_id.choices = [
        (c.id, c.name) for c in Client.query.order_by(Client.name.asc()).all()
    ]

    if form.validate_on_submit():
        admin = User.query.get(form.admin_id.data)
        client = Client.query.get(form.client_id.data)

        if not admin or not client:
            flash("❌ Invalid selection. Please try again.", "danger")
            return render_template('super_admin/client/assign_admin.html', form=form)

        # 🧩 Assign the Admin to the client
        client.admin_id = admin.id
        db.session.commit()

        flash(f"✅ {admin.full_name} assigned to client {client.name}", "success")
        return redirect(url_for('super_admin.manage_clients'))

    return render_template('super_admin/client/assign_admin.html', form=form)
