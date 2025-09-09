# app/routes/super_admin/client/manage_client.py

from datetime import date

from flask import render_template, abort
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app.models import db
from app.models.client.client import Client          # concrete model path
from app.models.core.user import User
from app.routes.super_admin import super_admin_bp
from app.decorators import super_admin_required


# 🧭 Manage Clients – list view (now includes `today` for expiry badges)
@super_admin_bp.route('/clients', methods=['GET'], endpoint='manage_clients')
@super_admin_required
@login_required
def manage_clients():
    """
    Lists clients for the current tenant/company, preloading related staff so the
    template can render without N+1 queries. We also inject `today` so the Jinja
    template can compute 'days to expiry' badges client-side.
    """
    q = (
        Client.query
        .options(
            joinedload(Client.assigned_pm),
            joinedload(Client.assigned_fc),
            joinedload(Client.assigned_assistant),
        )
    )

    # Multi-tenant safety: scope to current user's company if present
    if getattr(current_user, "company_id", None):
        q = q.filter(Client.company_id == current_user.company_id)

    clients = q.order_by(Client.name.asc()).all()

    # Pass `today` for Jinja date math on contract_end_date
    return render_template(
        'super_admin/client/manage_clients.html',
        clients=clients,
        today=date.today(),
    )


# 👁️ View a single client (read-only details, edit gated in template by role)
@super_admin_bp.route('/clients/<int:client_id>', methods=['GET'], endpoint='view_client')
@super_admin_required
@login_required
def view_client(client_id: int):
    """
    Shows a single client's details. We enforce tenant isolation so a Super Admin
    from one company cannot view another company's records.
    """
    client = (
        Client.query
        .options(
            joinedload(Client.assigned_pm),
            joinedload(Client.assigned_fc),
            joinedload(Client.assigned_assistant),
        )
        .get_or_404(client_id)
    )

    # Tenant isolation
    if getattr(current_user, "company_id", None) and client.company_id != current_user.company_id:
        abort(404)

    return render_template('super_admin/client/view_client.html', client=client)
