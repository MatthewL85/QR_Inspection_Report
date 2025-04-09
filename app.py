from flask import Flask, render_template, request, redirect, url_for
import csv
import os
import qrcode
from datetime import datetime

app = Flask(__name__)

EQUIPMENT_CSV = 'equipment.csv'
LOG_CSV = 'inspection_logs.csv'
QR_FOLDER = 'static/qrcodes'

os.makedirs(QR_FOLDER, exist_ok=True)

def load_equipment():
    equipment = []
    if os.path.exists(EQUIPMENT_CSV):
        with open(EQUIPMENT_CSV, newline='') as csvfile:
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
        fieldnames = ['timestamp', 'equipment_id', 'inspector_pin', 'clean', 'damage', 'functional', 'notes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

@app.route('/')
def index():
    return render_template('index.html', equipment=load_equipment())

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        eq_id = request.form['id']
        name = request.form['name']
        location = request.form['location']
        model = request.form['model']
        age = request.form['age']
        last_inspection = request.form['last_inspection']

        # Save equipment
        with open(EQUIPMENT_CSV, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if os.stat(EQUIPMENT_CSV).st_size == 0:
                writer.writerow(['id', 'name', 'location', 'model', 'age', 'last_inspection'])
            writer.writerow([eq_id, name, location, model, age, last_inspection])

        # Generate QR Code
        qr_url = url_for('inspect', equipment_id=eq_id, _external=True)
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
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'equipment_id': equipment_id,
            'inspector_pin': request.form['pin'],
            'clean': request.form['clean'],
            'damage': request.form['damage'],
            'functional': request.form['functional'],
            'notes': request.form['notes']
        }
        save_inspection_log(log_data)
        return f"Inspection for {equipment['name']} saved successfully."

    return render_template('inspect.html', equipment=equipment)

if __name__ == '__main__':
    app.run(debug=True)
