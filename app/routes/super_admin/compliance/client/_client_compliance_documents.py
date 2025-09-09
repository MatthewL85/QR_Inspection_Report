# 📄 app/routes/super_admin/compliance/client_compliance_documents.py

from flask import render_template
from flask_login import current_user
from app.routes.super_admin import super_admin_bp
from app.decorators.role import super_admin_required
from app.models.client import Client
from app.models.client.client_compliance_document import ClientComplianceDocument
from datetime import datetime

@super_admin_bp.route('/client/<int:client_id>/compliance', methods=['GET'], endpoint='client_compliance_documents')
@super_admin_required
def client_compliance_documents(client_id):
    """
    🧭 View all compliance documents for a specific client (Super Admin view).
    This route is designed with Director Logix reuse in mind.
    
    Displays only active documents related to the selected client.
    """
    # 🏢 Get client by ID or show 404
    client = Client.query.get_or_404(client_id)

    # 📄 Fetch all active compliance documents (sorted newest first)
    documents = (
        ClientComplianceDocument.query
        .filter_by(client_id=client.id, status='active')
        .order_by(ClientComplianceDocument.uploaded_at.desc())
        .all()
    )

    # 📆 Get current date (used for expiry highlighting or countdowns)
    current_date = datetime.utcnow().date()

    # 🖥️ Render template with full context
    return render_template(
        'super_admin/client_compliance_tab.html',  # ✅ Shared template for tab view
        client=client,
        documents=documents,
        current_date=current_date,
        user=current_user
    )
