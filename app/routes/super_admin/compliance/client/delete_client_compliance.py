# ✅ app/routes/super_admin/compliance/delete_client_compliance.py

from flask import redirect, url_for, flash
from app.routes.super_admin import super_admin_bp
from app.extensions import db
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.decorators.role import super_admin_required

@super_admin_bp.route('/client-compliance-document/<int:doc_id>/delete', methods=['POST'], endpoint='delete_client_compliance_document')
@super_admin_required
def delete_client_compliance_document(doc_id):
    document = ClientComplianceDocument.query.get_or_404(doc_id)

    # Soft-delete by changing status, do not remove from DB
    document.status = 'archived'
    db.session.commit()

    flash('Client compliance document archived successfully.', 'success')
    return redirect(url_for('super_admin.compliance_documents'))
