# app/routes/super_admin/compliance_upload.py

import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.routes.super_admin import super_admin_bp
from app.decorators.role import super_admin_required
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.models.contractor.contractor import Contractor
from app.services.gar_parser import parse_compliance_doc  # 🧠 AI parser hook

UPLOAD_FOLDER = 'static/uploads/compliance/'

@super_admin_bp.route('/upload-compliance-document', methods=['GET', 'POST'], endpoint='upload_compliance_document')
@super_admin_required
def upload_compliance_document():
    contractors = Contractor.query.order_by(Contractor.full_name.asc()).all()

    if request.method == 'POST':
        document_type = request.form.get('document_type')
        contractor_id = request.form.get('contractor_id')
        expiry_date_str = request.form.get('expiry_date')
        is_required = bool(request.form.get('is_required'))
        ai_reviewed = bool(request.form.get('ai_reviewed'))
        description = request.form.get('description', '').strip()
        files = request.files.getlist('files[]')

        # 🚫 Validate required fields
        if not files or not contractor_id or not document_type or not expiry_date_str:
            flash('All required fields must be completed.', 'danger')
            return redirect(request.url)

        try:
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid expiry date format.', 'danger')
            return redirect(request.url)

        os.makedirs(os.path.join(current_app.root_path, UPLOAD_FOLDER), exist_ok=True)

        for file in files:
            if file and file.filename.strip():
                filename = secure_filename(file.filename)
                relative_path = os.path.join(UPLOAD_FOLDER, filename)
                absolute_path = os.path.join(current_app.root_path, relative_path)
                file.save(absolute_path)

                # 🧠 AI PARSER (Optional and non-blocking)
                try:
                    parsed_text, extracted_data = parse_compliance_doc(absolute_path)
                    parsed_summary = extracted_data.get('summary') if extracted_data else None
                except Exception as e:
                    parsed_text = None
                    extracted_data = None
                    parsed_summary = None
                    current_app.logger.warning(f"AI parser failed for {filename}: {str(e)}")

                doc = ClientComplianceDocument(
                    file_name=filename,
                    file_path=relative_path.replace('static/', ''),  # clean relative path
                    document_type=document_type,
                    contractor_id=contractor_id,
                    expiry_date=expiry_date,
                    is_required_for_work_order=is_required,
                    ai_status='Reviewed' if ai_reviewed else 'Pending',
                    uploaded_by_id=current_user.id,
                    uploaded_at=datetime.utcnow(),
                    description=description or None,
                    parsed_text=parsed_text,
                    extracted_data=extracted_data,
                    parsed_summary=parsed_summary
                )

                db.session.add(doc)

        db.session.commit()
        flash('Document(s) uploaded successfully.', 'success')
        return redirect(url_for('super_admin.compliance_documents'))

    return render_template('super_admin/upload_compliance_document.html', contractors=contractors)
