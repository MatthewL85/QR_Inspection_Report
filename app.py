from auth import create_user, authenticate_user, user_exists
from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash, abort
from werkzeug.security import generate_password_hash
from dateutil.relativedelta import relativedelta
import csv
import os
import qrcode
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key

DATA_FILE = 'equipment.csv'
LOG_CSV = 'inspection_logs.csv'
QR_FOLDER = 'static/qrcodes'
USER_CSV = 'users.csv'


os.makedirs(QR_FOLDER, exist_ok=True)


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
        return redirect(url_for('admin_dashboard'))
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
                if row['name']:  # or row['client_name'] if your column is named that
                    client_names.append(row['name'])

    if request.method == 'POST':
        eq_id = request.form['id']
        client = request.form['client']
        name = request.form['name']
        location = request.form['location']
        model = request.form['model']
        age = request.form['age']
        last_inspection = request.form['last_inspection']
        pin = request.form['pin']

        file_exists = os.path.isfile(DATA_FILE)

        with open(DATA_FILE, 'a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
               writer.writerow(['id', 'client', 'name', 'location', 'model', 'age', 'last_inspection', 'pin', 'created_by'])
            created_by = session['user']['username'] if 'user' in session else 'Unknown'
            writer.writerow([eq_id, client, name, location, model, age, last_inspection, pin, created_by])

            print("Saved to CSV:", eq_id, name, pin)
            print("CSV Path:", os.path.abspath(DATA_FILE))

        # Generate QR Code
        qr_url = url_for('enter_pin', equipment_id=eq_id, _external=True)
        img = qrcode.make(qr_url)
        img.save(f'{QR_FOLDER}/{eq_id}.png')
        return redirect(url_for('index'))

    return render_template('generate.html')

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        user = authenticate_user(email, password)

        if user:
            # Normalize role casing
            user['role'] = user.get('role', '').strip().title()
            session['user'] = user
            flash('Login successful!', 'success')

            role = user['role']

            # Direct to specific dashboards
            if role == 'Admin Contractor':
                return redirect(url_for('admin_contractor_dashboard'))
            elif role == 'Admin':
                return redirect(url_for('admin_management_dashboard'))
            elif role == 'Property Manager':
                return redirect(url_for('property_manager_dashboard'))
            elif role == 'Contractor':
                return redirect(url_for('contractor_dashboard'))
            else:
                flash("Unknown role. Please contact your administrator.", "danger")
                return redirect(url_for('login'))

        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

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

    return render_template(
        'admin_management_dashboard.html',
        missed_tasks=missed_tasks
    )

@app.route('/admin-contractor-dashboard')
def admin_contractor_dashboard():
    if 'user' not in session or session['user']['role'] != 'Admin Contractor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))
    return render_template('admin_contractor_dashboard.html')


@app.route('/admin/clients')
def manage_clients():
    clients = load_clients()

    # Load assignments
    assignments = {}
    if os.path.exists('assignments.csv'):
        with open('assignments.csv', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assignments[row['client_name']] = row['manager_email']

    # Attach PM email to each client
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

def get_upcoming_maintenance_for_pm(pm_username):
    upcoming = []
    today = datetime.today().date()
    seen_equipment = set()

    if os.path.exists(LOG_CSV):
        with open(LOG_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                eq_id = row['equipment_id']
                created_by = get_equipment_by_id(eq_id).get('created_by', '')
                
                if row['functional'].startswith("Next Maintenance:") and eq_id not in seen_equipment:
                    if created_by == pm_username:
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
    
    upcoming_maintenance = get_upcoming_maintenance()
    return render_template('admin_maintenance_planner.html', maintenance=upcoming_maintenance)

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
                            'type': 'manual'
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
    return render_template('onboard.html')
    
@app.route('/register-company/<company_type>', methods=['GET', 'POST'])
def register_company(company_type):
    if request.method == 'POST':
        company_name = request.form['company_name']
        admin_email = request.form['admin_email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        print("Submitted:", company_name, admin_email, password, confirm_password)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register_company.html', company_type=company_type)

        if user_exists(admin_email):
            flash("An account with that email already exists.", "warning")
            return render_template('register_company.html', company_type=company_type)

        # 👇 Assign a different admin role based on company_type
        if company_type.lower() == 'contractor':
            role = 'Admin Contractor'
        else:
            role = 'Admin'

        # ❌ Remove generate_password_hash here
        # ✅ Let create_user handle the hashing
        create_user(username=admin_email, password=password, role=role, company=company_name)

        flash(f"{company_type} registered successfully! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register_company.html', company_type=company_type)

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

        # Restrict Contractor Admin from changing role to non-contractor
        if session['user']['role'] == 'Admin Contractor' and new_role != 'Contractor':
            flash("You can only assign Contractor role.", "danger")
            return redirect(url_for('manage_users'))

        for u in users:
            if u['username'] == email:
                u['role'] = new_role
                u['company'] = new_company
                break

        with open(USER_CSV, 'w', newline='') as csvfile:
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

    current_role = session['user']['role']
    company = session['user']['company']

    # Set allowed roles based on who is logged in
    if current_role == 'Admin':
        allowed_roles = ['Admin', 'Contractor', 'Property Manager']
    else:
        allowed_roles = ['Contractor']

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        confirm_password = request.form['confirm_password'].strip()
        role = request.form['role'].strip()
        pin = request.form['pin'].strip()
        name_or_company = request.form['name_or_company'].strip()

        if role not in allowed_roles:
            flash("Invalid role selection.", "danger")
            return render_template('add_user.html', allowed_roles=allowed_roles)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('add_user.html', allowed_roles=allowed_roles)

        if user_exists(username):
            flash("User already exists.", "warning")
            return render_template('add_user.html', allowed_roles=allowed_roles)

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
    with open('clients.csv', 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                contacts = json.loads(row['contacts'].replace('""', '"'))
            except json.JSONDecodeError:
                contacts = []

            client = {
                'name': row['client_name'],
                'address': row['address'],
                'contacts': contacts,
                'assigned_manager_email': row.get('assigned_manager_email', ''),
                'company': row.get('company', '')
            }
            clients.append(client)
    return clients

@app.route('/report/<client_id>')
def report_client(client_id):
    clients = load_clients()
    client = next((c for c in clients if c['id'] == client_id), None)
    if not client:
        return "Client not found", 404
    return render_template('report_client.html', client=client)

@app.route('/add-client', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        # Generate a new ID (can be improved later with UUID or auto-increment)
        new_id = str(uuid.uuid4())  # import uuid at the top

        name = request.form['name']
        address = request.form['address']

        contacts = []
        for i in range(1, 10):
            contact_name = request.form.get(f'contact{i}_name', '').strip()
            contact_email = request.form.get(f'contact{i}_email', '').strip()
            contact_phone = request.form.get(f'contact{i}_phone', '').strip()
            if contact_name:  # Only include if there's a name
                contacts.append({
                    'name': contact_name,
                    'email': contact_email,
                    'phone': contact_phone
                })

        # Prepare row
        row = {
            'id': new_id,
            'name': name,
            'address': address
        }
        for idx, contact in enumerate(contacts, 1):
            row[f'contact{idx}_name'] = contact['name']
            row[f'contact{idx}_email'] = contact['email']
            row[f'contact{idx}_phone'] = contact['phone']

        # Get all fieldnames including dynamic contact fields
        fieldnames = ['id', 'name', 'address']
        for i in range(1, 10):
            fieldnames += [f'contact{i}_name', f'contact{i}_email', f'contact{i}_phone']

        # Save to clients.csv
        file_exists = os.path.isfile('clients.csv')
        with open('clients.csv', 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        return redirect(url_for('show_dashboard'))  # Adjust as needed

    return render_template('add_client.html')

@app.route('/edit-client/<client_id>', methods=['GET', 'POST'])
def edit_client(client_id):
    clients = load_clients()
    client = next((c for c in clients if c['name'] == client_id), None)

    if not client:
        return "Client not found", 404

    if request.method == 'POST':
        client['name'] = request.form['name']
        client['address'] = request.form['address']

        contacts = []
        for i in range(1, 10):
            name = request.form.get(f'contact{i}_name', '').strip()
            email = request.form.get(f'contact{i}_email', '').strip()
            phone = request.form.get(f'contact{i}_phone', '').strip()
            if name:
                contacts.append({'name': name, 'email': email, 'phone': phone})

        client['contacts'] = contacts

        # Save back to CSV
        with open('clients.csv', 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['client_name', 'address', 'contacts', 'assigned_manager_email', 'company']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for c in clients:
                row = {
                    'client_name': c['name'],
                    'address': c['address'],
                    'contacts': json.dumps(c['contacts']),
                    'assigned_manager_email': c.get('assigned_manager_email', ''),
                    'company': c.get('company', '')
                }
                writer.writerow(row)

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
        return redirect(url_for('admin_assignments'))

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

@app.route('/add-maintenance-task', methods=['GET', 'POST'])
def add_maintenance_task():
    if 'user' not in session or session['user']['role'] not in ['Admin', 'Property Manager']:
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    client_names = []
    if os.path.exists('clients.csv'):
        with open('clients.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                client_name = row.get('client_name')
                if client_name:
                    client_names.append(client_name)

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
                    for i in range(1, 12):  # Generate 11 more tasks
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

        # Redirect
        if session['user']['role'] == 'Property Manager':
            return redirect(url_for('property_manager_maintenance_planner'))
        else:
            return redirect(url_for('admin_maintenance_planner'))

    # GET request
    return render_template('add_maintenance_task.html', client_names=client_names)

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

        # Load client list based on role
        client_names = []
        if os.path.exists('clients.csv'):
            with open('clients.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if session['user']['role'] == 'Admin':
                    for row in reader:
                        if row.get('client_name'):
                            client_names.append(row['client_name'])
                else:
                    assigned_clients = get_clients_for_manager(session['user']['username'])
                    for row in reader:
                        if row.get('client_name') and row['client_name'] in assigned_clients:
                            client_names.append(row['client_name'])

        # Standard frequency options
        frequency_options = [
            'One-time', 'Daily', 'Weekly', 'Fortnightly', 'Monthly',
            'Bi-monthly', 'Tri-monthly', 'Quarterly', 'Bi-annual', 'Annually'
        ]

        return render_template(
            'edit_task.html',
            task=task_to_edit,
            client_names=client_names,
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
        flash("Task deleted successfully!", "success")
    else:
        flash("Task not found. No changes made.", "warning")

    if session['user']['role'] == 'Admin':
        return redirect(url_for('admin_management_dashboard'))
    else:
        return redirect(url_for('property_manager_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)