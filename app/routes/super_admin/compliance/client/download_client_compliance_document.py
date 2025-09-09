# app/routes/super_admin/download_client_compliance_document.py

import os
from flask import send_from_directory, abort, current_app
from app.routes.super_admin import super_admin_bp
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.decorators.role import super_admin_required

@super_admin_bp.route('/client-compliance-document/<int:doc_id>/download', endpoint='download_client_compliance_document')
@super_admin_required
def download_client_compliance_document(doc_id):
    document = ClientComplianceDocument.query.get_or_404(doc_id)

    # Ensure file path is safe and file exists
    file_path = document.file_path  # stored like: uploads/compliance/filename.pdf
    base_dir = os.path.join(current_app.root_path, 'static')

    full_path = os.path.join(base_dir, file_path)
    if not os.path.isfile(full_path):
        abort(404, description='File not found.')

    directory, filename = os.path.split(full_path)
    return send_from_directory(directory, filename, as_attachment=True)
