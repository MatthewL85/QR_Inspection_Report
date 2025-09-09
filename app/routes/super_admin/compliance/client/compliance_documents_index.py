# app/routes/super_admin/compliance/client_compliance_documents.py

from flask import render_template, request
from datetime import datetime
from app.routes.super_admin import super_admin_bp
from app.decorators.role import super_admin_required
from app.models.client.client import Client
from app.models.client.client_compliance_document import ClientComplianceDocument
from flask_login import current_user
from sqlalchemy import or_

@super_admin_bp.route('/compliance-documents/clients', endpoint='compliance_documents_index')
@super_admin_required
def client_compliance_documents():
    search = request.args.get('search', '').strip()
    client_id = request.args.get('client_id', type=int)
    document_type = request.args.get('document_type', '').strip()
    ai_status = request.args.get('ai_status', '').strip()
    page = request.args.get('page', 1, type=int)

    query = ClientComplianceDocument.query

    if search:
        query = query.filter(
            or_(
                ClientComplianceDocument.file_name.ilike(f'%{search}%'),
                ClientComplianceDocument.description.ilike(f'%{search}%'),
                ClientComplianceDocument.parsed_summary.ilike(f'%{search}%')
            )
        )

    if document_type:
        query = query.filter_by(document_type=document_type)

    if ai_status:
        query = query.filter_by(ai_status=ai_status)

    if client_id:
        query = query.filter_by(client_id=client_id)

    documents = query.order_by(ClientComplianceDocument.uploaded_at.desc()).paginate(page=page, per_page=10)
    clients = Client.query.order_by(Client.name.asc()).all()

    all_document_types = [d[0] for d in ClientComplianceDocument.query.with_entities(ClientComplianceDocument.document_type).distinct() if d[0]]
    all_ai_statuses = [s[0] for s in ClientComplianceDocument.query.with_entities(ClientComplianceDocument.ai_status).distinct() if s[0]]
    current_date = datetime.utcnow().date()

    return render_template(
        'super_admin/compliance_documents/client/client_compliance_documents.html',
        documents=documents,
        clients=clients,
        document_types=all_document_types,
        ai_statuses=all_ai_statuses,
        current_date=current_date,
        user=current_user
    )
