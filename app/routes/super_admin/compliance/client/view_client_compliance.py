# 📍 File: app/routes/director/compliance.py

from flask import Blueprint, render_template
from flask_login import login_required
from datetime import datetime

from app.models.client import Client
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.decorators import director_required

director_bp = Blueprint('director', __name__)

@director_bp.route('/client/<int:client_id>/compliance', methods=['GET'], endpoint='view_client_compliance')
@login_required
@director_required
def view_client_compliance(client_id):
    client = Client.query.get_or_404(client_id)
    documents = (
        ClientComplianceDocument.query
        .filter_by(client_id=client.id)
        .order_by(ClientComplianceDocument.expiry_date)
        .all()
    )
    current_date = datetime.utcnow().date()
    return render_template(
        'director/client_compliance_public_view.html',
        client=client,
        documents=documents,
        current_date=current_date
    )
