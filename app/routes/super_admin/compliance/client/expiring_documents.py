# app/routes/super_admin/compliance/client/expiring_documents.py

from flask import render_template
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.routes.super_admin import super_admin_bp
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.decorators.role import super_admin_required

@super_admin_bp.route("/compliance-documents/clients/expiring", endpoint="client_expiring_documents")
@login_required
@super_admin_required
def client_expiring_documents():
    today = datetime.utcnow().date()
    upcoming_cutoff = today + timedelta(days=30)  # ⏳ change window as needed

    expiring_docs = ClientComplianceDocument.query.filter(
        ClientComplianceDocument.expiry_date != None,
        ClientComplianceDocument.expiry_date >= today,
        ClientComplianceDocument.expiry_date <= upcoming_cutoff
    ).order_by(ClientComplianceDocument.expiry_date.asc()).all()

    return render_template(
        "super_admin/compliance_documents/client/expiring_documents.html",
        expiring_docs=expiring_docs,
        current_date=today,
        user=current_user
    )
