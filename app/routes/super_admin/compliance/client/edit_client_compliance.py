# ✅ app/routes/super_admin/edit_client_compliance.py

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

@super_admin_bp.route('/edit-client-compliance/<int:doc_id>', methods=['GET', 'POST'], endpoint='edit_client_compliance_document')
@super_admin_required
def edit_client_compliance_document(doc_id):
    document = ClientComplianceDocument.query.get_or_404(doc_id)
    clients = Client.query.order_by(Client.name.asc()).all()

    if request.method == 'POST':
        document_name = request.form.get('document_name')
        document_type = request.form.get('document_type')
        client_id = request.form.get('client_id')
        expiry_date_str = request.form.get('expiry_date')
        is_required = bool(request.form.get('is_required'))
        reviewed_by_ai = bool(request.form.get('ai_reviewed'))
        new_files = request.files.getlist('files[]')

        if not document_name or not document_type or not client_id or not expiry_date_str:
            flash('All fields are required.', 'danger')
            return redirect(request.url)

        document.document_name = document_name
        document.document_type = document_type
        document.client_id = client_id
        document.expires_at = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        document.is_required_for_work_order = is_required
        document.reviewed_by_ai = reviewed_by_ai
        document.ai_status = 'Reviewed' if reviewed_by_ai else 'Parsed'
        document.ai_parsed_at = datetime.utcnow() if reviewed_by_ai else None

        os.makedirs(os.path.join(current_app.root_path, UPLOAD_FOLDER), exist_ok=True)

        # Optional file replacement
        if new_files and new_files[0].filename:
            for file in new_files:
                filename = secure_filename(file.filename)
                relative_path = os.path.join(UPLOAD_FOLDER, filename)
                absolute_path = os.path.join(current_app.root_path, relative_path)
                file.save(absolute_path)

                # 🧠 Re-parse
                parsed_text, extracted_data = parse_compliance_doc(absolute_path)
                parsed_summary = extracted_data.get('summary') if extracted_data else None

                document.file_path = relative_path.replace('static/', '')
                document.parsed_text = parsed_text
                document.extracted_data = extracted_data
                document.parsed_summary = parsed_summary

        db.session.commit()
        flash('Client compliance document updated successfully.', 'success')
        return redirect(url_for('super_admin.compliance_documents'))

    return render_template(
        'super_admin/edit_client_compliance_document.html',
        document=document,
        clients=clients
    )
