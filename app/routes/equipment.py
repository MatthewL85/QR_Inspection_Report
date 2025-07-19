import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models import Equipment, Client
import qrcode
from datetime import datetime

equipment_bp = Blueprint('equipment', __name__, url_prefix='/equipment')

UPLOAD_PHOTO_FOLDER = 'static/uploads/photos'
UPLOAD_WARRANTY_FOLDER = 'static/uploads/warranties'
QR_FOLDER = 'static/qr_codes'

@equipment_bp.route('/generate', endpoint='generate')
def generate():
    if request.method == 'POST':
        client = request.form['client']
        equipment_id = request.form['id']
        name = request.form['name']
        equipment_type = request.form['equipment_type']
        serial_number = request.form.get('serial_number')
        location = request.form.get('location')
        model = request.form.get('model')
        age = request.form.get('age')
        maintenance_frequency = request.form.get('maintenance_frequency')
        warranty_expiry = request.form.get('warranty_expiry')
        last_inspection = request.form.get('last_inspection')
        pin = request.form['pin']

        # File Handling
        photo_file = request.files.get('photo')
        warranty_file = request.files.get('warranty_document')
        photo_path = None
        warranty_path = None

        os.makedirs(os.path.join(current_app.root_path, UPLOAD_PHOTO_FOLDER, equipment_id), exist_ok=True)
        os.makedirs(os.path.join(current_app.root_path, UPLOAD_WARRANTY_FOLDER, equipment_id), exist_ok=True)
        os.makedirs(os.path.join(current_app.root_path, QR_FOLDER), exist_ok=True)

        if photo_file and photo_file.filename:
            filename = secure_filename(photo_file.filename)
            photo_path = os.path.join(UPLOAD_PHOTO_FOLDER, equipment_id, filename)
            photo_file.save(os.path.join(current_app.root_path, photo_path))

        if warranty_file and warranty_file.filename:
            filename = secure_filename(warranty_file.filename)
            warranty_path = os.path.join(UPLOAD_WARRANTY_FOLDER, equipment_id, filename)
            warranty_file.save(os.path.join(current_app.root_path, warranty_path))

        # Generate QR Code
        qr_img = qrcode.make(f"Equipment ID: {equipment_id}\nName: {name}")
        qr_filename = f"{equipment_id}.png"
        qr_path = os.path.join(QR_FOLDER, qr_filename)
        qr_img.save(os.path.join(current_app.root_path, qr_path))

        # Save to database
        new_equipment = Equipment(
            client_name=client,
            equipment_id=equipment_id,
            name=name,
            equipment_type=equipment_type,
            serial_number=serial_number,
            location=location,
            model=model,
            age=age,
            maintenance_frequency=maintenance_frequency,
            warranty_expiry=warranty_expiry,
            last_inspection=last_inspection,
            qr_code_image=qr_path,
            photo=photo_path,
            warranty_document=warranty_path,
            created_by=session.get('user_id'),
            created_at=datetime.utcnow()
        )

        db.session.add(new_equipment)
        db.session.commit()

        flash('Equipment and QR code generated successfully.', 'success')
        return redirect(url_for('equipment.generate'))

    client_names = [client.name for client in Client.query.all()]
    return render_template('equipment/generate_qr.html', client_names=client_names)
