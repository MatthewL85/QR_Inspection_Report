# app/routes/super_admin/dashboard.py
from __future__ import annotations

from flask import render_template, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date

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
from app.models.contracts import ClientContract  # for portfolio + expiry

from app.services.contract import signature_status_metrics  # existing util


@super_admin_bp.route('/dashboard', endpoint='dashboard')
@super_admin_required
@login_required
def dashboard():
    now = datetime.utcnow()
    today: date = now.date()
    next_30_days = today + timedelta(days=30)

    # ---- boundaries for expiry buckets ----
    in_30 = today + timedelta(days=30)
    in_60 = today + timedelta(days=60)   # NEW
    in_90 = today + timedelta(days=90)

    # ---------- tenant scoping ----------
    company_id = getattr(current_user, "company_id", None)

    clients_q = Client.query
    users_q = db.session.query(User).outerjoin(Role, User.role_id == Role.id)
    if company_id:
        clients_q = clients_q.filter(Client.company_id == company_id)
        users_q = users_q.filter(User.company_id == company_id)

    clients = clients_q.order_by(Client.name.asc()).all()
    users = users_q.all()

    managers = [u for u in users if u.role and u.role.name == "Property Manager"]
    contractor_users = [u for u in users if u.role and u.role.name == "Contractor"]

    # ---------- Managed portfolio ----------
    portfolio_q = (
        db.session.query(db.func.coalesce(db.func.sum(ClientContract.contract_value), 0.0))
        .select_from(ClientContract)
        .join(Client, Client.id == ClientContract.client_id)
    )
    if company_id:
        portfolio_q = portfolio_q.filter(Client.company_id == company_id)
    managed_portfolio_value = portfolio_q.scalar() or 0.0

    # ---------- expiry KPIs for contracts tile ----------
    expiry_base = db.session.query(ClientContract).join(Client, Client.id == ClientContract.client_id)
    if company_id:
        expiry_base = expiry_base.filter(Client.company_id == company_id)
    expiry_base = expiry_base.filter(ClientContract.end_date.isnot(None))

    contracts_expired = expiry_base.filter(ClientContract.end_date < today).count()
    contracts_expiring_30 = expiry_base.filter(
        ClientContract.end_date >= today, ClientContract.end_date <= in_30
    ).count()
    contracts_expiring_60 = expiry_base.filter(                      # NEW
        ClientContract.end_date > in_30, ClientContract.end_date <= in_60
    ).count()
    contracts_expiring_90 = expiry_base.filter(
        ClientContract.end_date > in_60, ClientContract.end_date <= in_90
    ).count()

    # ---------- compliance & agm ----------
    client_ids = [c.id for c in clients]
    upcoming_agm_count = (
        AGM.query.filter(AGM.client_id.in_(client_ids), AGM.meeting_date >= now).count()
        if client_ids else 0
    )

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

    audit_logs = (
        ProfileChangeLog.query
        .order_by(ProfileChangeLog.timestamp.desc())
        .limit(5).all()
    )

    # ---------- signature metrics (kept; harmless if not rendered) ----------
    sign_metrics = signature_status_metrics(company_id=company_id)

    # ---------- render ----------
    return render_template(
        "super_admin/dashboard.html",
        # KPIs expected by template
        total_clients=len(clients),
        total_pms=len(managers),
        total_contractors=len(contractor_users),
        managed_portfolio_value=managed_portfolio_value,
        contracts_expired=contracts_expired,
        contracts_expiring_30=contracts_expiring_30,
        contracts_expiring_60=contracts_expiring_60,   # NEW
        contracts_expiring_90=contracts_expiring_90,

        # original context used by other tiles/sections
        clients=clients,
        users=users,
        managers=managers,
        contractor_users=contractor_users,
        upcoming_agm_count=upcoming_agm_count,
        expiring_docs_count=expiring_docs_count,
        client_compliance_docs=client_compliance_docs,
        contractor_compliance_docs=contractor_compliance_docs,
        clients_missing_docs=clients_missing_docs,
        contractors_missing_docs=contractors_missing_docs,
        gar_flagged_count=0,
        audit_logs=audit_logs,
        sign_metrics=sign_metrics,
        current_app=current_app,
    )
