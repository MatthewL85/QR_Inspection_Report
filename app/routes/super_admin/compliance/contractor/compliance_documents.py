# app/routes/super_admin/compliance/contractor_compliance_documents.py

from flask import render_template, request
from datetime import datetime
from app.routes.super_admin import super_admin_bp
from app.decorators.role import super_admin_required
from app.models.contractor.contractor import Contractor
from app.models.contractor.contractor_compliance_document import ContractorComplianceDocument
from flask_login import current_user
from sqlalchemy import or_

@super_admin_bp.route('/compliance-documents/contractors', endpoint='contractor_compliance_documents')
@super_admin_required
def contractor_compliance_documents():
    search = request.args.get('search', '').strip()
    contractor_id = request.args.get('contractor_id', type=int)
    document_type = request.args.get('document_type', '').strip()
    ai_status = request.args.get('ai_status', '').strip()
    page = request.args.get('page', 1, type=int)

    query = ContractorComplianceDocument.query

    if search:
        query = query.filter(
            or_(
                ContractorComplianceDocument.file_name.ilike(f'%{search}%'),
                ContractorComplianceDocument.description.ilike(f'%{search}%'),
                ContractorComplianceDocument.parsed_summary.ilike(f'%{search}%')
            )
        )

    if document_type:
        query = query.filter_by(document_type=document_type)

    if ai_status:
        query = query.filter_by(ai_status=ai_status)

    if contractor_id:
        query = query.filter_by(contractor_id=contractor_id)

    documents = query.order_by(ContractorComplianceDocument.uploaded_at.desc()).paginate(page=page, per_page=10)
    contractors = Contractor.query.order_by(Contractor.company_name.asc()).all()

    all_document_types = [d[0] for d in ContractorComplianceDocument.query.with_entities(ContractorComplianceDocument.document_type).distinct() if d[0]]
    all_ai_statuses = [s[0] for s in ContractorComplianceDocument.query.with_entities(ContractorComplianceDocument.ai_status).distinct() if s[0]]
    current_date = datetime.utcnow().date()

    return render_template(
        'super_admin/compliance_documents/contractor/compliance_documents.html',
        documents=documents,
        contractors=contractors,
        document_types=all_document_types,
        ai_statuses=all_ai_statuses,
        current_date=current_date,
        user=current_user
    )
