from flask import request, redirect, url_for, flash
from flask_login import login_required
from app.routes.super_admin import super_admin_bp  # ✅ This is missing
from app.decorators.role import super_admin_required
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.extensions import db



@super_admin_bp.route('/client-compliance-documents/delete-selected', methods=['POST'], endpoint='delete_selected_client_compliance')
@super_admin_required
def delete_selected_client_compliance():
    from app.extensions import db
    from app.models.client.client_compliance_document import ClientComplianceDocument

    selected_ids = request.form.getlist('selected_ids')
    
    if not selected_ids:
        flash('⚠️ No documents were selected for deletion.', 'warning')
        return redirect(url_for('super_admin.client_compliance_documents'))

    deleted_count = 0
    for doc_id in selected_ids:
        doc = ClientComplianceDocument.query.get(doc_id)
        if doc:
            db.session.delete(doc)
            deleted_count += 1

    db.session.commit()
    flash(f'🗑️ Successfully deleted {deleted_count} document(s).', 'success')
    return redirect(url_for('super_admin.client_compliance_documents'))
