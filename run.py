from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash, abort, make_response
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from dateutil.relativedelta import relativedelta
from weasyprint import HTML
from app.models import db, Client, CapexRequest  # SQLAlchemy db instance and all models
from app.helpers.auth_helpers import create_user, authenticate_user, user_exists
from werkzeug.utils import secure_filename
from sqlalchemy import extract
from app.routes.capex import capex_bp
from app import create_app



import os
import qrcode
import json
from datetime import datetime
from collections import defaultdict
import uuid
import re

# Initialize the Flask app and DB
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///logixpm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'  # 🔥 Set secret key immediately

app.register_blueprint(capex_bp)

db.init_app(app)
migrate = Migrate(app, db)
app = create_app()

from flask.cli import with_appcontext
import click

@click.command(name='create_db')
@with_appcontext
def create_db():
    db.create_all()
    click.echo("Database created.")

# Load company settings
SETTINGS_FILE = 'static/settings.json'

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}


# Load settings once at startup
app_settings = load_settings()


def validate_pin_strength(pin):
    """
    Ensure PIN meets minimum security requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(pin) < 8:
        return False
    if not re.search(r'[A-Z]', pin):
        return False
    if not re.search(r'[a-z]', pin):
        return False
    if not re.search(r'[0-9]', pin):
        return False
    if not re.search(r'[\W_]', pin):  # non-word character (symbol)
        return False
    return True

@app.context_processor
def inject_settings():
    return dict(settings=app_settings)

# Other global constants
DATA_FILE = 'equipment.csv'
LOG_CSV = 'inspection_logs.csv'
QR_FOLDER = 'static/qrcodes'
USER_CSV = 'users.csv'

os.makedirs(QR_FOLDER, exist_ok=True)

# Custom filter to format timestamp
@app.template_filter('format_datetime')
def format_datetime_filter(value):
    """Format ISO datetime to DD-MM-YYYY HH:MM:SS"""
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime('%d-%m-%Y %H:%M:%S')
    except Exception:
        return value  # fallback if invalid


if not os.path.exists(LOG_CSV):
    with open(LOG_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'equipment_id', 'name', 'client', 'inspector_pin', 'clean', 'damage', 'functional', 'notes'])
    print("Created empty inspection_logs.csv with headers.")


def load_equipment():
    equipment = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                equipment.append(row)
    return equipment

def get_equipment_by_id(equipment_id):
    for eq in load_equipment():
        if eq['id'] == equipment_id:
            if 'created_by' not in eq:
                eq['created_by'] = 'Unknown'
            return eq
    return None

def save_inspection_log(data):
    file_exists = os.path.exists(LOG_CSV)
    with open(LOG_CSV, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'equipment_id', 'name', 'client', 'inspector_pin', 'clean', 'damage', 'functional', 'notes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

    print("Inspection saved for ID:", data['equipment_id'])
    print("Log saved to:", os.path.abspath(LOG_CSV))

@app.route('/')
def index():
    return redirect(url_for('show_dashboard'))

@app.route('/dashboard')
def show_dashboard():
    if 'user' not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('login'))

    role = session['user'].get('role')

    if role == 'Admin':
        return redirect(url_for('admin.dashboard')

)
    elif role == 'Property Manager':
        return redirect(url_for('property_manager_dashboard'))
    elif role == 'Contractor':
        return redirect(url_for('contractor_dashboard'))
    else:
        flash("Unknown role. Please contact your administrator.", "danger")
        return redirect(url_for('login'))

    return render_template('dashboard.html', equipment=filtered_equipment, user=user)

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    client_names = []

    # Load client names from clients.csv
    if os.path.exists('clients.csv'):
        with open('clients.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                client_name = row.get('client_name')
                if client_name:
                    client_names.append(client_name)

    if request.method == 'POST':
        client = request.form['client']
        eq_id = request.form['id']
        name = request.form['name']
        location = request.form['location']
        model = request.form['model']
        age = request.form['age']
        last_inspection = request.form['last_inspection']
        pin = request.form['pin']

        # Save new equipment to equipment.csv
        file_exists = os.path.isfile(DATA_FILE)
        with open(DATA_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['id', 'client', 'name', 'location', 'model', 'age', 'last_inspection', 'pin', 'created_by'])

            created_by = session['user'].get('full_name') or session['user'].get('name_or_company') or session['user']['username']

            writer.writerow([eq_id, client, name, location, model, age, last_inspection, pin, created_by])

            print(f"✅ Equipment saved: {eq_id} for client {client}")

        # Generate QR Code linking to the inspection page
        qr_url = url_for('enter_pin', equipment_id=eq_id, _external=True)
        img = qrcode.make(qr_url)
        os.makedirs(QR_FOLDER, exist_ok=True)
        img.save(os.path.join(QR_FOLDER, f"{eq_id}.png"))

        flash("Equipment created and QR code generated successfully!", "success")
        if session['user']['role'] == 'Admin':
            return redirect(url_for('admin_management_dashboard'))
        else:
            return redirect(url_for('property_manager_dashboard'))

    # GET request
    return render_template('generate.html', client_names=sorted(client_names))


@app.route('/inspect/<equipment_id>', methods=['GET', 'POST'])
def inspect(equipment_id):
    equipment = get_equipment_by_id(equipment_id)
    if not equipment:
        return 'Equipment not found.', 404

    if request.method == 'POST':
        entered_pin = request.form['pin']
        stored_pin = equipment.get('pin', '').strip()

        if entered_pin == stored_pin:
            # Save inspection data
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'equipment_id': equipment_id,
                'name': equipment.get('name', ''),
                'client': equipment.get('client', ''),
                'inspector_pin': entered_pin,
                'clean': request.form['clean'],
                'damage': request.form['damage'],
                'functional': request.form['functional'],
                'notes': request.form['notes']
            }
            save_inspection_log(log_data)
            return render_template('inspection_success.html', equipment=equipment)
        else:
            return render_template('inspect.html', equipment=equipment, error='Invalid PIN')

    return render_template('inspect.html', equipment=equipment)

@app.route('/logs')
def view_logs():
    logs = []
    if os.path.exists(LOG_CSV):
        with open(LOG_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                logs.append(row)
    return render_template('logs.html', logs=logs)

@app.route('/download-logs')
def download_logs():
    return send_file(LOG_CSV, as_attachment=True)

@app.route('/qrcodes')
def view_qrcodes():
    equipment = load_equipment()
    return render_template('qrcodes.html', equipment=equipment)

@app.route('/enter-pin/<equipment_id>', methods=['GET', 'POST'])
def enter_pin(equipment_id):
    if request.method == 'POST':
        pin_entered = request.form['pin']
        role_info = get_user_by_pin(pin_entered)

        if role_info:
            role = role_info['role']
            name_or_company = role_info['name_or_company']

            if role == 'Property Manager':
                return redirect(url_for('property_manager_interface', equipment_id=equipment_id, pm_name=name_or_company))
            elif role == 'Contractor':
                return redirect(url_for('contractor_interface', equipment_id=equipment_id, client=name_or_company))
            else:
                return "Unknown role in users.csv", 400
        else:
            return render_template('enter_pin.html', error="Invalid PIN", equipment_id=equipment_id)

    return render_template('enter_pin.html', equipment_id=equipment_id)

def get_user_by_pin(pin):
    if os.path.exists('users.csv'):
        with open('users.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['pin'] == pin:
                    return {'role': row['role'], 'name_or_company': row['name_or_company']}
    return None

@app.route('/property-manager/<equipment_id>', methods=['GET', 'POST'])
def property_manager_interface(equipment_id):
    pm_name = request.args.get('pm_name')
    equipment = get_equipment_by_id(equipment_id)

    if not equipment:
        return 'Equipment not found.', 404

    if request.method == 'POST':
        clean = request.form['clean']
        damage = request.form['damage']
        functional = request.form['functional']
        notes = request.form['notes']

        media = request.files.get('media')
        media_filename = ''
        if media and media.filename:
            media_folder = os.path.join('static', 'uploads')
            os.makedirs(media_folder, exist_ok=True)
            media_filename = f"{equipment_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{media.filename}"
            media.save(os.path.join(media_folder, media_filename))

        log_data = {
            'timestamp': datetime.now().isoformat(),
            'equipment_id': equipment_id,
            'name': equipment.get('name', ''),
            'client': equipment.get('client', ''),
            'inspector_pin': f"Property Manager: {pm_name}",
            'clean': clean,
            'damage': damage,
            'functional': functional,
            'notes': notes + (f"\nMedia: {media_filename}" if media_filename else "")
        }
        save_inspection_log(log_data)

        return render_template('inspection_success.html', equipment=equipment, media_filename=media_filename)

    return render_template('pm_interface.html', equipment=equipment, pm_name=pm_name)

@app.route('/contractor/<equipment_id>', methods=['GET', 'POST'])
def contractor_interface(equipment_id):
    client = request.args.get('client')
    equipment = get_equipment_by_id(equipment_id)

    if not equipment:
        return 'Equipment not found.', 404

    current_next_date = get_next_maintenance_date(equipment_id)

    allow_edit = True
    if current_next_date:
        try:
            next_dt = datetime.strptime(current_next_date, '%Y-%m-%d')
            today = datetime.today()
            delta = (next_dt - today).days
            allow_edit = delta <= 7  # Editable only if within a week
        except ValueError:
            pass  # Invalid format fallback: allow edit

    if request.method == 'POST':
        visit_date = request.form['visit_date']
        visit_type = request.form['visit_type']
        next_maintenance = request.form['next_maintenance']
        notes = request.form['notes']

        # Save new next maintenance date if allowed
        if allow_edit:
            save_next_maintenance_date(equipment_id, next_maintenance)

        # Handle media upload
        media = request.files.get('media')
        media_filename = ''
        if media and media.filename:
            media_folder = os.path.join('static', 'uploads')
            os.makedirs(media_folder, exist_ok=True)
            media_filename = f"{equipment_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{media.filename}"
            media.save(os.path.join(media_folder, media_filename))
            notes += f"\nMedia: {media_filename}"

        log_data = {
            'timestamp': datetime.now().isoformat(),
            'equipment_id': equipment_id,
            'name': equipment.get('name', ''),
            'client': client,
            'inspector_pin': f"Contractor: {client}",
            'clean': f"Visit Type: {visit_type}",
            'damage': f"Visit Date: {visit_date}",
            'functional': f"Next Maintenance: {next_maintenance}",
            'notes': notes
        }
        save_inspection_log(log_data)

        return render_template('inspection_success.html', equipment=equipment, media_filename=media_filename)

    return render_template('contractor_interface.html', equipment=equipment, company=client, next_maintenance=current_next_date, allow_edit=allow_edit)

def get_next_maintenance_date(equipment_id):
    log_entries = []
    if os.path.exists(LOG_CSV):
        with open(LOG_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['equipment_id'] == equipment_id and row['functional'].startswith("Next Maintenance:"):
                    log_entries.append(row)

    # Return the latest next maintenance date (if available)
    if log_entries:
        latest_entry = max(log_entries, key=lambda x: x['timestamp'])
        return latest_entry['functional'].replace("Next Maintenance:", "").strip()

    return None

def save_next_maintenance_date(equipment_id, next_date):
    # This function logs the new date in a structured way so it can be retrieved later
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'equipment_id': equipment_id,
        'name': '',  # optional if you want to leave blank
        'client': '',
        'inspector_pin': 'System Auto-Update',
        'clean': '',
        'damage': '',
        'functional': f"Next Maintenance: {next_date}",
        'notes': '[Auto-update from Contractor Interface]'
    }
    save_inspection_log(log_data)

@app.route('/upload/<equipment_id>', methods=['POST'])
def upload_media(equipment_id):
    uploads = []
    for field in ['photo', 'video']:
        file = request.files.get(field)
        if file and file.filename:
            filename = f"{equipment_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            file_path = os.path.join('static', 'uploads', filename)
            file.save(file_path)
            uploads.append(file_path)

    if not uploads:
        return "No files uploaded", 400

    print(f"Uploaded files: {uploads}")
    return redirect(url_for('property_manager_interface', equipment_id=equipment_id, pm_name=request.args.get('pm_name')))

@app.route('/report/client/<client_name>')
def report_by_client(client_name):
    logs = []
    if os.path.exists(LOG_CSV):
        with open(LOG_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['client'].strip().lower() == client_name.strip().lower():
                    logs.append(row)

    equipment_ids = set(row['equipment_id'] for row in logs)
    equipment_list = [get_equipment_by_id(eid) for eid in equipment_ids if get_equipment_by_id(eid)]

    return render_template('report_client.html', client=client_name, logs=logs, equipment=equipment_list)

@app.route('/report/equipment/<equipment_id>')
def report_by_equipment(equipment_id):
    logs = []
    if os.path.exists(LOG_CSV):
        with open(LOG_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['equipment_id'] == equipment_id:
                    logs.append(row)

    equipment = get_equipment_by_id(equipment_id)
    return render_template('report_equipment.html', equipment=equipment, logs=logs)


  
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/register')
def legacy_register_redirect():
    flash("Please begin by selecting your company type.", "info")
    return redirect(url_for('onboard'))

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user' not in session or session['user']['role'] != 'Admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    company = session['user'].get('company', '').lower()

    # Simple keyword check to determine company type
    if any(keyword in company for keyword in ['fire', 'tech', 'hvac', 'plumb', 'contractor', 'lighting']):
        return render_template('admin_contractor_dashboard.html')
    else:
        return render_template('admin_management_dashboard.html')

@app.route('/admin-management-dashboard')
def admin_management_dashboard():
    if 'user' not in session or session['user']['role'] != 'Admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    missed_tasks = get_missed_tasks_for_admin()
    missed_count = len(missed_tasks)

    upcoming = get_upcoming_maintenance()
    this_month = datetime.today().month
    planner_this_month = [m for m in upcoming if m['next_date'].month == this_month]

    print("📅 ALL upcoming:", upcoming)
    print("📅 Filtered planner_this_month:", planner_this_month)

    return render_template(
        'admin_management_dashboard.html',
        missed_tasks=missed_tasks,
        missed_count=missed_count,
        planner_this_month=planner_this_month  # ✅ FIXED here
    )

@app.route('/admin-contractor-dashboard')
def admin_contractor_dashboard():
    if 'user' not in session or session['user']['role'] != 'Admin Contractor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))
    return render_template('admin_contractor_dashboard.html')


@app.route('/admin/clients')
def manage_clients():
    if 'user' not in session or session['user']['role'] != 'Admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    clients = []
    if os.path.exists('clients.csv'):
        with open('clients.csv', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    contacts = json.loads(row['contacts'].replace('""', '"'))
                except json.JSONDecodeError:
                    contacts = []

                client = {
                    'id': row['id'],
                    'name': row['client_name'],
                    'address': row['address'],
                    'contacts': contacts,
                    'assigned_manager_email': row.get('assigned_manager_email', ''),
                    'company': row.get('company', ''),
                    'client_code': row.get('client_code', '')  # ✅ Now also load client_code
                }
                clients.append(client)

    # Load assignments (who is assigned to manage which client)
    assignments = {}
    if os.path.exists('assignments.csv'):
        with open('assignments.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assignments[row['client_name']] = row['manager_email']

    # Attach Property Manager email to each client
    for client in clients:
        client['assigned_pm'] = assignments.get(client['name'], '—')

    return render_template('manage_clients.html', clients=clients)


@app.route('/admin/reports')
def admin_reports():
    if 'user' not in session or session['user']['role'] != 'Admin':
        return abort(403)
    return render_template('admin_reports.html')


@app.route('/admin/alerts')
def admin_alerts():
    if 'user' not in session or session['user']['role'] != 'Admin':
        return abort(403)
    
    missed_alerts = get_missed_inspections()
    return render_template('admin_alerts.html', missed_alerts=missed_alerts)


@app.route('/property-manager-dashboard')
def property_manager_dashboard():
    if session['user']['role'] != 'Property Manager':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    username = session['user']['username']
    assigned_clients = get_clients_for_manager(username)
    equipment = [eq for eq in load_equipment() if eq.get('client') in assigned_clients]

    missed_tasks = get_missed_tasks_for_pm(username)

    return render_template(
        'property_manager_dashboard.html',
        equipment=equipment,
        missed_tasks=missed_tasks
    )

@app.route('/contractor-dashboard')
def contractor_dashboard():
    if 'user' not in session or session['user']['role'] != 'Contractor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    contractor_name = session['user']['company']
    logs = []

    if os.path.exists(LOG_CSV):
        with open(LOG_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if f"Contractor: {contractor_name}" in row['inspector_pin']:
                    logs.append(row)

    return render_template('contractor_dashboard.html', company=contractor_name, logs=logs)

def get_clients_for_manager(manager_email):
    clients = []
    if os.path.exists('assignments.csv'):
        with open('assignments.csv', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['manager_email'].strip().lower() == manager_email.strip().lower():
                    clients.append(row['client_name'].strip())
    return clients

def get_missed_inspections():
    missed_alerts = []
    today = datetime.today().date()

    if os.path.exists(LOG_CSV):
        with open(LOG_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['functional'].startswith("Next Maintenance:"):
                    try:
                        next_date = datetime.strptime(row['functional'].replace("Next Maintenance:", "").strip(), '%Y-%m-%d').date()
                        if next_date < today:
                            missed_alerts.append(row)
                    except ValueError:
                        continue  # Skip badly formatted dates
    return missed_alerts

def get_missed_inspections_for_pm(pm_email):
    today = datetime.today().date()
    missed_alerts = []

    assigned_clients = get_clients_for_manager(pm_email)

    if os.path.exists(LOG_CSV):
        with open(LOG_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['client'] not in assigned_clients:
                    continue
                if row['functional'].startswith("Next Maintenance:"):
                    try:
                        next_date = datetime.strptime(
                            row['functional'].replace("Next Maintenance:", "").strip(), "%Y-%m-%d"
                        ).date()
                        if next_date < today:
                            missed_alerts.append(row)
                    except ValueError:
                        continue  # skip bad formats
    return missed_alerts

def get_upcoming_maintenance():
    upcoming = []
    today = datetime.today().date()
    seen_equipment = set()

    if os.path.exists(LOG_CSV):
        with open(LOG_CSV, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                eq_id = row['equipment_id']
                if row['functional'].startswith("Next Maintenance:") and eq_id not in seen_equipment:
                    try:
                        next_date = datetime.strptime(
                            row['functional'].replace("Next Maintenance:", "").strip(), '%Y-%m-%d'
                        ).date()
                        if next_date >= today:
                            upcoming.append({
                                'equipment_id': eq_id,
                                'client': row['client'],
                                'name': row['name'],
                                'next_date': next_date,
                                'inspector': row['inspector_pin'],
                            })
                            seen_equipment.add(eq_id)
                    except ValueError:
                        continue

    return sorted(upcoming, key=lambda x: x['next_date'])

@app.route('/pm/alerts')
def pm_alerts():
    if 'user' not in session or session['user']['role'] != 'Property Manager':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    pm_email = session['user']['username']
    missed_alerts = get_missed_inspections_for_pm(pm_email)

    return render_template('pm_alerts.html', missed_alerts=missed_alerts)

@app.route('/admin/maintenance-planner')
def admin_maintenance_planner():
    if 'user' not in session or session['user']['role'] != 'Admin':
        return abort(403)
    
    # Load PPM tasks
    upcoming_maintenance = get_upcoming_maintenance()

    # Load manual tasks
    manual_tasks = []
    if os.path.exists('manual_tasks.csv'):
        with open('manual_tasks.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    manual_tasks.append({
                        'title': row['title'],
                        'client': row['client'],
                        'date': datetime.strptime(row['date'], '%Y-%m-%d').date(),
                        'frequency': row['frequency'],
                        'type': 'manual',
                        'completed': row.get('completed', 'no')
                    })
                except ValueError:
                    continue  # skip bad dates

    return render_template(
        'admin_maintenance_planner.html',
        maintenance=upcoming_maintenance,
        manual_tasks=manual_tasks
    )

@app.route('/pm/maintenance-planner')
def property_manager_maintenance_planner():
    if 'user' not in session or session['user']['role'] != 'Property Manager':
        return abort(403)

    username = session['user']['username']
    maintenance = get_upcoming_maintenance_for_pm(username)

    # Load manual tasks
    manual_tasks = []
    if os.path.exists('manual_tasks.csv'):
        with open('manual_tasks.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                user_name = session['user'].get('full_name') or session['user']['name_or_company'] or username
                if row['created_by'] == user_name or row['created_by'] == username:
                    try:
                        manual_tasks.append({
                            'title': row['title'],
                            'client': row['client'],
                            'date': datetime.strptime(row['date'], '%Y-%m-%d').date(),
                            'frequency': row['frequency'],
                            'type': 'manual',
                            'completed': row.get('completed', 'no')
                        })
                    except ValueError:
                        continue

    return render_template(
        'pm_maintenance_planner.html',
        maintenance=maintenance,
        manual_tasks=manual_tasks
    )

@app.route('/onboard')
def onboard():
    omc_names = []
    management_names = []
    contractor_names = []

    clients = Client.query.all()
    for row in clients:
        client_type = (row.registration_number or '').lower()
        name = row.name.replace(' ', '-')

        if client_type == 'omc':
            omc_names.append(name)
        elif client_type == 'management':
            management_names.append(name)
        elif client_type == 'contractor':
            contractor_names.append(name)

    return render_template(
        'onboard.html',
        omc_names=omc_names,
        management_names=management_names,
        contractor_names=contractor_names
    )
    
@app.route('/register-company/<company_type>', methods=['GET', 'POST'])
def register_company(company_type):
    company_name = request.args.get('company_name', '')  # Optional pre-fill

    if request.method == 'POST':
        company_name = request.form['company_name'].strip()
        admin_email = request.form['admin_email'].strip().lower()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register_company.html', company_type=company_type, company_name=company_name)

        if user_exists(admin_email):
            flash("An account with that email already exists.", "warning")
            return render_template('register_company.html', company_type=company_type, company_name=company_name)

        # ✅ Check if the company already exists
        existing_client = Client.query.filter_by(name=company_name).first()
        if existing_client:
            flash(f"A company named '{company_name}' already exists.", "warning")
            return render_template('register_company.html', company_type=company_type, company_name=company_name)

        # ✅ Create the company in the database
        new_client = Client(
            name=company_name,
            address='',  # Can be collected later
            registration_number='',
            year_of_construction='',
            number_of_units=0,
            client_type=company_type.lower()
        )
        db.session.add(new_client)
        db.session.commit()

        # ✅ Assign admin role based on company_type
        if company_type.lower() == 'contractor':
            role = 'Admin Contractor'
        elif company_type.lower() == 'omc':
            role = 'Director'
        else:
            role = 'Admin'

        try:
            create_user(
                email=admin_email,
                password=password,
                role=role,
                company_id=new_client.id,
                full_name=f"{role} for {company_name}"
            )
        except Exception as e:
            flash(f"An error occurred while creating the user: {e}", "danger")
            return render_template('register_company.html', company_type=company_type, company_name=company_name)

        flash(f"{company_type.capitalize()} '{company_name}' registered successfully! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register_company.html', company_type=company_type, company_name=company_name)


@app.route('/admin/users')
def manage_users():
    if 'user' not in session or session['user']['role'] not in ['Admin', 'Admin Contractor']:
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    company = session['user']['company'].strip().lower()
    role = session['user']['role']
    users = []

    if os.path.exists(USER_CSV):
        with open(USER_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                same_company = row['company'].strip().lower() == company
                is_contractor_only = row['role'].strip() == 'Contractor'

                if role == 'Admin' and same_company:
                    users.append(row)
                elif role == 'Admin Contractor' and same_company and is_contractor_only:
                    users.append(row)

    return render_template('manage_users.html', users=users)

def load_all_users():
    users = []
    if os.path.exists('users.csv'):
        with open('users.csv', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append(row)
    return users

@app.route('/admin/delete-user/<username>', methods=['GET'])
def delete_user(username):
    if 'user' not in session or session['user']['role'] not in ['Admin', 'Admin Contractor']:
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    users = []
    user_deleted = False
    current_company = session['user']['company'].strip().lower()
    current_role = session['user']['role']

    if os.path.exists(USER_CSV):
        with open(USER_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['username'] == username:
                    if row['company'].strip().lower() == current_company:
                        if current_role == 'Admin' or (current_role == 'Admin Contractor' and row['role'] == 'Contractor'):
                            user_deleted = True
                            continue  # Skip this user (delete)
                users.append(row)

        if user_deleted:
            with open(USER_CSV, 'w', newline='') as csvfile:
                fieldnames = ['username', 'password', 'role', 'company', 'pin', 'name_or_company']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(users)

            flash(f"User '{username}' deleted successfully.", "success")
        else:
            flash("You do not have permission to delete this user.", "danger")

    return redirect(url_for('manage_users'))

@app.route('/admin/users/edit/<email>', methods=['GET', 'POST'])
def edit_user(email):
    if 'user' not in session or session['user']['role'] not in ['Admin', 'Admin Contractor']:
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    users = load_all_users()
    user_to_edit = None
    for u in users:
        if u['username'] == email:
            user_to_edit = u
            break

    if not user_to_edit:
        flash("User not found.", "danger")
        return redirect(url_for('manage_users'))

    # Restrict Contractor Admin from editing non-contractor users
    if session['user']['role'] == 'Admin Contractor':
        if user_to_edit['role'] != 'Contractor' or user_to_edit['company'].lower() != session['user']['company'].lower():
            flash("You are not allowed to edit this user.", "danger")
            return redirect(url_for('manage_users'))

    if request.method == 'POST':
        new_role = request.form['role']
        new_company = request.form['company']
        new_pin = request.form.get('pin', '').strip()

        # Restrict Contractor Admin from changing role to non-contractor
        if session['user']['role'] == 'Admin Contractor' and new_role != 'Contractor':
            flash("You can only assign Contractor role.", "danger")
            return redirect(url_for('manage_users'))

        # Validate PIN if provided
        if new_pin:
            import re
            pin_pattern = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[\W_]).{8,}$'
            if not re.match(pin_pattern, new_pin):
                flash('PIN must be at least 8 characters long, including a number, a symbol, a lowercase and uppercase letter.', 'danger')
                return redirect(url_for('edit_user', email=email))

        # Update the user
        for u in users:
            if u['username'] == email:
                u['role'] = new_role
                u['company'] = new_company
                if new_pin:
                    u['pin'] = new_pin
                break

        with open(USER_CSV, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['username', 'password', 'role', 'company', 'pin', 'name_or_company']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(users)

        flash("User updated successfully.", "success")
        return redirect(url_for('manage_users'))

    return render_template('edit_user.html', user=user_to_edit)


@app.route('/admin/add-user', methods=['GET', 'POST'])
def add_user():
    if 'user' not in session or session['user']['role'] not in ['Admin', 'Admin Contractor']:
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    # ✅ Load allowed roles correctly
    if session['user']['role'] == 'Admin':
        allowed_roles = ['Admin', 'Property Manager']
    elif session['user']['role'] == 'Admin Contractor':
        allowed_roles = ['Contractor']

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        confirm_password = request.form['confirm_password'].strip()
        role = request.form['role'].strip()
        pin = request.form['pin'].strip()
        name_or_company = request.form['name_or_company'].strip()
        company = session['user']['company']  # ✅ Also needed!

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('add_user.html', allowed_roles=allowed_roles)

        if not validate_pin_strength(pin):
            flash("PIN does not meet security requirements. Must be at least 8 characters with uppercase, lowercase, number, and symbol.", "danger")
            return render_template('add_user.html', allowed_roles=allowed_roles)

        # ✅ Now it's safe to continue creating the user
        create_user(username=username, password=password, role=role, pin=pin, company=company, name_or_company=name_or_company)
        flash("User added successfully!", "success")
        return redirect(url_for('manage_users'))

    return render_template('add_user.html', allowed_roles=allowed_roles)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip()
        if not user_exists(email):
            flash("No account found with that email.", "danger")
        else:
            flash("If your email is registered, a password reset link will be sent. (Feature coming soon!)", "info")
            # Later: generate and send email with reset token

    return render_template('forgot_password.html')

def load_clients():
    clients = []
    if os.path.exists('clients.csv'):
        with open('clients.csv', 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Parse contacts field
                try:
                    contacts = json.loads(row.get('contacts', '[]').replace('""', '"'))
                except json.JSONDecodeError:
                    contacts = []

                client = {
                    'id': row.get('id', ''),  # Keep using client ID (UUID or custom)
                    'name': row.get('client_name', ''),
                    'address': row.get('address', ''),
                    'contacts': contacts,
                    'assigned_pm': row.get('assigned_manager_email', '').strip(),
                    'company': row.get('company', ''),
                    'client_code': row.get('client_code', '')  # <-- ADD this so it loads properly
                }
                clients.append(client)
    return clients

def save_clients(clients):
    """Save the list of clients to clients.csv."""
    fieldnames = ['id', 'client_name', 'address', 'contacts', 'assigned_manager_email', 'company', 'client_code']

    with open('clients.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for client in clients:
            writer.writerow({
                'id': client.get('id', ''),
                'client_name': client.get('name', ''),
                'address': client.get('address', ''),
                'contacts': json.dumps(client.get('contacts', [])),
                'assigned_manager_email': client.get('assigned_pm', ''),  # <-- FIX HERE
                'company': client.get('company', ''),
                'client_code': client.get('client_code', '')
            })

@app.route('/report/<client_id>')
def report_client(client_id):
    clients = load_clients()
    client = next((c for c in clients if c['id'] == client_id), None)
    if not client:
        return "Client not found", 404
    return render_template('report_client.html', client=client)

@app.route('/add-client', methods=['GET', 'POST'])
def add_client():
    if 'user' not in session or session['user']['role'] != 'Admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        clients = load_clients()

        name = request.form['name'].strip()
        address = request.form['address'].strip()

        # Contacts
        contacts = []
        for i in range(1, 10):
            contact_name = request.form.get(f'contact{i}_name', '').strip()
            contact_email = request.form.get(f'contact{i}_email', '').strip()
            contact_phone = request.form.get(f'contact{i}_phone', '').strip()
            if contact_name:
                contacts.append({
                    'name': contact_name,
                    'email': contact_email,
                    'phone': contact_phone
                })

        # 🆕 Generate Client ID (UUID) and Client Code (Initials)
        new_id = str(uuid.uuid4())  # You must `import uuid` at the top!
        client_code = ''.join([word[0] for word in name.upper().split() if word.isalnum()])[:2]  # E.g., "Rathborne Village" ➔ "RV"

        new_client = {
            'id': new_id,
            'name': name,
            'address': address,
            'contacts': contacts,
            'assigned_pm': '',
            'company': session['user']['company'],  # Match current Admin's company
            'client_code': client_code
        }

        clients.append(new_client)
        save_clients(clients)

        flash(f"Client '{name}' added successfully!", "success")
        return redirect(url_for('manage_clients'))

    return render_template('add_client.html')


@app.route('/edit-client/<client_id>', methods=['GET', 'POST'])
def edit_client(client_id):
    if 'user' not in session or session['user']['role'] != 'Admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    clients = load_clients()
    client = next((c for c in clients if c['id'] == client_id), None)

    if not client:
        flash("Client not found.", "danger")
        return redirect(url_for('manage_clients'))

    if request.method == 'POST':
        client['name'] = request.form['name'].strip()
        client['address'] = request.form['address'].strip()

        # ✨ NEW: Refresh the client_code if name changed
        client['client_code'] = ''.join([word[0] for word in client['name'].upper().split() if word.isalnum()])[:2]

        # Update contacts
        contacts = []
        for i in range(1, 10):
            contact_name = request.form.get(f'contact{i}_name', '').strip()
            contact_email = request.form.get(f'contact{i}_email', '').strip()
            contact_phone = request.form.get(f'contact{i}_phone', '').strip()
            if contact_name:
                contacts.append({
                    'name': contact_name,
                    'email': contact_email,
                    'phone': contact_phone
                })

        client['contacts'] = contacts

        save_clients(clients)

        flash("Client updated successfully!", "success")
        return redirect(url_for('manage_clients'))

    return render_template('edit_client.html', client=client)

@app.route('/admin/assignments', methods=['GET', 'POST'])
def admin_assignments():
    if 'user' not in session or session['user']['role'] != 'Admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    clients = load_clients()
    users = load_all_users()
    pms = [u for u in users if u['role'] == 'Property Manager']

    # Load current assignments
    assignments = {}
    if os.path.exists('assignments.csv'):
        with open('assignments.csv', newline='') as f:
            for row in csv.DictReader(f):
                assignments[row['client_name']] = row['manager_email']

    if request.method == 'POST':
        updated_assignments = []
        for client in clients:
            field = f"pm_for_{client['name']}"
            manager_email = request.form.get(field, '').strip()
            if manager_email:
                updated_assignments.append({
                    'client_name': client['name'],
                    'manager_email': manager_email
                })

        # Save updated assignments
        with open('assignments.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['manager_email', 'client_name'])
            writer.writeheader()
            writer.writerows(updated_assignments)

        flash("Assignments updated successfully!", "success")
        return redirect(url_for('admin.alerts')
)

    return render_template('assignments.html', clients=clients, managers=pms, assignments=assignments)

@app.route('/pm/inspections')
def pm_inspections():
    if 'user' not in session or session['user']['role'] != 'Property Manager':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    pm_email = session['user']['username']
    assigned_clients = get_clients_for_manager(pm_email)

    logs = []
    if os.path.exists(LOG_CSV):
        with open(LOG_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['client'] in assigned_clients:
                    logs.append(row)

    return render_template('pm_inspections.html', logs=logs, clients=assigned_clients)

from collections import defaultdict

@app.route('/add-maintenance-task', methods=['GET', 'POST'])
def add_maintenance_task():
    if 'user' not in session or session['user']['role'] not in ['Admin', 'Property Manager']:
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    client_groups = defaultdict(list)

    # Load and group client names
    if os.path.exists('clients.csv'):
        with open('clients.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                client_name = row.get('client_name', '').strip()
                if client_name:
                    first_letter = client_name[0].upper()
                    client_groups[first_letter].append(client_name)

    for letter in client_groups:
        client_groups[letter] = sorted(client_groups[letter])

    client_groups = dict(sorted(client_groups.items()))  # final sorting A-Z

    if request.method == 'POST':
        client = request.form['client']
        title = request.form['title']
        date = request.form['date']
        frequency = request.form.get('frequency', 'One-time')
        notes = request.form['notes']
        created_by = session['user'].get('full_name') or session['user'].get('name_or_company', session['user']['username'])

        file_exists = os.path.exists('manual_tasks.csv')
        with open('manual_tasks.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['client', 'title', 'date', 'notes', 'frequency', 'created_by', 'completed'])
            if not file_exists:
                writer.writeheader()

            # Write original task
            writer.writerow({
                'client': client,
                'title': title,
                'date': date,
                'notes': notes,
                'frequency': frequency,
                'created_by': created_by,
                'completed': 'no'
            })
            print("✅ Saved original task")

            # Handle recurring logic
            if request.form.get('repeat_tasks') == 'yes':
                intervals = {
                    'Daily': relativedelta(days=1),
                    'Weekly': relativedelta(weeks=1),
                    'Fortnightly': relativedelta(weeks=2),
                    'Monthly': relativedelta(months=1),
                    'Bi-monthly': relativedelta(months=2),
                    'Tri-monthly': relativedelta(months=3),
                    'Quarterly': relativedelta(months=3),
                    'Bi-annual': relativedelta(months=6),
                    'Annually': relativedelta(years=1)
                }
                interval = intervals.get(frequency)
                if interval:
                    base_date = datetime.strptime(date, "%Y-%m-%d").date()
                    for i in range(1, 12):  # Generate 11 future tasks
                        next_date = base_date + (interval * i)
                        writer.writerow({
                            'client': client,
                            'title': title,
                            'date': next_date.strftime("%Y-%m-%d"),
                            'notes': notes,
                            'frequency': frequency,
                            'created_by': created_by,
                            'completed': 'no'
                        })
                    print(f"✅ Generated 11 recurring tasks for frequency: {frequency}")

        # Redirect after saving
        if session['user']['role'] == 'Property Manager':
            return redirect(url_for('property_manager_maintenance_planner'))
        else:
            return redirect(url_for('admin_maintenance_planner'))

    # GET request
    return render_template('add_maintenance_task.html', client_groups=client_groups)


def get_missed_tasks_for_pm(username):
    today = datetime.today().date()
    missed = []

    full_name = session['user'].get('full_name') or session['user'].get('name_or_company') or username

    if os.path.exists('manual_tasks.csv'):
        with open('manual_tasks.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                created_by = row.get('created_by', '')
                completed = row.get('completed', 'no').lower()

                if completed != 'yes' and (created_by == username or created_by == full_name):
                    try:
                        task_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                        if task_date < today:
                            missed.append({
                                'title': row['title'],
                                'client': row['client'],
                                'date': row['date'],
                                'type': 'Manual',
                                'frequency': row['frequency'],
                                'completed': completed
                            })
                    except ValueError:
                        continue

    return missed

def get_missed_tasks_for_admin():
    today = datetime.today().date()
    missed = []

    if os.path.exists('manual_tasks.csv'):
        with open('manual_tasks.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                created_by = row.get('created_by', '')
                completed = row.get('completed', 'no').lower()

                if completed != 'yes':
                    try:
                        task_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                        if task_date < today:
                            missed.append({
                                'title': row['title'],
                                'client': row['client'],
                                'date': row['date'],
                                'type': 'Manual',
                                'frequency': row['frequency'],
                                'created_by': created_by,
                                'completed': completed
                            })
                    except ValueError:
                        continue

    return missed

@app.route('/complete-task', methods=['POST'])
def complete_task():
    title = request.form['title']
    date = request.form['date']
    client = request.form['client']

    updated_rows = []
    fieldnames = ['client', 'title', 'date', 'notes', 'frequency', 'created_by', 'completed']

    # Read and update rows
    with open('manual_tasks.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['title'] == title and row['date'] == date and row['client'] == client:
                row['completed'] = 'yes'
            updated_rows.append(row)

    # Safely write only expected fields
    with open('manual_tasks.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in updated_rows:
            clean_row = {field: row.get(field, '') for field in fieldnames}  # ✅ Strip unknown keys
            writer.writerow(clean_row)

    flash("Task marked as complete!", "success")
    if session['user']['role'] == 'Admin':
        return redirect(url_for('admin_management_dashboard'))
    else:
        return redirect(url_for('property_manager_dashboard'))

from datetime import datetime

# --- Helper function ---
def save_task_history(action, title, client, date, performed_by):
    """Save an edit or delete action to task_history.csv"""
    history_file = 'task_history.csv'
    file_exists = os.path.exists(history_file)

    with open(history_file, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['timestamp', 'action', 'title', 'client', 'date', 'performed_by']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'title': title,
            'client': client,
            'date': date,
            'performed_by': performed_by
        })

# --- Edit Task Route ---
@app.route('/edit-task', methods=['GET', 'POST'])
def edit_task():
    fieldnames = ['client', 'title', 'date', 'notes', 'frequency', 'created_by', 'completed']

    if request.method == 'GET':
        title = request.args.get('title')
        date = request.args.get('date')
        client = request.args.get('client')

        task_to_edit = None
        if os.path.exists('manual_tasks.csv'):
            with open('manual_tasks.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['title'] == title and row['date'] == date and row['client'] == client:
                        task_to_edit = row
                        break

        if not task_to_edit:
            flash("Task not found.", "danger")
            return redirect(url_for('property_manager_dashboard'))

        # Group client names A–Z
        client_groups = {}
        if os.path.exists('clients.csv'):
            with open('clients.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    client_name = row.get('client_name')
                    if client_name:
                        first_letter = client_name[0].upper()
                        client_groups.setdefault(first_letter, []).append(client_name)

        # Sort clients inside each letter group
        for letter in client_groups:
            client_groups[letter].sort()

        # Frequency options
        frequency_options = [
            'One-time', 'Daily', 'Weekly', 'Fortnightly', 'Monthly',
            'Bi-monthly', 'Tri-monthly', 'Quarterly', 'Bi-annual', 'Annually'
        ]

        return render_template(
            'edit_task.html',
            task=task_to_edit,
            client_groups=client_groups,
            frequency_options=frequency_options
        )

    # POST: Save the edited task
    updated_rows = []
    if os.path.exists('manual_tasks.csv'):
        with open('manual_tasks.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row['title'] == request.form['original_title'] and
                    row['date'] == request.form['original_date'] and
                    row['client'] == request.form['original_client']):
                    updated_rows.append({
                        'client': request.form['client'],
                        'title': request.form['title'],
                        'date': request.form['date'],
                        'notes': request.form['notes'],
                        'frequency': request.form['frequency'],
                        'created_by': row.get('created_by', ''),
                        'completed': row.get('completed', 'no')
                    })
                else:
                    updated_rows.append(row)

    with open('manual_tasks.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in updated_rows:
            clean_row = {field: row.get(field, '') for field in fieldnames}
            writer.writerow(clean_row)

    flash("Task updated successfully!", "success")
    if session['user']['role'] == 'Admin':
        return redirect(url_for('admin_management_dashboard'))
    else:
        return redirect(url_for('property_manager_dashboard'))

# --- Delete Task Route ---
@app.route('/delete-task', methods=['POST'])
def delete_task():
    title = request.form['title']
    date = request.form['date']
    client = request.form['client']

    fieldnames = ['client', 'title', 'date', 'notes', 'frequency', 'created_by', 'completed']

    updated_rows = []
    task_found = False

    if os.path.exists('manual_tasks.csv'):
        with open('manual_tasks.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['title'] == title and row['date'] == date and row['client'] == client:
                    task_found = True  # Skip this row (delete it)
                    continue
                updated_rows.append(row)

    with open('manual_tasks.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in updated_rows:
            clean_row = {field: row.get(field, '') for field in fieldnames}
            writer.writerow(clean_row)

    if task_found:
        # ✅ Save to Task History
        save_task_history(
            action='delete',
            title=title,
            client=client,
            date=date,
            performed_by=session['user']['username']
        )
        flash("Task deleted successfully!", "success")
    else:
        flash("Task not found. No changes made.", "warning")

    if session['user']['role'] == 'Admin':
        return redirect(url_for('admin_management_dashboard'))
    else:
        return redirect(url_for('property_manager_dashboard'))

from datetime import datetime

def save_task_history(action, title, client, date, performed_by):
    """Save an edit or delete action to task_history.csv"""
    history_file = 'task_history.csv'
    file_exists = os.path.exists(history_file)

    with open(history_file, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['timestamp', 'action', 'title', 'client', 'date', 'performed_by']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'title': title,
            'client': client,
            'date': date,
            'performed_by': performed_by
        })

@app.route('/task-history', methods=['GET', 'POST'])
def task_history():
    if 'user' not in session or session['user']['role'] != 'Admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    history = []
    if os.path.exists('task_history.csv'):
        with open('task_history.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                history.append(row)

    # Sort newest first
    history.sort(key=lambda x: x['timestamp'], reverse=True)

    filtered_history = history

    # Apply filters if needed
    if request.method == 'POST':
        user_filter = request.form.get('performed_by')
        action_filter = request.form.get('action')

        if user_filter:
            filtered_history = [h for h in filtered_history if h['performed_by'] == user_filter]

        if action_filter:
            filtered_history = [h for h in filtered_history if h['action'] == action_filter]

    # Collect unique users and actions for dropdowns
    users = sorted(set(h['performed_by'] for h in history))
    actions = ['edit', 'delete']

    return render_template('task_history.html', history=filtered_history, users=users, actions=actions)

from flask import Response

@app.route('/download-task-history', methods=['POST'])
def download_task_history():
    if 'user' not in session or session['user']['role'] != 'Admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    history = []
    if os.path.exists('task_history.csv'):
        with open('task_history.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                history.append(row)

    # Apply same filters if provided
    user_filter = request.form.get('performed_by')
    action_filter = request.form.get('action')
    title_search = request.form.get('title_search', '').lower()
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    if user_filter:
        history = [h for h in history if h['performed_by'] == user_filter]

    if action_filter:
        history = [h for h in history if h['action'] == action_filter]

    if title_search:
        history = [h for h in history if title_search in h['title'].lower()]

    if start_date:
        history = [h for h in history if h['timestamp'] >= start_date]
    if end_date:
        history = [h for h in history if h['timestamp'] <= end_date + "T23:59:59"]

    # Prepare CSV
    output = "timestamp,action,title,client,date,performed_by\n"
    for h in history:
        output += f"{h['timestamp']},{h['action']},{h['title']},{h['client']},{h['date']},{h['performed_by']}\n"

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=task_history.csv"}
    )

@app.route('/download-inspection-log/<equipment_id>')
def download_inspection_log(equipment_id):
    if 'user' not in session or session['user']['role'] not in ['Admin', 'Property Manager']:
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    logs = []
    if os.path.exists(LOG_CSV):
        with open(LOG_CSV, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if equipment_id == 'all' or row['equipment_id'] == equipment_id:
                    logs.append(row)

    if not logs:
        flash("No logs found.", "warning")
        return redirect(url_for('property_manager_dashboard'))

    if equipment_id == 'all':
        equipment = {'id': 'All Equipment', 'name': 'All Equipment'}
    else:
        equipment = get_equipment_by_id(equipment_id)
        if not equipment:
            flash("Equipment not found.", "warning")
            return redirect(url_for('property_manager_dashboard'))

    rendered = render_template('inspection_log_pdf.html', logs=logs, equipment=equipment)

    pdf = HTML(string=rendered).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    filename = 'all_inspection_logs.pdf' if equipment_id == 'all' else f'inspection_log_{equipment_id}.pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'

    return response

@app.route('/export-inspections', methods=['GET', 'POST'])
def filtered_inspection_export():
    if 'user' not in session or session['user']['role'] not in ['Admin', 'Property Manager']:
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    if request.method == 'GET':
        # Load clients
        client_list = []
        if os.path.exists('clients.csv'):
            with open('clients.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('client_name'):
                        client_list.append(row['client_name'])

        return render_template('export_inspection_log.html', clients=client_list)

    # POST - apply filters
    selected_client = request.form.get('client')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    add_watermark = request.form.get('add_watermark') == 'yes'

    logs = []
    if os.path.exists(LOG_CSV):
        with open(LOG_CSV, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                match = True
                if selected_client and selected_client != row.get('client', ''):
                    match = False
                if start_date and row['timestamp'] < start_date:
                    match = False
                if end_date and row['timestamp'] > end_date + "T23:59:59":
                    match = False

                if match:
                    logs.append(row)

    equipment = {'name': 'Filtered Inspections', 'id': 'Multiple'}

    rendered = render_template(
        'inspection_log_pdf.html',
        logs=logs,
        equipment=equipment,
        now=datetime.now(),
        add_watermark=add_watermark
    )

    pdf = HTML(string=rendered).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=filtered_inspections.pdf'

    return response

@app.route('/admin/upload-logo', methods=['GET', 'POST'])
def upload_logo():
    if 'user' not in session or session['user']['role'] != 'Admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['logo']
        if file:
            filename = session['user']['company'] + '.png'
            save_path = os.path.join('static', 'logos', filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)
            flash("Logo uploaded successfully!", "success")
            return redirect(url_for('admin_management_dashboard'))
        else:
            flash("No file selected.", "warning")
            return redirect(url_for('upload_logo'))

    return render_template('upload_logo.html')

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if 'user' not in session or session['user']['role'] != 'Admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    # Load current settings
    settings = load_settings()

    if request.method == 'POST':
        # Update text settings
        settings['company_name'] = request.form.get('company_name', settings.get('company_name', ''))
        settings['company_address'] = request.form.get('company_address', settings.get('company_address', ''))
        settings['company_email'] = request.form.get('company_email', settings.get('company_email', ''))
        settings['company_phone'] = request.form.get('company_phone', settings.get('company_phone', ''))
        settings['company_license'] = request.form.get('company_license', settings.get('company_license', ''))

        # Handle logo upload
        file = request.files.get('logo')
        if file and file.filename != '':
            filename = session['user']['company'] + '.png'
            save_path = os.path.join('static', 'logos', filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)
            flash("Logo uploaded successfully!", "success")

        # Save settings to settings.json
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)

        flash("Settings updated successfully!", "success")
        return redirect(url_for('admin.admin_settings')


)

    return render_template('admin_settings.html', settings=settings)

@app.route('/contractor/settings', methods=['GET', 'POST'])
def contractor_settings():
    if 'user' not in session or session['user']['role'] != 'Admin Contractor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['logo']
        if file:
            filename = session['user']['company'] + '.png'
            save_path = os.path.join('static', 'logos', filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)
            flash("Logo uploaded successfully!", "success")
            return redirect(url_for('contractor_settings'))

    return render_template('contractor_settings.html')

@app.route('/get-next-equipment-id', methods=['POST'])
def get_next_equipment_id():
    client = request.form['client']
    client_initials = ''.join(word[0] for word in client.split() if word).upper()

    existing_ids = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['client'] == client:
                    existing_ids.append(row['id'])

    next_number = 1
    if existing_ids:
        numbers = []
        for eq_id in existing_ids:
            try:
                parts = eq_id.split('-')
                if len(parts) >= 2:
                    num = int(parts[1])
                    numbers.append(num)
            except (ValueError, IndexError):
                continue
        if numbers:
            next_number = max(numbers) + 1

    new_id = f"EQP-{str(next_number).zfill(5)}-{client_initials}"
    return {'next_id': new_id}

@app.route('/admin/capex')
def capex_dashboard():
    if 'user' not in session or session['user']['role'] != 'Admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    return render_template('capex_dashboard.html')

@app.route('/director-dashboard')
def director_dashboard():
    if 'user' not in session or session['user']['role'] != 'Director':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    area_filter = request.args.get('area')
    status_filter = request.args.get('status')
    year_filter = request.args.get('year')
    capex_requests = get_filtered_capex_requests(area=area_filter, status=status_filter, year=year_filter)

    company = Client.query.filter_by(name=session['user']['company']).first()

    # Prepare assignment data for display
    area_assignments = db.session.query(DirectorAreaAssignment.area_name, DirectorAreaAssignment.director_email).all()
    assignments = {}
    for area, email in area_assignments:
        assignments[area] = email

    # Prepare unique values for dropdowns
    all_areas = sorted({req.area for req in CapexRequest.query.distinct(CapexRequest.area)})
    all_statuses = ['Pending', 'Responded', 'Approved', 'Declined', 'On Hold', 'Scheduled', 'Completed']  # static list

    all_years = sorted({req.date_submitted.year for req in CapexRequest.query if req.date_submitted})
    return render_template('director_dashboard.html', capex_requests=capex_requests, assignments=assignments, areas=all_areas, statuses=all_statuses, years=all_years, company=company)

@app.route('/director-settings')
def director_settings():
    return render_template('director_settings.html')

@app.route('/director-settings/assign-area', methods=['GET', 'POST'])
def assign_director():
    if 'user' not in session or session['user']['role'] != 'Admin':
        flash("Only Admins can assign directors.", "danger")
        return redirect(url_for('login'))

    all_directors = User.query.filter(User.role == 'Director').all()
    all_areas = db.session.query(DirectorAreaAssignment.area_name).distinct().all()
    all_areas = [a.area_name for a in all_areas]

    if request.method == 'POST':
        director_email = request.form['director_email']
        area_name = request.form['area_name'].strip()

        # Allow new area creation
        if not area_name:
            flash("Area name cannot be empty.", "warning")
            return redirect(url_for('assign_director'))

        new_assignment = DirectorAreaAssignment(
            director_email=director_email,
            area_name=area_name
        )
        db.session.add(new_assignment)
        db.session.commit()

        flash(f"{director_email} assigned to area: {area_name}.", "success")
        return redirect(url_for('assign_director'))

    return render_template('director_settings/assign_area.html', directors=all_directors, areas=all_areas)

@app.route('/director-settings/remove-assignment/<int:assignment_id>', methods=['POST'])
def remove_assignment(assignment_id):
    if 'user' not in session or session['user']['role'] != 'Admin':
        flash("Only Admins can remove assignments.", "danger")
        return redirect(url_for('login'))

    assignment = DirectorAreaAssignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()

    flash(f"Assignment for {assignment.director_email} to area '{assignment.area_name}' has been removed.", "success")
    return redirect(url_for('assign_director'))

@app.route("/submit_capex", methods=["GET", "POST"])
def submit_capex():
    if 'user' not in session or session['user']['role'] != 'Director':
        flash("Only Directors can submit CAPEX requests.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        area = request.form.get("area")
        description = request.form.get("description")
        estimated_cost = request.form.get("estimated_cost")
        submitted_by = session['user']['email']
        date_submitted = datetime.now()
        file = request.files.get("file")

        filename = ""
        if file and file.filename:
            upload_folder = os.path.join("static", "uploads", "capex")
            os.makedirs(upload_folder, exist_ok=True)
            safe_name = secure_filename(file.filename)
            filename = f"{uuid.uuid4()}_{safe_name}"
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
        else:
            file_path = ""

        new_request = CapexRequest(
            area=area,
            description=description,
            estimated_cost=float(estimated_cost),
            status="Submitted",
            submitted_by=submitted_by,
            file_path=file_path,
            date_submitted=date_submitted
        )
        db.session.add(new_request)
        db.session.commit()

        flash("CAPEX request submitted successfully.", "success")
        return redirect(url_for("director_dashboard"))

    return render_template("submit_capex.html")

@app.route('/respond-capex/<int:capex_id>', methods=['GET', 'POST'])
def respond_capex(capex_id):
    if 'user' not in session or session['user']['role'] != 'Property Manager':
        flash("Access denied. Only Property Managers can respond to CAPEX requests.", "danger")
        return redirect(url_for("login"))

    capex_request = CapexRequest.query.get_or_404(capex_id)

    if request.method == "POST":
        submitted_by = session['user']['email']
        notes = request.form.get("notes")
        upload_folder = os.path.join("static", "uploads", "capex_responses")
        os.makedirs(upload_folder, exist_ok=True)

        response_data = {
            "capex_request_id": capex_id,
            "submitted_by": submitted_by,
            "notes": notes
        }

        for i in range(1, 6):
            name_field = f"contractor_{i}_name"
            file_field = f"contractor_{i}_file"

            response_data[name_field] = request.form.get(name_field)

            uploaded_file = request.files.get(file_field)
            if uploaded_file and uploaded_file.filename:
                filename = f"{uuid.uuid4()}_{secure_filename(uploaded_file.filename)}"
                filepath = os.path.join(upload_folder, filename)
                uploaded_file.save(filepath)
                response_data[file_field] = filepath
            else:
                response_data[file_field] = None

        new_response = CapexResponse(**response_data)
        db.session.add(new_response)
        db.session.commit()

        flash("CAPEX response submitted successfully.", "success")
        return redirect(url_for("property_manager_dashboard"))

    return render_template("respond_capex.html", capex_id=capex_id, capex_request=capex_request)

@app.route('/view-responses/<int:capex_id>')
def view_responses(capex_id):
    if 'user' not in session or session['user']['role'] != 'Director':
        flash("Access denied. Only Directors can view CAPEX responses.", "danger")
        return redirect(url_for("login"))

    capex_request = CapexRequest.query.get_or_404(capex_id)
    responses = CapexResponse.query.filter_by(capex_request_id=capex_id).all()

    return render_template("view_responses.html", capex_request=capex_request, responses=responses)

@app.route('/set-scheduled-date/<int:capex_id>', methods=['GET', 'POST'])
def set_scheduled_date(capex_id):
    if 'user' not in session or session['user']['role'] != 'Property Manager':
        flash("Access denied. Only Property Managers can set scheduled dates.", "danger")
        return redirect(url_for("login"))

    capex_request = CapexRequest.query.get_or_404(capex_id)

    if request.method == 'POST':
        date_str = request.form.get('scheduled_date')
        if date_str:
            capex_request.scheduled_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            db.session.commit()
            flash("Scheduled date set successfully.", "success")
            return redirect(url_for("property_manager_dashboard"))

    return render_template("set_scheduled_date.html", capex_request=capex_request)

@app.route('/capex-decision/<int:capex_id>/<action>', methods=['POST'])
def capex_decision(capex_id, action):
    from app.models import CapexRequest, CapexApproval, User, DirectorAreaAssignment, db
    from flask import request, session, redirect, url_for, flash
    from datetime import datetime

    if 'user' not in session:
        flash("Login required.", "danger")
        return redirect(url_for('login'))

    user_email = session['user']['email']
    user_role = session['user']['role']

    if action not in ['approve', 'decline', 'hold']:
        flash("Invalid action.", "danger")
        return redirect(url_for('view_responses', capex_id=capex_id))

    capex = CapexRequest.query.get_or_404(capex_id)

    existing = CapexApproval.query.filter_by(capex_request_id=capex.id, approved_by=user_email).first()
    if existing:
        flash("You have already submitted a decision for this request.", "warning")
        return redirect(url_for('view_responses', capex_id=capex_id))

    note = request.form.get('note') if action in ['decline', 'hold'] else ''

    approval = CapexApproval(
        capex_request_id=capex.id,
        approved_by=user_email,
        role=user_role,
        action=action,
        note=note,
        timestamp=datetime.utcnow()
    )
    db.session.add(approval)
    db.session.commit()

    # Check approval state
    approvals = CapexApproval.query.filter_by(capex_request_id=capex.id, action='approve').all()
    approved_emails = [a.approved_by for a in approvals]

    chair_approved = any(a.role == 'Chairperson' for a in approvals)

    assigned_directors = db.session.query(DirectorAreaAssignment).filter_by(area_name=capex.area).all()
    assigned_emails = [d.director_email for d in assigned_directors]
    assigned_director_approved = any(email in approved_emails for email in assigned_emails)

    total_directors = db.session.query(User).filter_by(role='Director').count()
    approval_count = len(approvals)

    if action == 'approve':
        if chair_approved and assigned_director_approved:
            capex.status = 'Approved'
        elif approval_count > total_directors / 2:
            capex.status = 'Approved'

    elif action == 'decline':
        capex.status = 'Declined'
    elif action == 'hold':
        capex.status = 'On Hold'

    db.session.commit()

    from notification_helpers import notify_users
    notify_users(
        message=f"CAPEX '{capex.area}' was {action}d.",
        capex_id=capex.id,
        roles_to_notify=["Director", "Property Manager"],
        additional_emails=[capex.submitted_by]
    )

    flash(f"CAPEX has been {action}d successfully.", "success")
    return redirect(url_for('view_responses', capex_id=capex.id))

def get_filtered_capex_requests(area=None, status=None, year=None):
    from app.models import CapexRequest

    query = CapexRequest.query

    if area:
        query = query.filter(CapexRequest.area == area)
    if status:
        query = query.filter(CapexRequest.status == status)
    if year:
        query = query.filter(extract('year', CapexRequest.date_submitted) == int(year))

    return query.order_by(CapexRequest.date_submitted.desc()).all()

def notify_users(message, capex_id=None, roles_to_notify=None, additional_emails=None):
    from app.models import User, Notification
    from app import db

    recipients = set()

    # Get emails by role
    if roles_to_notify:
        users = User.query.filter(User.role.in_(roles_to_notify)).all()
        recipients.update(user.email for user in users)

    # Add manually specified emails
    if additional_emails:
        recipients.update(additional_emails)

    # Always notify admins silently
    admins = User.query.filter(User.role == 'Admin').all()
    recipients.update(admin.email for admin in admins)

    # Create notification entries
    for email in recipients:
        new_note = Notification(
            recipient_email=email,
            message=message,
            capex_id=capex_id
        )
        db.session.add(new_note)

    db.session.commit()

@app.route('/seed-clients')
def seed_clients():
    from app.models import Client, db

    demo_clients = [
        Client(name="Oakwood OMC", address="Dublin", registration_number="OMC123", year_of_construction="2010", number_of_units=45, client_type="omc"),
        Client(name="GreenLine Management", address="Cork", registration_number="MGMT456", year_of_construction="2015", number_of_units=120, client_type="management"),
        Client(name="FireCheck Ltd", address="Galway", registration_number="CON789", year_of_construction="2012", number_of_units=0, client_type="contractor")
    ]

    db.session.add_all(demo_clients)
    db.session.commit()
    return "Clients seeded successfully."

if __name__ == '__main__':
    app.run(debug=True)