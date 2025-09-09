# ✅ app/routes/super_admin/upload_client_compliance.py

import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.routes.super_admin import super_admin_bp
from app.decorators.role import super_admin_required
from app.models.client import Client
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.services.gar_parser import parse_compliance_doc  # 🧠 AI parser hook

UPLOAD_FOLDER = 'static/uploads/compliance/'

@super_admin_bp.route('/upload-client-compliance-document', methods=['GET', 'POST'], endpoint='upload_client_compliance_document')
@super_admin_required
def upload_client_compliance_document():
    clients = Client.query.order_by(Client.name.asc()).all()

    if request.method == 'POST':
        document_name = request.form.get('document_name')
        document_type = request.form.get('document_type')
        client_id = request.form.get('client_id')
        expiry_date_str = request.form.get('expiry_date')
        is_required = bool(request.form.get('is_required'))
        files = request.files.getlist('files[]')
        reviewed_by_ai = bool(request.form.get('ai_reviewed'))

        if not files or not client_id or not document_name or not document_type or not expiry_date_str:
            flash('All fields are required.', 'danger')
            return redirect(request.url)

        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()

        os.makedirs(os.path.join(current_app.root_path, UPLOAD_FOLDER), exist_ok=True)

        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                relative_path = os.path.join(UPLOAD_FOLDER, filename)
                absolute_path = os.path.join(current_app.root_path, relative_path)
                file.save(absolute_path)

                # 🧠 AI Parser Hook
                parsed_text, extracted_data = parse_compliance_doc(absolute_path)
                parsed_summary = extracted_data.get('summary') if extracted_data else None

                document = ClientComplianceDocument(
                    document_name=document_name,
                    file_path=relative_path.replace('static/', ''),
                    document_type=document_type,
                    client_id=client_id,
                    expires_at=expiry_date,
                    is_required_for_work_order=is_required,
                    uploaded_by_id=current_user.id,
                    uploaded_at=datetime.utcnow(),
                    parsed_text=parsed_text,
                    extracted_data=extracted_data,
                    parsed_summary=parsed_summary,
                    reviewed_by_ai=reviewed_by_ai,
                    ai_status='Reviewed' if reviewed_by_ai else 'Parsed',
                    ai_parsed_at=datetime.utcnow() if reviewed_by_ai else None,
                )

                db.session.add(document)

        db.session.commit()
        flash('Client compliance document(s) uploaded successfully.', 'success')
        return redirect(url_for('super_admin.compliance_documents'))

    return render_template('super_admin/upload_client_compliance_document.html', clients=clients)
