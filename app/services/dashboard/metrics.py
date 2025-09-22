# app/services/dashboard/metrics.py
from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional

from app.models import db
from app.models.client.client import Client
from app.models.core.user import User
from app.models.core.role import Role
from app.models.client.agm import AGM
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.models.contractor.contractor_compliance_document import ContractorComplianceDocument
from app.models.contracts import ClientContract
from app.services.contract import signature_status_metrics


def _scoped_clients_q(company_id: Optional[int]):
    q = Client.query
    if company_id:
        q = q.filter(Client.company_id == company_id)
    return q


def _scoped_users_q(company_id: Optional[int]):
    q = db.session.query(User).outerjoin(Role, User.role_id == Role.id)
    if company_id:
        q = q.filter(User.company_id == company_id)
    return q


def _scoped_contracts_q(company_id: Optional[int]):
    q = db.session.query(ClientContract).join(Client, Client.id == ClientContract.client_id)
    if company_id:
        q = q.filter(Client.company_id == company_id)
    return q


def get_dashboard_metrics(*, company_id: Optional[int]) -> Dict[str, Any]:
    """
    Returns a tenant-scoped, JSON-serializable dict of all dashboard KPIs.
    Safe to use for API and server-rendered pages.
    """
    now = datetime.utcnow()
    today: date = now.date()

    in_30 = today + timedelta(days=30)
    in_60 = today + timedelta(days=60)
    in_90 = today + timedelta(days=90)
    next_30_days = today + timedelta(days=30)

    # ---- base queries ----
    clients_q = _scoped_clients_q(company_id)
    users_q = _scoped_users_q(company_id)
    contracts_q = _scoped_contracts_q(company_id)

    clients = clients_q.all()
    users = users_q.all()

    managers = [u for u in users if u.role and u.role.name == "Property Manager"]
    contractors = [u for u in users if u.role and u.role.name == "Contractor"]

    # ---- portfolio ----
    portfolio_value = (
        db.session.query(db.func.coalesce(db.func.sum(ClientContract.contract_value), 0.0))
        .select_from(ClientContract)
        .join(Client, Client.id == ClientContract.client_id)
        .filter(*( [Client.company_id == company_id] if company_id else [] ))
        .scalar()
        or 0.0
    )

    # ---- expiries ----
    expiry_base = contracts_q.filter(ClientContract.end_date.isnot(None))
    exp_expired = expiry_base.filter(ClientContract.end_date < today).count()
    exp_30 = expiry_base.filter(ClientContract.end_date >= today, ClientContract.end_date <= in_30).count()
    exp_60 = expiry_base.filter(ClientContract.end_date > in_30, ClientContract.end_date <= in_60).count()
    exp_90 = expiry_base.filter(ClientContract.end_date > in_60, ClientContract.end_date <= in_90).count()

    # ---- AGMs / compliance ----
    client_ids = [c.id for c in clients]
    upcoming_agm = (
        AGM.query.filter(AGM.client_id.in_(client_ids), AGM.meeting_date >= now).count()
        if client_ids else 0
    )

    client_docs_recent = (
        ClientComplianceDocument.query
        .filter(ClientComplianceDocument.client_id.in_(client_ids))
        .order_by(ClientComplianceDocument.uploaded_at.desc())
        .limit(5).all()
        if client_ids else []
    )
    contractor_docs_recent = (
        ContractorComplianceDocument.query
        .order_by(ContractorComplianceDocument.uploaded_at.desc())
        .limit(5).all()
    )

    exp_client_docs = (
        ClientComplianceDocument.query.filter(
            ClientComplianceDocument.client_id.in_(client_ids),
            ClientComplianceDocument.expires_at.isnot(None),
            ClientComplianceDocument.expires_at >= today,
            ClientComplianceDocument.expires_at <= next_30_days
        ).count()
        if client_ids else 0
    )
    exp_contractor_docs = ContractorComplianceDocument.query.filter(
        ContractorComplianceDocument.expiry_date.isnot(None),
        ContractorComplianceDocument.expiry_date >= today,
        ContractorComplianceDocument.expiry_date <= next_30_days
    ).count()
    expiring_docs = exp_client_docs + exp_contractor_docs

    REQUIRED = {"Insurance Certificate", "Health & Safety Policy", "Tax Clearance", "Company Registration"}

    missing_client_docs = 0
    for c in clients:
        docs = ClientComplianceDocument.query.filter_by(client_id=c.id).all()
        have = {d.document_type for d in docs}
        if any(req not in have for req in REQUIRED):
            missing_client_docs += 1

    missing_contractor_docs = 0
    for u in contractors:
        docs = ContractorComplianceDocument.query.filter_by(contractor_id=u.id).all()
        have = {d.document_type for d in docs}
        if any(req not in have for req in REQUIRED):
            missing_contractor_docs += 1

    # ---- signature metrics ----
    sig_metrics = signature_status_metrics(company_id=company_id)

    return {
        "meta": {
            "generated_at": now.isoformat(),
            "company_id": company_id,
        },
        "counts": {
            "clients": len(clients),
            "property_managers": len(managers),
            "contractors": len(contractors),
            "portfolio_value": float(portfolio_value),
            "contracts": {
                "expired": exp_expired,
                "expiring_30": exp_30,
                "expiring_60": exp_60,
                "expiring_90": exp_90,
            },
            "agms_upcoming": upcoming_agm,
            "docs_expiring_30d": expiring_docs,
            "clients_missing_docs": missing_client_docs,
            "contractors_missing_docs": missing_contractor_docs,
            "signature_status": {
                # passthrough; ensure default keys exist
                "Draft": int(sig_metrics.get("Draft", 0)),
                "Sent": int(sig_metrics.get("Sent", 0)),
                "Signed": int(sig_metrics.get("Signed", 0)),
                "Declined": int(sig_metrics.get("Declined", 0)),
                "Expired": int(sig_metrics.get("Expired", 0)),
            },
        },
        # Optional: first-page previews for lists (you can remove if not needed)
        "previews": {
            "client_docs_recent": [d.as_dict() if hasattr(d, "as_dict") else {"id": d.id, "document_type": d.document_type} for d in client_docs_recent],
            "contractor_docs_recent": [d.as_dict() if hasattr(d, "as_dict") else {"id": d.id, "document_type": d.document_type} for d in contractor_docs_recent],
        }
    }
