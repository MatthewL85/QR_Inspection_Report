# app/routes/super_admin/compliance_review.py

from flask import render_template, redirect, url_for, flash
from app.routes.super_admin import super_admin_bp
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.decorators.role import super_admin_required
from app.extensions import db
from datetime import datetime

@super_admin_bp.route('/compliance-document/<int:doc_id>/review', methods=['GET'], endpoint='review_compliance_document')
@super_admin_required
def review_compliance_document(doc_id):
    document = ClientComplianceDocument.query.get_or_404(doc_id)
    return render_template('super_admin/review_compliance_document.html', document=document)
