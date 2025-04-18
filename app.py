from auth import create_user, authenticate_user, user_exists
from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash, abort
import csv
import os
import qrcode
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key

DATA_FILE = 'equipment.csv'
LOG_CSV = 'inspection_logs.csv'
QR_FOLDER = 'static/qrcodes'

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

    user = session['user']
    role = user.get('role')
    username = user.get('username')
    company = user.get('company')

    equipment = load_equipment()

    if role == 'Property Manager':
        # Show only equipment associated with this Property Manager
        filtered_equipment = [eq for eq in equipment if eq.get('created_by') == username]
    else:
        # Show all equipment for Contractors/Admins
        filtered_equipment = equipment

    return render_template('dashboard.html', equipment=filtered_equipment, user=user)

@app.route('/generate', methods=['GET', 'POST'])
def generate():
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
        email = request.form['email']
        password = request.form['password']
        user = authenticate_user(email, password)
        if user:
            session['user'] = user  # store user data in session
            flash('Login successful!', 'success')
            return redirect(url_for('show_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']
        name_or_company = request.form['name_or_company']

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if user_exists(email):
            flash('An account with that email already exists.', 'warning')
            return render_template('register.html')

        create_user(username=email, password=password, role=role, company=name_or_company)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user' not in session or session['user']['role'] != 'Admin':
        flash("Access restricted to Admins only.", "danger")
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/users')
def manage_users():
    if 'user' not in session or session['user']['role'] != 'Admin':
        return abort(403)
    return render_template('manage_users.html')

@app.route('/admin/clients')
def manage_clients():
    if 'user' not in session or session['user']['role'] != 'Admin':
        return abort(403)
    return render_template('manage_clients.html')

@app.route('/admin/reports')
def admin_reports():
    if 'user' not in session or session['user']['role'] != 'Admin':
        return abort(403)
    return render_template('admin_reports.html')

@app.route('/admin/alerts')
def admin_alerts():
    if 'user' not in session or session['user']['role'] != 'Admin':
        return abort(403)
    return render_template('admin_alerts.html')

if __name__ == '__main__':
    app.run(debug=True)