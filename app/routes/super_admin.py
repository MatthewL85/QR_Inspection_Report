# app/routes/super_admin.py
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import User, Client, Contractor, Alert, WorkOrder, ContractorComplianceDocument, Role
from datetime import datetime, timedelta, date
import os
from werkzeug.utils import secure_filename
from app.extensions import db
from app.utils.auth import super_admin_required

super_admin_bp = Blueprint('super_admin', __name__, url_prefix='/super-admin')

# 🔐 Decorator

def super_admin_required(view_func):
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.name != "Super Admin":
            flash("Access denied. Super Admins only.", "danger")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    decorated_view.__name__ = view_func.__name__
    return login_required(decorated_view)

# ✅ Dashboard
from flask import Blueprint, render_template, session
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.decorators import super_admin_required
from app.models.client.client import Client
from app.models.core.user import User
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.models.contractor.contractor_compliance_document import ContractorComplianceDocument
from app.models.client.agm import AGM

super_admin_bp = Blueprint('super_admin', __name__, template_folder='../../templates/super_admin')

@super_admin_bp.route('/dashboard', endpoint='dashboard')
@login_required
@super_admin_required
def dashboard():
    # Get current user’s company (to limit results to their agency only)
    company_id = current_user.company_id

    # Clients scoped to the current management company
    clients = Client.query.filter_by(company_id=company_id).all()

    # Property Managers under this agency
    managers = User.query.filter_by(company_id=company_id, role='Property Manager').all()

    # Contractors (under same agency or globally assigned depending on structure)
    contractors = User.query.filter_by(company_id=company_id, role='Contractor').all()

    # Total contract value (ensure each client has contract_value)
    total_portfolio_value = sum(client.contract_value or 0 for client in clients)

    # Upcoming AGMs
    upcoming_agms = AGM.query.filter(AGM.company_id == company_id, AGM.date >= func.now()).all()
    upcoming_agm_count = len(upcoming_agms)

    # Compliance docs for clients under this company
    compliance_docs = ComplianceDocument.query \
        .join(Client, Client.id == ComplianceDocument.client_id) \
        .filter(Client.company_id == company_id).count()

    return render_template('super_admin/dashboard.html',
                           clients=clients,
                           managers=managers,
                           contractors=contractors,
                           total_portfolio_value=total_portfolio_value,
                           upcoming_agm_count=upcoming_agm_count,
                           compliance_docs=compliance_docs)


# ✅ Clients
@super_admin_bp.route('/clients')
@super_admin_required
def manage_clients():
    clients = Client.query.all()
    return render_template('super_admin/manage_clients.html', clients=clients)

@super_admin_bp.route('/add-client', methods=['GET', 'POST'])
@super_admin_required
def add_client():
    if request.method == 'POST':
        form_data = request.form
        new_client = Client(
            name=form_data.get('name'),
            address=form_data.get('address'),
            postal_code=form_data.get('postal_code'),
            registration_number=form_data.get('registration_number'),
            vat_reg_number=form_data.get('vat_reg_number'),
            tax_number=form_data.get('tax_number'),
            year_of_construction=form_data.get('year_of_construction'),
            number_of_units=form_data.get('number_of_units'),
            client_type=form_data.get('client_type'),
            country=form_data.get('country'),
            region=form_data.get('region'),
            currency=form_data.get('currency'),
            timezone=form_data.get('timezone'),
            preferred_language=form_data.get('preferred_language'),
            ownership_type=form_data.get('ownership_type'),
            transfer_of_common_area=bool(form_data.get('transfer_of_common_area')),
            deed_of_covenants=form_data.get('deed_of_covenants'),
            data_protection_compliance=form_data.get('data_protection_compliance'),
            consent_to_communicate=bool(form_data.get('consent_to_communicate')),
            min_directors=form_data.get('min_directors'),
            max_directors=form_data.get('max_directors'),
            number_of_blocks=form_data.get('number_of_blocks'),
            block_names=form_data.get('block_names'),
            cores_per_block=form_data.get('cores_per_block'),
            apartments_per_block=form_data.get('apartments_per_block')
        )
        db.session.add(new_client)
        db.session.commit()
        flash('Client added successfully.', 'success')
        return redirect(url_for('super_admin.manage_clients'))
    return render_template('super_admin/add_client.html')

@super_admin_bp.route('/edit-client/<int:client_id>', methods=['GET', 'POST'])
@super_admin_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        form_data = request.form
        client.name = form_data.get('name')
        client.address = form_data.get('address')
        client.postal_code = form_data.get('postal_code')
        client.registration_number = form_data.get('registration_number')
        client.vat_reg_number = form_data.get('vat_reg_number')
        client.tax_number = form_data.get('tax_number')
        client.year_of_construction = form_data.get('year_of_construction')
        client.number_of_units = form_data.get('number_of_units')
        client.client_type = form_data.get('client_type')
        client.country = form_data.get('country')
        client.region = form_data.get('region')
        client.currency = form_data.get('currency')
        client.timezone = form_data.get('timezone')
        client.preferred_language = form_data.get('preferred_language')
        client.ownership_type = form_data.get('ownership_type')
        client.deed_of_covenants = form_data.get('deed_of_covenants')
        client.data_protection_compliance = form_data.get('data_protection_compliance')
        client.consent_to_communicate = bool(form_data.get('consent_to_communicate'))
        client.transfer_of_common_area = bool(form_data.get('transfer_of_common_area'))
        client.min_directors = form_data.get('min_directors')
        client.max_directors = form_data.get('max_directors')
        client.number_of_blocks = form_data.get('number_of_blocks')
        client.block_names = form_data.get('block_names')
        client.cores_per_block = form_data.get('cores_per_block')
        client.apartments_per_block = form_data.get('apartments_per_block')
        db.session.commit()
        flash('Client updated successfully.', 'success')
        return redirect(url_for('super_admin.manage_clients'))
    return render_template('super_admin/edit_client.html', client=client)

@super_admin_bp.route('/users', endpoint='manage_users')
@super_admin_required
def manage_users():
    users = User.query.all()
    return render_template('super_admin/manage_users.html', users=users)

@super_admin_bp.route('/add-user', methods=['GET', 'POST'], endpoint='add_user')
@super_admin_required
def add_user():
    roles = Role.query.all()
    management_companies = Client.query.all()
    contractor_companies = Contractor.query.all()

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('username')  # Field is still named username in form
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role_id = request.form.get('role_id')
        pin = request.form.get('pin')
        is_active = bool(request.form.get('is_active'))

        # Company association
        company_id = request.form.get('contractor_id') if role_id == '5' else request.form.get('company_id')

        if not all([full_name, email, password, confirm_password, role_id, pin, company_id]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('super_admin.add_user'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('super_admin.add_user'))

        hashed_password = generate_password_hash(password)

        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=hashed_password,
            role_id=role_id,
            company_id=company_id,
            pin=pin,
            is_active=is_active,
            created_at=datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()

        flash('User created successfully.', 'success')
        return redirect(url_for('super_admin.manage_users'))

    return render_template(
        'super_admin/add_user.html',
        roles=roles,
        management_companies=management_companies,
        contractor_companies=contractor_companies
    )
@super_admin_bp.route('/edit-user/<int:user_id>', methods=['GET', 'POST'], endpoint='edit_user')
@super_admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    management_companies = Client.query.all()
    contractor_companies = Contractor.query.all()

    if request.method == 'POST':
        from app.utils.audit import log_change

        form = request.form
        new_full_name = form.get('full_name')
        new_email = form.get('email')
        new_role_id = form.get('role_id')
        new_pin = form.get('pin')
        new_is_active = bool(form.get('is_active'))
        company_id = form.get('contractor_id') if new_role_id == '5' else form.get('company_id')

        # Log & apply changes
        if user.full_name != new_full_name:
            log_change(user, 'full_name', user.full_name, new_full_name)
            user.full_name = new_full_name

        if user.email != new_email:
            log_change(user, 'email', user.email, new_email)
            user.email = new_email

        if str(user.role_id) != str(new_role_id):
            log_change(user, 'role_id', user.role_id, new_role_id)
            user.role_id = new_role_id

        if user.pin != new_pin:
            log_change(user, 'pin', user.pin, new_pin)
            user.pin = new_pin

        if str(user.company_id) != str(company_id):
            log_change(user, 'company_id', user.company_id, company_id)
            user.company_id = company_id

        if user.is_active != new_is_active:
            log_change(user, 'is_active', user.is_active, new_is_active)
            user.is_active = new_is_active

        # Optional password reset
        new_password = form.get('new_password')
        confirm_password = form.get('confirm_password')
        if new_password:
            if new_password == confirm_password:
                user.password_hash = generate_password_hash(new_password)
                log_change(user, 'password_hash', '[old]', '[new]')
            else:
                flash('Passwords do not match.', 'danger')
                return redirect(url_for('super_admin.edit_user', user_id=user.id))

        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('super_admin.manage_users'))

    return render_template(
        'super_admin/edit_user.html',
        user=user,
        management_companies=management_companies,
        contractor_companies=contractor_companies
    )
@super_admin_bp.route('/alerts', endpoint='alerts')
@super_admin_required
def alerts():
    alerts = Alert.query.order_by(Alert.timestamp.desc()).all()
    return render_template('super_admin/alerts.html', alerts=alerts)

@super_admin_bp.route('/alerts/<int:alert_id>', methods=['GET', 'POST'], endpoint='review_alert')
@super_admin_required
def review_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)

    if request.method == 'POST':
        alert.status = request.form.get('status')
        alert.category = request.form.get('category')
        alert.priority = request.form.get('priority')

        # Optional: escalate to work order
        if 'create_work_order' in request.form and request.form.get('create_work_order') == 'on':
            new_work_order = WorkOrder(
                title=f"Work Order for Alert #{alert.id}: {alert.title}",
                description=alert.description,
                status='Open',
                unit_id=alert.unit_id,
                client_id=alert.client_id,
                created_by=current_user.full_name,
                alert_id=alert.id,
                date_created=datetime.utcnow()
            )
            db.session.add(new_work_order)
            alert.status = 'Escalated to Work Order'

        db.session.commit()
        flash('Alert updated successfully.', 'success')
        return redirect(url_for('super_admin.alerts'))

    return render_template('super_admin/review_alert.html', alert=alert)
