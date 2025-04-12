from flask import Flask, render_template, request, redirect, url_for, send_file
import csv
import os
import qrcode
from datetime import datetime

app = Flask(__name__)

DATA_FILE = 'equipment.csv'
LOG_CSV = 'inspection_logs.csv'
QR_FOLDER = 'static/qrcodes'

os.makedirs(QR_FOLDER, exist_ok=True)

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
            return eq
    return None

def save_inspection_log(data):
    file_exists = os.path.exists(LOG_CSV)
    with open(LOG_CSV, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'equipment_id', 'name', 'company', 'inspector_pin', 'clean', 'damage', 'functional', 'notes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

    print("Inspection saved for ID:", data['equipment_id'])
    print("Log saved to:", os.path.abspath(LOG_CSV))

@app.route('/')
def index():
    return render_template('index.html', equipment=load_equipment())

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        eq_id = request.form['id']
        company = request.form['company']
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
                writer.writerow(['id', 'company', 'name', 'location', 'model', 'age', 'last_inspection', 'pin'])
            writer.writerow([eq_id, company, name, location, model, age, last_inspection, pin])

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
                'company': equipment.get('company', ''),
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
                return redirect(url_for('contractor_interface', equipment_id=equipment_id, company=name_or_company))
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
        # Collect inspection form data
        clean = request.form['clean']
        damage = request.form['damage']
        functional = request.form['functional']
        notes = request.form['notes']

        # Handle media upload
        media = request.files.get('media')
        media_filename = ''
        if media and media.filename:
            media_folder = os.path.join('static', 'uploads')
            os.makedirs(media_folder, exist_ok=True)
            media_filename = f"{equipment_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{media.filename}"
            media.save(os.path.join(media_folder, media_filename))

        # Save to inspection log
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'equipment_id': equipment_id,
            'name': equipment.get('name', ''),
            'company': equipment.get('company', ''),
            'inspector_pin': f"Property Manager: {pm_name}",
            'clean': clean,
            'damage': damage,
            'functional': functional,
            'notes': notes + (f"\nMedia: {media_filename}" if media_filename else "")
        }
        save_inspection_log(log_data)

        return render_template('inspection_success.html', equipment=equipment, media_filename=media_filename)

    return render_template('pm_interface.html', equipment=equipment, pm_name=pm_name)

@app.route('/contractor/<equipment_id>')
def contractor_interface(equipment_id):
    company = request.args.get('company')
    return render_template('contractor_interface.html', equipment=get_equipment_by_id(equipment_id), company=company)

if __name__ == '__main__':
    app.run(debug=True)
