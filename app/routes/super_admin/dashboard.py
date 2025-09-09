# 📍 app/routes/super_admin/dashboard.py

# app/routes/super_admin/dashboard.py
from flask import render_template, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from app.decorators import super_admin_required
from app.routes.super_admin import super_admin_bp
from app.models import db
from app.models.client.client import Client
from app.models.core.user import User
from app.models.core.role import Role
from app.models.audit.profile_change_log import ProfileChangeLog
from app.models.client.agm import AGM
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.models.contractor.contractor_compliance_document import ContractorComplianceDocument

# 🔢 NEW: signature status metrics (re-exported from app/service/contract/__init__.py)
from app.services.contract import signature_status_metrics


@super_admin_bp.route('/dashboard', endpoint='dashboard')
@super_admin_required
@login_required
def dashboard():
    now = datetime.utcnow()
    today = now.date()
    next_30_days = today + timedelta(days=30)

    # 🔎 Consistent tenant scoping
    clients_q = Client.query
    # 🔧 EXPLICIT onclause fixes AmbiguousForeignKeysError
    users_q = db.session.query(User).outerjoin(Role, User.role_id == Role.id)

    if current_user.company_id:
        clients_q = clients_q.filter(Client.company_id == current_user.company_id)
        users_q = users_q.filter(User.company_id == current_user.company_id)

    clients = clients_q.order_by(Client.name.asc()).all()
    users = users_q.all()

    managers = [u for u in users if u.role and u.role.name == "Property Manager"]
    contractor_users = [u for u in users if u.role and u.role.name == "Contractor"]

    total_portfolio_value = sum(c.contract_value or 0 for c in clients)

    client_ids = [c.id for c in clients]
    upcoming_agm_count = (AGM.query.filter(AGM.client_id.in_(client_ids),
                                           AGM.meeting_date >= now).count()
                          if client_ids else 0)

    client_compliance_docs = (
        ClientComplianceDocument.query
        .filter(ClientComplianceDocument.client_id.in_(client_ids))
        .order_by(ClientComplianceDocument.uploaded_at.desc())
        .limit(5).all()
        if client_ids else []
    )

    contractor_compliance_docs = (
        ContractorComplianceDocument.query
        .order_by(ContractorComplianceDocument.uploaded_at.desc())
        .limit(5).all()
    )

    expiring_client_docs = (
        ClientComplianceDocument.query.filter(
            ClientComplianceDocument.client_id.in_(client_ids),
            ClientComplianceDocument.expires_at.isnot(None),
            ClientComplianceDocument.expires_at >= today,
            ClientComplianceDocument.expires_at <= next_30_days
        ).count()
        if client_ids else 0
    )
    expiring_contractor_docs = ContractorComplianceDocument.query.filter(
        ContractorComplianceDocument.expiry_date.isnot(None),
        ContractorComplianceDocument.expiry_date >= today,
        ContractorComplianceDocument.expiry_date <= next_30_days
    ).count()
    expiring_docs_count = expiring_client_docs + expiring_contractor_docs

    REQUIRED_DOC_TYPES = ["Insurance Certificate", "Health & Safety Policy", "Tax Clearance", "Company Registration"]

    clients_missing_docs = 0
    for client in clients:
        docs = ClientComplianceDocument.query.filter_by(client_id=client.id).all()
        if any(t not in {d.document_type for d in docs} for t in REQUIRED_DOC_TYPES):
            clients_missing_docs += 1

    contractors_missing_docs = 0
    for contractor in contractor_users:
        docs = ContractorComplianceDocument.query.filter_by(contractor_id=contractor.id).all()
        if any(t not in {d.document_type for d in docs} for t in REQUIRED_DOC_TYPES):
            contractors_missing_docs += 1

    audit_logs = (ProfileChangeLog.query
                  .order_by(ProfileChangeLog.timestamp.desc())
                  .limit(5).all())

    # ✅ NEW: signature status metrics (scoped to current tenant/company)
    sign_metrics = signature_status_metrics(company_id=getattr(current_user, "company_id", None))

    return render_template(
        "super_admin/dashboard.html",
        clients=clients,
        users=users,
        managers=managers,
        contractor_users=contractor_users,
        total_portfolio_value=total_portfolio_value,
        upcoming_agm_count=upcoming_agm_count,
        expiring_docs_count=expiring_docs_count,
        client_compliance_docs=client_compliance_docs,
        contractor_compliance_docs=contractor_compliance_docs,
        clients_missing_docs=clients_missing_docs,
        contractors_missing_docs=contractors_missing_docs,
        gar_flagged_count=0,
        audit_logs=audit_logs,
        sign_metrics=sign_metrics,   # ← NEW in context
        current_app=current_app
    )
