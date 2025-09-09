from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import User, Client, Document  # Make sure your models are defined correctly
from flask_login import login_required
from app.extensions import db
from werkzeug.security import generate_password_hash
from datetime import datetime
from functools import wraps
from flask import current_app
from datetime import datetime, timedelta


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Decorator to check if the user is admin
def admin_required(func):
    from functools import wraps
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'Admin':
            return redirect(url_for('auth.login'))
        return func(*args, **kwargs)
    return decorated_view

@admin_bp.route('/dashboard', endpoint='dashboard')
@admin_required
def admin_dashboard():
    print("=== SESSION DEBUG ===", session.get('user'))
    current_app.logger.info(f"Session contents: {session}")

    clients = Client.query.all()
    managers = User.query.filter_by(role='Property Manager').all()
    work_orders = []

    pm_portfolios = {}
    total_portfolio_value = 0

    for pm in managers:
        assigned_clients = [c for c in clients if c.assigned_pm_id == pm.id]
        total_value = sum(c.contract_value or 0 for c in assigned_clients)
        total_portfolio_value += total_value
        pm_portfolios[pm.full_name] = {
            'total_value': total_value,
            'client_count': len(assigned_clients),
            'clients': assigned_clients
        }

    # ✅ Upcoming AGMs
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    three_months_out = today + timedelta(days=90)
    upcoming_agms = [c for c in clients if c.financial_year_end and today <= c.financial_year_end <= three_months_out]
    upcoming_agm_count = len(upcoming_agms)

    # ✅ Contractor Compliance Documents Count
    from app.models import ContractorComplianceDocument
    compliance_docs = ContractorComplianceDocument.query.count()

    return render_template(
        'admin/admin_dashboard.html',
        clients=clients,
        work_orders=work_orders,
        managers=managers,
        pm_portfolios=pm_portfolios,
        total_portfolio_value=total_portfolio_value,
        upcoming_agm_count=upcoming_agm_count,
        compliance_docs=compliance_docs  # ✅ Added metric
    )

@admin_bp.route('/add-client', methods=['GET', 'POST'], endpoint='add_client')
@login_required
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
        return redirect(url_for('admin.manage_clients'))

    return render_template('admin/add_client.html')

@admin_bp.route('/admin/edit-client/<int:client_id>', methods=['GET', 'POST'], endpoint='edit_client')
@login_required
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

@admin_bp.route('/add-user', methods=['GET', 'POST'], endpoint='add_user')
@login_required
@admin_required
def add_user():
    management_companies = Client.query.all()
    contractor_companies = Contractor.query.all()

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('username')  # field name in form
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        pin = request.form.get('pin')
        is_active = bool(request.form.get('is_active'))

        # Conditional company assignment
        if role == 'Contractor':
            company_id = request.form.get('contractor_id')
        else:
            company_id = request.form.get('company_id')

        # Validate required fields
        if not all([full_name, email, password, confirm_password, role, pin, company_id]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.add_user'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('admin.add_user'))

        # Hash password
        hashed_password = generate_password_hash(password)

        # Create user
        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=hashed_password,
            role=role,
            company_id=company_id,
            pin=pin,
            is_active=is_active,
            created_at=datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()

        flash(f'{role} "{full_name}" created successfully.', 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template(
        'admin/add_user.html',
        management_companies=management_companies,
        contractor_companies=contractor_companies
    )

# Future Routes
@admin_bp.route('/clients')
@admin_required
def manage_clients():
    clients = Client.query.all()
    return render_template('admin/manage_clients.html', clients=clients)

@admin_bp.route('/users')
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/reports')
@admin_required
def reports():
    return render_template('admin/reports.html')

@admin_bp.route('/logs', endpoint='logs')
@login_required
@admin_required
def view_logs():
    logs = []  # Load from DB or file (we can expand this later)
    return render_template('admin/view_logs.html', logs=logs)

@admin_bp.route('/alerts')
@login_required
def alerts():
    # Temporary dummy alerts for testing
    dummy_alerts = [
        {
            'client': 'Sample Client 1',
            'title': 'Leaking Roof',
            'category': 'Maintenance',
            'priority': 'High',
            'status': 'Open',
            'date_created': '2025-05-26'
        }
    ]
    return render_template('admin/alerts.html', alerts=dummy_alerts)

@admin_bp.route('/alerts/<int:alert_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def review_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)

    if request.method == 'POST':
        alert.status = request.form['status']
        alert.category = request.form['category']
        alert.priority = request.form['priority']

        # Check for optional work order creation
        if 'create_work_order' in request.form:
            new_work_order = WorkOrder(
                title=f"Work Order for Alert #{alert.id}: {alert.title}",
                description=alert.description,
                status='Open',
                unit_id=alert.unit_id,
                client_id=alert.client_id,
                created_by='System',
                alert_id=alert.id
            )
            db.session.add(new_work_order)
            alert.status = 'Escalated to Work Order'

        db.session.commit()
        flash('Alert updated successfully.', 'success')
        return redirect(url_for('admin.alerts'))

    return render_template('admin/review_alert.html', alert=alert)

@admin_bp.route('/settings')
def admin_settings():
    return render_template('admin/settings.html')

@admin_bp.route('/upcoming-agms')
@admin_required
def upcoming_agms():
    from datetime import datetime, timedelta

    today = datetime.utcnow().date()
    one_month = today + timedelta(days=30)
    two_months = today + timedelta(days=60)
    three_months = today + timedelta(days=90)

    clients = Client.query.filter(Client.financial_year_end != None).all()

    def filter_agms(clients, start, end):
        return [c for c in clients if start < c.financial_year_end <= end and not c.agm_completed]

    agms_1_month = filter_agms(clients, today, one_month)
    agms_2_month = filter_agms(clients, one_month, two_months)
    agms_3_month = filter_agms(clients, two_months, three_months)

    completed_agms = [c for c in clients if c.agm_completed]

    return render_template(
        'admin/upcoming_agms.html',
        agms_1_month=agms_1_month,
        agms_2_month=agms_2_month,
        agms_3_month=agms_3_month,
        completed_agms=completed_agms
    )

@admin_bp.route('/mark-agm-completed/<int:client_id>', methods=['POST'])
@admin_required
def mark_agm_completed(client_id):
    client = Client.query.get_or_404(client_id)
    client.agm_completed = True
    db.session.commit()
    flash(f'AGM marked as completed for {client.name}.', 'success')
    return redirect(url_for('admin.upcoming_agms'))

from app.models import ContractorComplianceDocument

from datetime import date

@admin_bp.route('/compliance-documents', endpoint='compliance_documents')
@admin_required
def compliance_documents():
    documents = ContractorComplianceDocument.query.order_by(ContractorComplianceDocument.uploaded_at.desc()).all()
    current_date = date.today()
    return render_template(
        'admin/compliance_documents.html',
        documents=documents,
        user=session.get('user'),
        current_date=current_date
    )

@admin_bp.route('/upload-compliance-document', methods=['GET', 'POST'])
@admin_required
def upload_compliance_document():
    contractors = User.query.filter_by(role='Contractor').all()

    if request.method == 'POST':
        file = request.files['document']
        if file:
            filename = secure_filename(file.filename)
            save_path = os.path.join(current_app.root_path, 'static/uploads/compliance_docs', filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)

            doc = ContractorComplianceDocument(
                document_type=request.form['document_type'],
                contractor_id=request.form['contractor_id'],
                file_name=filename,
                file_path='uploads/compliance_docs/' + filename,
                expiry_date=datetime.strptime(request.form['expiry_date'], '%Y-%m-%d'),
                uploaded_at=datetime.utcnow(),
                reminder_sent=False,
                reminder_date=None,
                is_required_for_work_order='is_required' in request.form,
                uploaded_by_id=session.get('id')
            )
            db.session.add(doc)
            db.session.commit()
            flash('Compliance document uploaded successfully.', 'success')
            return redirect(url_for('admin.compliance_documents'))

    return render_template('admin/upload_compliance_document.html', contractors=contractors)

@admin_bp.route('/review-compliance-document/<int:doc_id>', methods=['GET', 'POST'])
@admin_required
def review_compliance_document(doc_id):
    document = ContractorComplianceDocument.query.get_or_404(doc_id)

    if request.method == 'POST':
        document.is_required_for_work_order = 'is_required' in request.form
        document.expiry_date = request.form.get('expiry_date')
        document.review_comment = request.form.get('review_comment')
        document.reviewed_by_id = session['user']['id']
        document.reviewed_at = datetime.utcnow()

        db.session.commit()
        flash('Document reviewed and updated successfully.', 'success')
        return redirect(url_for('admin.compliance_documents'))

    return render_template('admin/review_compliance_document.html', document=document)

@admin_bp.route('/toggle-reviewed/<int:doc_id>', methods=['POST'], endpoint='toggle_reviewed_document')
@admin_required
def toggle_reviewed_document(doc_id):
    doc = ContractorComplianceDocument.query.get_or_404(doc_id)
    doc.reviewed = request.form.get('reviewed') == '1'
    db.session.commit()
    flash('Review status updated.', 'info')
    return redirect(url_for('admin.compliance_documents'))

@admin_bp.route('/delete-compliance-document/<int:doc_id>')
@admin_required
def delete_compliance_document(doc_id):
    doc = ContractorComplianceDocument.query.get_or_404(doc_id)
    db.session.delete(doc)
    db.session.commit()
    flash('Document deleted successfully.', 'success')
    return redirect(url_for('admin.compliance_documents'))
