"""Source-backed query adapters for GAR inquiries."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from sqlalchemy import and_, or_

from app.extensions import db
from app.models.capex.capex_projects import CapexProject
from app.models.capex.capex_request import CapexRequest
from app.models.client.agm import AGM
from app.models.contracts import ClientContract
from app.models.client.client import Client
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.models.core.document import Document
from app.models.core.media_file import MediaFile
from app.models.core.user import User
from app.models.exports.exported_file_log import ExportedFileLog
from app.models.members.unit import Unit
from app.models.members.unit_membership import UnitMembership
from app.services.core.notification_feed import (
    NotificationFilters,
    build_notification_context,
    notification_feed_payload,
)
from app.services.contract.renewal_alerts import renewal_bucket
from app.services.works.workflow_service import (
    WorksFilters,
    build_command_centre,
    works_command_centre_payload,
)


ROLE_ALIASES = {
    "assigned_assistant": "assistant",
    "assistant_manager_cover": "assistant",
    "assistant_manager": "assistant",
    "master_assistant": "assistant",
    "financial_controller": "finance",
    "director_governance": "director",
}

WORKS_QUALITY_MANAGEMENT_ROLES = {
    "super_admin",
    "admin",
    "property_manager",
    "assistant",
}


def _normalise_role_context(role_context: str | None) -> str:
    role = (role_context or "").strip().lower().replace(" ", "_").replace("-", "_")
    return ROLE_ALIASES.get(role, role)


def _compact_work_item(item: dict) -> dict:
    return {
        "id": item.get("id"),
        "reference": item.get("reference"),
        "title": item.get("title"),
        "status": item.get("status"),
        "client": item.get("client"),
        "unit": item.get("unit"),
        "contractor": item.get("contractor"),
        "link": item.get("links", {}).get("review") if isinstance(item.get("links"), dict) else None,
        "completion_evidence": item.get("completion_evidence"),
        "gar_relevant_history": item.get("gar_relevant_history"),
    }


def _normalise_text(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _member_name(member) -> str:
    if not member:
        return ""
    full_name = (getattr(member, "full_name", None) or "").strip()
    if full_name:
        return full_name
    return " ".join(
        part for part in (
            getattr(member, "first_name", None),
            getattr(member, "last_name", None),
        )
        if part
    ).strip()


def _client_score(client: Client, question_text: str) -> int:
    candidates = [
        client.name,
        client.property_name,
        client.client_code,
        client.address,
        client.address_line1,
        client.city,
    ]
    score = 0
    for candidate in candidates:
        normalised = _normalise_text(candidate)
        if not normalised:
            continue
        if normalised in question_text:
            score += 20
        score += sum(1 for token in normalised.split() if token and token in question_text)
    return score


def _find_client_for_question(
    *,
    company_id: int,
    allowed_client_ids: tuple[int, ...] | None,
    question: str,
) -> Client | None:
    query = Client.query.filter(Client.company_id == company_id)
    if allowed_client_ids is not None:
        query = query.filter(Client.id.in_(allowed_client_ids))
    clients = query.order_by(Client.name.asc()).all()
    if not clients:
        return None

    question_text = _normalise_text(question)
    if not question_text:
        return clients[0] if len(clients) == 1 else None

    scored = sorted(
        ((_client_score(client, question_text), client) for client in clients),
        key=lambda item: (-item[0], item[1].name or ""),
    )
    return scored[0][1] if scored and scored[0][0] > 0 else (clients[0] if len(clients) == 1 else None)


def _unit_label(unit: Unit) -> str:
    return unit.unit_name or unit.unit_label or unit.unit_number or f"Unit {unit.id}"


def _current_links(unit: Unit, roles: tuple[str, ...]) -> list[UnitMembership]:
    return (
        unit.membership_links
        .filter(
            UnitMembership.role.in_(roles),
            UnitMembership.is_current.is_(True),
        )
        .all()
    )


def _compact_unit_item(unit: Unit, *, include_names: bool) -> dict:
    owner_links = _current_links(unit, ("owner",))
    resident_links = _current_links(unit, ("resident", "tenant"))
    item = {
        "id": unit.id,
        "label": _unit_label(unit),
        "unit_number": unit.unit_number,
        "unit_type": unit.unit_type,
        "unit_category": unit.unit_category,
        "block": unit.block_name,
        "core": unit.core_name,
        "area": unit.area_name,
        "status": unit.status,
        "occupancy_status": unit.occupancy_status or "unknown",
        "owner_count": len(owner_links),
        "resident_count": len(resident_links),
        "gar_chat_ready": bool(unit.gar_chat_ready),
    }
    if include_names:
        item["owners"] = [_member_name(link.member) for link in owner_links if _member_name(link.member)]
        item["residents"] = [_member_name(link.member) for link in resident_links if _member_name(link.member)]
    return item


def _unit_group_key(unit: Unit) -> str:
    return unit.block_name or unit.core_name or unit.area_name or "Unassigned"


def _sort_unit(unit: Unit) -> tuple:
    label = unit.unit_number or unit.unit_label or unit.unit_name or ""
    parts = re.split(r"(\d+)", label)
    natural = tuple(int(part) if part.isdigit() else part.lower() for part in parts)
    return (_unit_group_key(unit).lower(), natural)


def _contract_title(contract: ClientContract) -> str:
    return (
        getattr(contract, "contract_title", None)
        or contract.get_json("meta.contract_title", None)
        or f"Contract #{contract.id}"
    )


def _contract_status(contract: ClientContract) -> str:
    return contract.sign_status or "Draft"


def _is_archived_contract(contract: ClientContract) -> bool:
    return _contract_status(contract).strip().lower() == "archived"


def _compact_contract_item(contract: ClientContract) -> dict:
    bucket, days = renewal_bucket(contract.end_date)
    client = contract.client
    return {
        "id": contract.id,
        "title": _contract_title(contract),
        "client": client.name if client else "-",
        "property": client.property_name if client else "-",
        "status": _contract_status(contract),
        "start_date": contract.start_date.isoformat() if contract.start_date else None,
        "end_date": contract.end_date.isoformat() if contract.end_date else None,
        "days_to_expiry": days,
        "alert_bucket": bucket or "active",
        "contract_value": float(contract.contract_value or 0),
        "currency": contract.currency or (client.currency if client else "EUR") or "EUR",
        "renewal_month": contract.renewal_month,
        "next_fee_increase_date": contract.next_fee_increase_date.isoformat() if contract.next_fee_increase_date else None,
        "new_contract_drafted": bool(contract.new_contract_drafted),
        "alert_owner": contract.alert_owner.full_name if contract.alert_owner else None,
        "gar_contract_risk_level": contract.gar_contract_risk_level,
        "gar_contract_recommendation": contract.gar_contract_recommendation,
        "link": f"/super-admin/contracts/renew/{contract.client_id}?step=3&contract_id={contract.id}",
    }


def _role_name(user: User) -> str:
    return getattr(getattr(user, "role", None), "name", None) or "Unassigned"


def _compact_team_member(user: User) -> dict:
    pm_clients = len(getattr(user, "assigned_clients", []) or [])
    fc_clients = len(getattr(user, "assigned_fc_clients", []) or [])
    assistant_clients = len(getattr(user, "assigned_assistant_clients", []) or [])
    return {
        "id": user.id,
        "full_name": user.full_name,
        "role": _role_name(user),
        "email": user.email,
        "username": user.username,
        "company": user.company.name if user.company else "-",
        "contact": {
            "mobile": user.mobile_phone,
            "direct_line": user.direct_phone,
            "extension": user.phone_extension,
        },
        "status": "Active" if user.is_active else "Inactive",
        "email_verified": bool(user.email_verified),
        "two_factor_enabled": bool(user.two_factor_enabled),
        "assigned_clients": {
            "property_manager": pm_clients,
            "financial_controller": fc_clients,
            "assistant": assistant_clients,
            "total": pm_clients + fc_clients + assistant_clients,
        },
        "gar_chat_ready": bool(user.gar_chat_ready),
    }


def build_team_source_query(
    *,
    company_id: int | None,
    role_context: str,
    allowed_client_ids: tuple[int, ...] | None = None,
    question: str = "",
) -> dict:
    """Build a source-backed Team Manager query result for GAR."""
    if not company_id:
        return {
            "context_type": "gar_team_source_query",
            "query_ready": False,
            "error": "company_context_missing",
            "source_references": [],
        }

    query = (
        User.query
        .filter(User.company_id == company_id)
        .filter(User.deleted_at.is_(None))
        .order_by(User.full_name.asc())
    )
    users = query.all()
    active_users = [user for user in users if user.is_active]
    inactive_users = [user for user in users if not user.is_active]
    role_counts: dict[str, int] = {}
    active_role_counts: dict[str, int] = {}
    for user in users:
        role = _role_name(user)
        role_counts[role] = role_counts.get(role, 0) + 1
        if user.is_active:
            active_role_counts[role] = active_role_counts.get(role, 0) + 1

    clients_query = Client.query.filter(Client.company_id == company_id)
    if allowed_client_ids is not None:
        clients_query = clients_query.filter(Client.id.in_(allowed_client_ids))
    clients = clients_query.all()
    assignment_gaps = [
        {
            "client_id": client.id,
            "client": client.name,
            "missing": [
                label for label, value in (
                    ("property_manager", client.assigned_pm_id),
                    ("financial_controller", client.assigned_fc_id),
                    ("assistant", client.assigned_assistant_id),
                )
                if not value
            ],
        }
        for client in clients
        if not client.assigned_pm_id or not client.assigned_fc_id or not client.assigned_assistant_id
    ]

    safe_summary = (
        f"Team Manager source query found {len(active_users)} active user(s), "
        f"{len(inactive_users)} inactive user(s), and {len(assignment_gaps)} client assignment gap(s) "
        f"in this company scope."
    )

    return {
        "context_type": "gar_team_source_query",
        "query_ready": True,
        "question": question or "",
        "role_context": role_context,
        "safe_summary": safe_summary,
        "stats": {
            "active_users": len(active_users),
            "inactive_users": len(inactive_users),
            "total_users": len(users),
            "roles": role_counts,
            "active_roles": active_role_counts,
            "client_assignment_gaps": len(assignment_gaps),
            "two_factor_enabled": len([user for user in active_users if user.two_factor_enabled]),
            "email_verified": len([user for user in active_users if user.email_verified]),
        },
        "records": {
            "active_users": [_compact_team_member(user) for user in active_users[:30]],
            "inactive_users": [_compact_team_member(user) for user in inactive_users[:15]],
            "assignment_gaps": assignment_gaps[:20],
        },
        "visibility": {
            "contact_details_included": True,
            "hr_leave_records_included": False,
            "performance_records_included": False,
            "login_hashes_or_security_secrets_included": False,
        },
        "source_references": [
            {"model": "User", "record_id": None, "fields": ["id", "full_name", "email", "role_id", "company_id", "is_active"]},
            {"model": "Role", "record_id": None, "fields": ["id", "name", "is_active"]},
            {"model": "Client", "record_id": None, "fields": ["assigned_pm_id", "assigned_fc_id", "assigned_assistant_id"]},
        ],
    }


def _date_value(value) -> date | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


def _compact_compliance_document(document: ClientComplianceDocument) -> dict:
    expires_at = _date_value(document.expires_at)
    client = document.client
    return {
        "id": document.id,
        "client_id": document.client_id,
        "client": client.name if client else "-",
        "document_name": document.document_name,
        "document_type": document.document_type,
        "status": document.status or "active",
        "expires_at": expires_at.isoformat() if expires_at else None,
        "ai_status": document.ai_status,
        "reviewed_by_human": bool(document.reviewed_by_human),
        "gar_chat_ready": bool(document.gar_chat_ready),
    }


def _compact_agm(agm: AGM) -> dict:
    client = agm.client
    return {
        "id": agm.id,
        "client_id": agm.client_id,
        "client": client.name if client else "-",
        "title": agm.meeting_title,
        "meeting_date": agm.meeting_date.isoformat() if agm.meeting_date else None,
        "location": agm.location,
        "reviewed_by_human": bool(agm.reviewed_by_human),
        "gar_chat_ready": bool(agm.gar_chat_ready),
    }


def _compact_capex_request(request: CapexRequest) -> dict:
    client = request.client
    return {
        "id": request.id,
        "client_id": request.client_id,
        "client": client.name if client else "-",
        "area": request.area,
        "status": request.status,
        "urgency": request.urgency,
        "estimated_cost": float(request.estimated_cost or 0),
        "submitted_at": request.submitted_at.isoformat() if request.submitted_at else None,
        "risk_level": request.risk_level,
        "is_gar_flagged": bool(request.is_gar_flagged),
        "gar_suggested_priority": request.gar_suggested_priority,
    }


def _compact_capex_project(project: CapexProject) -> dict:
    return {
        "id": str(project.id),
        "client_id": project.client_id,
        "client": project.client.name if project.client else "-",
        "name": project.name,
        "target_year": project.target_year,
        "cost": float(project.cost or 0),
        "priority": project.priority,
        "funding": project.funding,
        "status": project.status,
    }


def _client_governance_attention(client: Client) -> list[str]:
    attention = []
    if client.enforce_gdpr is False:
        attention.append("gdpr_not_enforced")
    if client.agm_completed is False:
        attention.append("agm_not_marked_completed")
    if client.ai_risk_level and client.ai_risk_level.strip().lower() not in {"low", "none", "green"}:
        attention.append("gar_risk_level")
    if client.ai_governance_score is not None and client.ai_governance_score < 60:
        attention.append("low_governance_score")
    if client.ai_compliance_index is not None and client.ai_compliance_index < 60:
        attention.append("low_compliance_index")
    if client.capex_status and client.capex_status.strip().lower() not in {"not_created", "created", "none"}:
        attention.append("capex_status")
    return attention


def _compact_governance_client(client: Client) -> dict:
    attention = _client_governance_attention(client)
    return {
        "id": client.id,
        "name": client.name,
        "property_name": client.property_name,
        "client_code": client.client_code,
        "agm_completed": bool(client.agm_completed),
        "last_agm_date": client.last_agm_date.isoformat() if client.last_agm_date else None,
        "financial_year_end": client.financial_year_end,
        "gdpr_enforced": bool(client.enforce_gdpr),
        "data_protection_compliance": client.data_protection_compliance,
        "gar_monitored": bool(client.is_gar_monitored),
        "gar_scores": {
            "governance": client.ai_governance_score,
            "compliance": client.ai_compliance_index,
            "health": client.ai_health_index,
            "risk_level": client.ai_risk_level,
        },
        "attention_signals": attention,
    }


def build_governance_source_query(
    *,
    company_id: int | None,
    role_context: str,
    allowed_client_ids: tuple[int, ...] | None = None,
    question: str = "",
) -> dict:
    """Build a source-backed governance/compliance query result for GAR."""
    if not company_id:
        return {
            "context_type": "gar_governance_source_query",
            "query_ready": False,
            "error": "company_context_missing",
            "source_references": [],
        }

    today = date.today()
    expiring_cutoff = today + timedelta(days=90)
    clients_query = Client.query.filter(Client.company_id == company_id)
    if allowed_client_ids is not None:
        clients_query = clients_query.filter(Client.id.in_(allowed_client_ids))
    clients = clients_query.order_by(Client.name.asc()).all()
    client_ids = [client.id for client in clients]

    documents = []
    agms = []
    capex_requests = []
    capex_projects = []
    if client_ids:
        documents = (
            ClientComplianceDocument.query
            .filter(ClientComplianceDocument.client_id.in_(client_ids))
            .filter(ClientComplianceDocument.status != "archived")
            .order_by(ClientComplianceDocument.expires_at.asc().nulls_last(), ClientComplianceDocument.uploaded_at.desc())
            .all()
        )
        agms = (
            AGM.query
            .filter(AGM.client_id.in_(client_ids))
            .order_by(AGM.meeting_date.desc())
            .all()
        )
        capex_requests = (
            CapexRequest.query
            .filter(CapexRequest.client_id.in_(client_ids))
            .order_by(CapexRequest.submitted_at.desc())
            .all()
        )
        capex_projects = (
            CapexProject.query
            .filter(CapexProject.client_id.in_(client_ids))
            .order_by(CapexProject.target_year.asc().nulls_last(), CapexProject.created_at.desc())
            .all()
        )

    expired_documents = [
        document for document in documents
        if (expires_at := _date_value(document.expires_at)) and expires_at < today
    ]
    expiring_documents = [
        document for document in documents
        if (expires_at := _date_value(document.expires_at)) and today <= expires_at <= expiring_cutoff
    ]
    documents_needing_review = [
        document for document in documents
        if not document.reviewed_by_human or (document.ai_status or "").strip().lower() in {"needs review", "failed"}
    ]
    upcoming_agms = [agm for agm in agms if agm.meeting_date and agm.meeting_date >= today]
    recent_agms = [agm for agm in agms if agm.meeting_date and agm.meeting_date < today][:10]
    open_capex_statuses = {"pending", "in review", "approved", "in progress"}
    open_capex_requests = [
        request for request in capex_requests
        if (request.status or "").strip().lower() in open_capex_statuses
    ]
    critical_capex_requests = [
        request for request in capex_requests
        if (request.urgency or "").strip().lower() == "critical"
        or (request.risk_level or "").strip().lower() == "high"
        or request.is_gar_flagged
    ]
    open_capex_projects = [
        project for project in capex_projects
        if (project.status or "").strip().lower() not in {"done", "deferred", "cancelled"}
    ]
    clients_with_attention = [
        client for client in clients
        if _client_governance_attention(client)
    ]

    safe_summary = (
        f"Governance source query found {len(clients_with_attention)} development(s) with governance attention, "
        f"{len(expired_documents)} expired compliance document(s), {len(expiring_documents)} document(s) expiring within 90 days, "
        f"{len(upcoming_agms)} upcoming AGM(s), and {len(open_capex_requests)} open CAPEX request(s)."
    )

    return {
        "context_type": "gar_governance_source_query",
        "query_ready": True,
        "question": question or "",
        "role_context": role_context,
        "safe_summary": safe_summary,
        "stats": {
            "clients_in_scope": len(clients),
            "clients_with_attention": len(clients_with_attention),
            "compliance_documents": len(documents),
            "expired_compliance_documents": len(expired_documents),
            "expiring_90_day_compliance_documents": len(expiring_documents),
            "documents_needing_review": len(documents_needing_review),
            "upcoming_agms": len(upcoming_agms),
            "recent_agms": len(recent_agms),
            "open_capex_requests": len(open_capex_requests),
            "critical_capex_requests": len(critical_capex_requests),
            "open_capex_projects": len(open_capex_projects),
        },
        "records": {
            "clients_with_attention": [_compact_governance_client(client) for client in clients_with_attention[:20]],
            "expired_compliance_documents": [_compact_compliance_document(document) for document in expired_documents[:15]],
            "expiring_compliance_documents": [_compact_compliance_document(document) for document in expiring_documents[:15]],
            "documents_needing_review": [_compact_compliance_document(document) for document in documents_needing_review[:15]],
            "upcoming_agms": [_compact_agm(agm) for agm in upcoming_agms[:10]],
            "recent_agms": [_compact_agm(agm) for agm in recent_agms[:10]],
            "open_capex_requests": [_compact_capex_request(request) for request in open_capex_requests[:15]],
            "critical_capex_requests": [_compact_capex_request(request) for request in critical_capex_requests[:10]],
            "open_capex_projects": [_compact_capex_project(project) for project in open_capex_projects[:15]],
        },
        "visibility": {
            "document_text_extraction_included": False,
            "director_appointment_scope_included": False,
            "finance_ledger_values_included": False,
            "owner_resident_private_data_included": False,
        },
        "source_references": [
            {"model": "Client", "record_id": None, "fields": ["agm_completed", "last_agm_date", "ai_governance_score", "ai_compliance_index", "ai_risk_level"]},
            {"model": "ClientComplianceDocument", "record_id": None, "fields": ["client_id", "document_name", "status", "expires_at", "reviewed_by_human", "ai_status"]},
            {"model": "AGM", "record_id": None, "fields": ["client_id", "meeting_title", "meeting_date", "reviewed_by_human"]},
            {"model": "CapexRequest", "record_id": None, "fields": ["client_id", "status", "urgency", "estimated_cost", "risk_level", "is_gar_flagged"]},
            {"model": "CapexProject", "record_id": None, "fields": ["client_id", "name", "target_year", "priority", "status", "cost"]},
        ],
    }


def _compact_document(document: Document, *, include_linkage: bool) -> dict:
    expires_at = _date_value(document.expires_at)
    item = {
        "id": document.id,
        "file_name": document.file_name,
        "file_type": document.file_type,
        "category": document.category,
        "compliance_category": document.compliance_category,
        "version": document.version,
        "is_current_version": bool(document.is_current_version),
        "access_scope": document.access_scope,
        "upload_date": document.upload_date.isoformat() if document.upload_date else None,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "renewal_required": bool(document.renewal_required),
        "requires_manual_review": bool(document.requires_manual_review),
        "parsing_status": document.parsing_status,
        "is_ai_processed": bool(document.is_ai_processed),
        "gar_chat_ready": bool(document.gar_chat_ready),
    }
    if include_linkage:
        item["linked_client_id"] = document.linked_client_id
        item["unit_id"] = document.unit_id
    return item


def _compact_media_file(media: MediaFile, *, include_linkage: bool) -> dict:
    expires_at = _date_value(media.expires_at)
    item = {
        "id": media.id,
        "filename": media.filename,
        "file_type": media.file_type,
        "description": media.description,
        "visibility": media.visibility,
        "upload_date": media.upload_date.isoformat() if media.upload_date else None,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "parsing_status": media.parsing_status,
        "is_ai_processed": bool(media.is_ai_processed),
        "ai_classification": media.ai_classification,
        "ai_confidence_score": media.ai_confidence_score,
        "tags": media.tags,
    }
    if include_linkage:
        item["related_table"] = media.related_table
        item["related_id"] = media.related_id
    return item


def _compact_exported_file(export: ExportedFileLog, *, include_sensitive_flags: bool) -> dict:
    item = {
        "id": export.id,
        "export_type": export.export_type,
        "related_model": export.related_model,
        "file_format": export.file_format,
        "file_name": export.file_name,
        "visibility_scope": export.visibility_scope,
        "client_id": export.client_id,
        "unit_id": export.unit_id,
        "exported_at": export.exported_at.isoformat() if export.exported_at else None,
        "flagged_by_gar": bool(export.flagged_by_gar),
        "gar_context_reference": export.gar_context_reference,
    }
    if include_sensitive_flags:
        item["is_sensitive"] = bool(export.is_sensitive)
        item["redacted_for_public"] = bool(export.redacted_for_public)
    return item


def build_document_source_query(
    *,
    company_id: int | None,
    role_context: str,
    allowed_client_ids: tuple[int, ...] | None = None,
    question: str = "",
) -> dict:
    """Build a source-backed document metadata query result for GAR."""
    if not company_id:
        return {
            "context_type": "gar_document_source_query",
            "query_ready": False,
            "error": "company_context_missing",
            "source_references": [],
        }

    today = date.today()
    expiring_cutoff = today + timedelta(days=90)
    clients_query = Client.query.filter(Client.company_id == company_id)
    if allowed_client_ids is not None:
        clients_query = clients_query.filter(Client.id.in_(allowed_client_ids))
    client_ids = [client.id for client in clients_query.all()]
    unit_ids = []
    if client_ids:
        unit_ids = [
            row[0]
            for row in db.session.query(Unit.id)
            .filter(Unit.client_id.in_(client_ids))
            .all()
        ]

    documents = []
    compliance_documents = []
    exports = []
    media_files = []
    if client_ids:
        document_filters = [Document.linked_client_id.in_(client_ids)]
        if unit_ids:
            document_filters.append(Document.unit_id.in_(unit_ids))
        documents = (
            Document.query
            .filter(or_(*document_filters))
            .order_by(Document.expires_at.asc().nulls_last(), Document.upload_date.desc())
            .all()
        )
        compliance_documents = (
            ClientComplianceDocument.query
            .filter(ClientComplianceDocument.client_id.in_(client_ids))
            .filter(ClientComplianceDocument.status != "archived")
            .order_by(ClientComplianceDocument.expires_at.asc().nulls_last(), ClientComplianceDocument.uploaded_at.desc())
            .all()
        )
        export_query = ExportedFileLog.query.filter(ExportedFileLog.client_id.in_(client_ids))
        if role_context not in {"super_admin", "admin", "property_manager", "assistant", "finance"}:
            export_query = export_query.filter(ExportedFileLog.is_sensitive.is_(False))
        exports = export_query.order_by(ExportedFileLog.exported_at.desc()).all()

    media_filters = []
    if client_ids:
        media_filters.append(and_(MediaFile.related_table.in_(("client", "clients")), MediaFile.related_id.in_(client_ids)))
    if unit_ids:
        media_filters.append(and_(MediaFile.related_table.in_(("unit", "units")), MediaFile.related_id.in_(unit_ids)))
    if media_filters:
        media_files = (
            MediaFile.query
            .filter(or_(*media_filters))
            .order_by(MediaFile.expires_at.asc().nulls_last(), MediaFile.upload_date.desc())
            .all()
        )

    all_expiring = []
    all_expired = []
    all_review = []
    for item in documents + compliance_documents + media_files:
        expires_at = _date_value(getattr(item, "expires_at", None))
        if expires_at and expires_at < today:
            all_expired.append(item)
        elif expires_at and today <= expires_at <= expiring_cutoff:
            all_expiring.append(item)

    all_review.extend([
        document for document in documents
        if document.requires_manual_review or (document.parsing_status or "").strip().lower() in {"failed", "needs review"}
    ])
    all_review.extend([
        document for document in compliance_documents
        if not document.reviewed_by_human or (document.ai_status or "").strip().lower() in {"failed", "needs review"}
    ])
    all_review.extend([
        media for media in media_files
        if (media.parsing_status or "").strip().lower() in {"failed", "needs review"}
    ])

    management_roles = {"super_admin", "admin", "property_manager", "assistant", "finance", "director"}
    include_records = role_context in management_roles
    include_linkage = role_context in management_roles
    safe_summary = (
        f"Document source query found {len(documents)} general document(s), "
        f"{len(compliance_documents)} client compliance document(s), {len(media_files)} media file(s), "
        f"and {len(exports)} exported file log(s) in this scope. "
        f"{len(all_expired)} item(s) are expired and {len(all_expiring)} item(s) expire within 90 days."
    )

    records = {}
    if include_records:
        records = {
            "general_documents": [_compact_document(document, include_linkage=include_linkage) for document in documents[:20]],
            "client_compliance_documents": [_compact_compliance_document(document) for document in compliance_documents[:20]],
            "media_files": [_compact_media_file(media, include_linkage=include_linkage) for media in media_files[:20]],
            "exported_files": [_compact_exported_file(export, include_sensitive_flags=role_context in {"super_admin", "admin"}) for export in exports[:20]],
            "items_needing_review": [
                {
                    "model": item.__class__.__name__,
                    "id": item.id,
                    "name": (
                        getattr(item, "file_name", None)
                        or getattr(item, "document_name", None)
                        or getattr(item, "filename", None)
                    ),
                }
                for item in all_review[:20]
            ],
        }

    return {
        "context_type": "gar_document_source_query",
        "query_ready": True,
        "question": question or "",
        "role_context": role_context,
        "safe_summary": safe_summary,
        "stats": {
            "clients_in_scope": len(client_ids),
            "general_documents": len(documents),
            "client_compliance_documents": len(compliance_documents),
            "media_files": len(media_files),
            "exported_file_logs": len(exports),
            "expired_items": len(all_expired),
            "expiring_90_day_items": len(all_expiring),
            "items_needing_review": len(all_review),
            "ai_processed_documents": len([document for document in documents if document.is_ai_processed]),
            "gar_ready_documents": len([document for document in documents if document.gar_chat_ready]),
            "sensitive_exports_visible": len([export for export in exports if export.is_sensitive]),
        },
        "records": records,
        "visibility": {
            "metadata_only": True,
            "file_paths_included": False,
            "document_text_extraction_included": False,
            "extracted_payloads_included": False,
            "sensitive_exports_filtered_for_external_roles": role_context not in {"super_admin", "admin", "property_manager", "assistant", "finance"},
            "records_included": include_records,
        },
        "source_references": [
            {"model": "Document", "record_id": None, "fields": ["linked_client_id", "unit_id", "category", "expires_at", "requires_manual_review", "parsing_status"]},
            {"model": "ClientComplianceDocument", "record_id": None, "fields": ["client_id", "document_name", "document_type", "status", "expires_at", "reviewed_by_human", "ai_status"]},
            {"model": "MediaFile", "record_id": None, "fields": ["related_table", "related_id", "file_type", "expires_at", "parsing_status", "ai_classification"]},
            {"model": "ExportedFileLog", "record_id": None, "fields": ["client_id", "unit_id", "export_type", "visibility_scope", "is_sensitive", "flagged_by_gar"]},
        ],
    }


def build_notification_source_query(
    *,
    user_id: int | None,
    role_context: str,
    question: str = "",
) -> dict:
    """Build a source-backed notification action queue query for GAR."""
    if not user_id:
        return {
            "context_type": "gar_notification_source_query",
            "query_ready": False,
            "error": "user_context_missing",
            "source_references": [],
        }

    context = build_notification_context(
        user_id,
        NotificationFilters(status="unread"),
        limit=100,
    )
    payload = notification_feed_payload(context)
    summary = payload.get("summary", {})
    notifications = payload.get("notifications", [])
    action_notifications = payload.get("action_queue", [])
    gar_notifications = [
        item for item in notifications
        if item.get("is_gar_related")
    ]
    high_priority = [
        item for item in notifications
        if int(item.get("priority_rank") or 0) >= 4
    ]
    source_references = payload.get("source_references") or _notification_source_references(notifications)

    safe_summary = (
        f"Notification source query found {summary.get('unread_count', 0)} unread notification(s), "
        f"{summary.get('action_count', 0)} action item(s), "
        f"{summary.get('high_priority_count', 0)} high-priority item(s), and "
        f"{summary.get('gar_count', 0)} GAR-related item(s) for this user. "
        f"{summary.get('acknowledged_count', 0)} notification(s) have been acknowledged."
    )

    return {
        "context_type": "gar_notification_source_query",
        "query_ready": True,
        "question": question or "",
        "role_context": role_context,
        "safe_summary": safe_summary,
        "stats": summary,
        "records": {
            "action_queue": action_notifications[:10],
            "high_priority": high_priority[:10],
            "gar_related": gar_notifications[:10],
            "recent_unread": notifications[:15],
        },
        "visibility": {
            "recipient_scoped": True,
            "other_users_included": False,
            "source_payloads_included": False,
            "mutating_actions_included": False,
        },
        "source_references": source_references,
    }


def _notification_source_references(notifications: list[dict]) -> list[dict]:
    fields = [
        "recipient_id",
        "message",
        "type",
        "is_read",
        "read_at",
        "priority_level",
        "gar_category",
        "suggested_action",
        "extracted_data",
    ]
    references = [
        {
            "model": "Notification",
            "record_id": None,
            "label": "Notification queue",
            "fields": fields,
        }
    ]
    seen = {("Notification", None)}

    for item in notifications:
        source = item.get("source_reference") or {}
        model = source.get("model")
        record_id = source.get("record_id")
        if not model or (model, record_id) in seen:
            continue
        seen.add((model, record_id))
        references.append(
            {
                "model": model,
                "record_id": record_id,
                "label": source.get("label") or f"{model} #{record_id}",
                "fields": [
                    "id",
                    "status",
                    "client_id",
                    "unit_id",
                    "created_at",
                    "updated_at",
                ],
                "module_key": source.get("module_key"),
                "module_label": source.get("module_label"),
                "source_field": source.get("source_field"),
                "url": source.get("url"),
            }
        )

    return references


def build_contract_source_query(
    *,
    company_id: int | None,
    role_context: str,
    allowed_client_ids: tuple[int, ...] | None = None,
    question: str = "",
) -> dict:
    """Build a source-backed Contract Manager query result for GAR."""
    if not company_id:
        return {
            "context_type": "gar_contract_source_query",
            "query_ready": False,
            "error": "company_context_missing",
            "source_references": [],
        }

    query = (
        ClientContract.query
        .join(Client, Client.id == ClientContract.client_id)
        .filter(Client.company_id == company_id)
        .order_by(ClientContract.end_date.asc(), ClientContract.created_at.desc())
    )
    if allowed_client_ids is not None:
        query = query.filter(ClientContract.client_id.in_(allowed_client_ids))

    contracts = query.all()
    active_scope_contracts = [contract for contract in contracts if not _is_archived_contract(contract)]
    archived_contracts = [contract for contract in contracts if _is_archived_contract(contract)]
    counts = {
        "expired": 0,
        "due_30": 0,
        "due_60": 0,
        "due_90": 0,
        "active": 0,
        "missing_end_date": 0,
        "archived": len(archived_contracts),
        "total_operational": len(active_scope_contracts),
    }
    for contract in active_scope_contracts:
        bucket, _days = renewal_bucket(contract.end_date)
        if bucket == "expired":
            counts["expired"] += 1
        elif bucket == "30":
            counts["due_30"] += 1
        elif bucket == "60":
            counts["due_60"] += 1
        elif bucket == "90":
            counts["due_90"] += 1
        elif contract.end_date:
            counts["active"] += 1
        else:
            counts["missing_end_date"] += 1

    attention_contracts = []
    for contract in active_scope_contracts:
        bucket, days = renewal_bucket(contract.end_date)
        if bucket in {"expired", "30", "60", "90"} or contract.gar_contract_risk_level:
            attention_contracts.append((bucket or "risk", days if days is not None else 9999, contract))
    attention_contracts.sort(key=lambda item: (item[1], item[2].client.name if item[2].client else ""))
    safe_summary = (
        f"Contract Manager source query found {counts['expired']} expired contract(s), "
        f"{counts['due_30']} due within 30 days, {counts['due_60']} due within 60 days, "
        f"{counts['due_90']} due within 90 days, and {counts['active']} active contract(s). "
        f"Archived contracts are retained but excluded from operational counts."
    )

    return {
        "context_type": "gar_contract_source_query",
        "query_ready": True,
        "question": question or "",
        "role_context": role_context,
        "safe_summary": safe_summary,
        "stats": counts,
        "records": {
            "attention_contracts": [_compact_contract_item(contract) for _bucket, _days, contract in attention_contracts[:20]],
            "active_contracts": [_compact_contract_item(contract) for contract in active_scope_contracts if renewal_bucket(contract.end_date)[0] is None and contract.end_date][:10],
        },
        "visibility": {
            "archived_in_operational_counts": False,
            "document_clause_extraction_included": False,
            "contract_documents_mutable": False,
        },
        "source_references": [
            {"model": "ClientContract", "record_id": None, "fields": ["client_id", "start_date", "end_date", "contract_value", "sign_status"]},
            {"model": "Client", "record_id": None, "fields": ["company_id", "name", "property_name"]},
            {"model": "ContractTemplateVersion", "record_id": None, "fields": ["id", "version_label"]},
        ],
    }


def build_client_unit_source_query(
    *,
    company_id: int | None,
    role_context: str,
    allowed_client_ids: tuple[int, ...] | None = None,
    question: str = "",
) -> dict:
    """Build a source-backed client/development/unit query result for GAR."""
    if not company_id:
        return {
            "context_type": "gar_client_unit_source_query",
            "query_ready": False,
            "error": "company_context_missing",
            "source_references": [],
        }

    client = _find_client_for_question(
        company_id=company_id,
        allowed_client_ids=allowed_client_ids,
        question=question,
    )
    if not client:
        return {
            "context_type": "gar_client_unit_source_query",
            "query_ready": False,
            "error": "client_scope_not_identified",
            "safe_summary": "GAR needs a specific development name or a single permitted development to summarise units.",
            "source_references": [
                {"model": "Client", "record_id": None, "fields": ["company_id", "name", "property_name"]},
            ],
        }

    units = (
        Unit.query
        .filter(Unit.client_id == client.id)
        .order_by(Unit.block_name.asc(), Unit.core_name.asc(), Unit.unit_number.asc(), Unit.unit_label.asc())
        .all()
    )
    units.sort(key=_sort_unit)
    privileged_roles = {"super_admin", "admin", "property_manager", "assistant", "finance", "director"}
    include_names = role_context in privileged_roles
    occupancy_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    block_counts: dict[str, int] = {}
    for unit in units:
        occupancy_counts[unit.occupancy_status or "unknown"] = occupancy_counts.get(unit.occupancy_status or "unknown", 0) + 1
        type_label = unit.unit_type or unit.unit_category or "Unknown"
        type_counts[type_label] = type_counts.get(type_label, 0) + 1
        group_label = _unit_group_key(unit)
        block_counts[group_label] = block_counts.get(group_label, 0) + 1

    compact_units = [_compact_unit_item(unit, include_names=include_names) for unit in units[:30]]
    owner_links = (
        UnitMembership.query
        .join(Unit, UnitMembership.unit_id == Unit.id)
        .filter(
            Unit.client_id == client.id,
            UnitMembership.role == "owner",
            UnitMembership.is_current.is_(True),
        )
        .all()
    )
    resident_links = (
        UnitMembership.query
        .join(Unit, UnitMembership.unit_id == Unit.id)
        .filter(
            Unit.client_id == client.id,
            UnitMembership.role.in_(("resident", "tenant")),
            UnitMembership.is_current.is_(True),
        )
        .all()
    )
    safe_summary = (
        f"{client.name} has {len(units)} generated unit record(s) across "
        f"{len(block_counts)} block/core/area group(s), with {len(owner_links)} current owner link(s) "
        f"and {len(resident_links)} current resident/tenant link(s) in source records."
    )

    return {
        "context_type": "gar_client_unit_source_query",
        "query_ready": True,
        "question": question or "",
        "role_context": role_context,
        "safe_summary": safe_summary,
        "client": {
            "id": client.id,
            "name": client.name,
            "property_name": client.property_name,
            "client_code": client.client_code,
            "client_type": client.client_type,
            "city": client.city,
            "region": client.region,
            "country": client.country,
            "expected_units": client.number_of_units,
            "source_structure": {
                "apartments": client.units_apartments or 0,
                "houses": client.units_houses or 0,
                "commercial": client.units_commercial or 0,
                "other": client.units_other or 0,
                "blocks": client.block_names,
                "cores_per_block": client.cores_per_block,
            },
        },
        "stats": {
            "units": len(units),
            "owners": len(owner_links),
            "residents": len(resident_links),
            "block_core_groups": len(block_counts),
            "gar_ready_units": len([unit for unit in units if unit.gar_chat_ready]),
        },
        "breakdown": {
            "by_block_core": block_counts,
            "by_occupancy": occupancy_counts,
            "by_type": type_counts,
        },
        "records": {
            "units": compact_units,
        },
        "visibility": {
            "owner_resident_names_included": include_names,
            "contact_details_included": False,
            "finance_details_included": False,
        },
        "source_references": [
            {"model": "Client", "record_id": client.id, "fields": ["name", "property_name", "number_of_units", "block_names"]},
            {"model": "Unit", "record_id": None, "fields": ["client_id", "unit_label", "unit_number", "block_name", "core_name", "occupancy_status"]},
            {"model": "UnitMembership", "record_id": None, "fields": ["unit_id", "member_id", "role", "is_current"]},
            {"model": "Member", "record_id": None, "fields": ["full_name"] if include_names else ["id"]},
        ],
    }


def build_works_source_query(
    *,
    company_id: int | None,
    role_context: str,
    allowed_client_ids: tuple[int, ...] | None = None,
    question: str = "",
) -> dict:
    """Build a source-backed Works query result for GAR.

    The result deliberately returns structured source data rather than a free
    model answer. GAR UI/app layers can render this or ask a model to summarise
    only after source references are present.
    """
    if not company_id:
        return {
            "context_type": "gar_works_source_query",
            "query_ready": False,
            "error": "company_context_missing",
            "source_references": [],
        }

    filters = WorksFilters(allowed_client_ids=allowed_client_ids)
    data = build_command_centre(
        company_id=company_id,
        filters=filters,
        include_gar_history=True,
    )
    payload = works_command_centre_payload(data, filters, role_context=role_context)
    stats = payload.get("stats", {})
    queues = payload.get("queues", {})
    gar = payload.get("gar", {})
    normalised_role = _normalise_role_context(role_context)
    can_view_quality = normalised_role in WORKS_QUALITY_MANAGEMENT_ROLES
    contractor_quality = gar.get("contractor_quality", []) if can_view_quality else []
    open_work_orders = queues.get("open_work_orders", [])
    member_requests = queues.get("open_member_requests", [])
    completion_review = queues.get("completion_review", [])
    repeated_returns = queues.get("repeated_returns", [])

    safe_summary = (
        f"Works Logix source query found {stats.get('open_work_orders', 0)} open work order(s), "
        f"{stats.get('closed_work_orders', 0)} closed work order(s), "
        f"{stats.get('open_member_requests', 0)} open member request(s), and "
        f"{gar.get('attention_total', 0)} GAR attention signal(s) in this role scope."
    )
    if contractor_quality:
        safe_summary += (
            f" GAR also found {len(contractor_quality)} contractor quality risk pattern"
            f"{'' if len(contractor_quality) == 1 else 's'} for management review."
        )

    return {
        "context_type": "gar_works_source_query",
        "query_ready": True,
        "question": question or "",
        "role_context": normalised_role or role_context,
        "scope": payload.get("scope", {}),
        "safe_summary": safe_summary,
        "stats": stats,
        "next_actions": payload.get("next_actions", []),
        "gar": {
            "signal_count": gar.get("signal_count", 0),
            "attention_total": gar.get("attention_total", 0),
            "history_review": gar.get("history_review", []),
            "contractor_quality_visible": can_view_quality,
            "contractor_quality": contractor_quality[:8],
            "summary": gar.get("summary", {}),
        },
        "records": {
            "open_work_orders": [_compact_work_item(item) for item in open_work_orders[:8]],
            "completion_review": [_compact_work_item(item) for item in completion_review[:8]],
            "repeated_returns": [_compact_work_item(item) for item in repeated_returns[:8]],
            "open_member_requests": member_requests[:8],
        },
        "source_references": [
            {"model": "WorkOrder", "record_id": None, "fields": ["id", "client_id", "unit_id", "status", "title"]},
            {"model": "MaintenanceRequest", "record_id": None, "fields": ["id", "unit_id", "status", "title"]},
            {"model": "WorkOrderLifecycleEvent", "record_id": None, "fields": ["work_order_id", "event_type", "occurred_at"]},
            {"model": "WorkOrderReopenRequest", "record_id": None, "fields": ["work_order_id", "status"]},
            {"model": "ContractorFeedback", "record_id": None, "fields": ["work_order_id", "overall_rating"]},
        ],
    }


def build_contractor_works_source_query(
    *,
    user_id: int | None,
    role_context: str,
    question: str = "",
) -> dict:
    """Build a contractor-scoped Works source query for GAR.

    This deliberately uses the Contractor Logix queue service rather than the
    management command centre, so GAR cannot widen a contractor into company
    work records they are not assigned to.
    """
    if not user_id:
        return {
            "context_type": "gar_contractor_works_source_query",
            "query_ready": False,
            "error": "user_context_missing",
            "source_references": [],
        }

    user = User.query.get(user_id)
    if not user or not user.contractor_id:
        return {
            "context_type": "gar_contractor_works_source_query",
            "query_ready": False,
            "error": "contractor_profile_missing",
            "source_references": [],
        }

    from app.services.works.workflow_service import (
        ContractorWorkFilters,
        contractor_work_queue_payload,
        get_contractor_work_orders,
    )

    filters = ContractorWorkFilters()
    data = get_contractor_work_orders(user.contractor_id, user.id, filters=filters)
    payload = contractor_work_queue_payload(data, filters)
    stats = payload.get("stats", {})
    queues = payload.get("queues", {})

    safe_summary = (
        f"Contractor Logix source query found {stats.get('assigned', 0)} assigned job(s), "
        f"{stats.get('active', 0)} active job(s), {stats.get('returned', 0)} returned job(s), "
        f"{stats.get('submitted', 0)} submitted job(s), and {stats.get('closed', 0)} closed job(s) "
        "in this contractor queue."
    )

    return {
        "context_type": "gar_contractor_works_source_query",
        "query_ready": True,
        "question": question or "",
        "role_context": _normalise_role_context(role_context) or "contractor",
        "safe_summary": safe_summary,
        "stats": stats,
        "next_actions": payload.get("next_actions", []),
        "records": {
            "assigned": [_compact_work_item(item) for item in queues.get("assigned", [])[:8]],
            "active": [_compact_work_item(item) for item in queues.get("active", [])[:8]],
            "returned": [_compact_work_item(item) for item in queues.get("returned", [])[:8]],
            "submitted": [_compact_work_item(item) for item in queues.get("submitted", [])[:8]],
            "closed": [_compact_work_item(item) for item in queues.get("closed", [])[:8]],
        },
        "visibility": {
            "scope": "assigned_contractor_queue",
            "management_quality_records_included": False,
            "member_private_contact_included": False,
            "finance_records_included": False,
        },
        "source_references": [
            {"model": "User", "record_id": user.id, "fields": ["id", "contractor_id"]},
            {"model": "WorkOrder", "record_id": None, "fields": ["id", "contractor_id", "status", "title", "unit_id"]},
            {"model": "WorkOrderCompletion", "record_id": None, "fields": ["work_order_id", "quality_status", "visibility_scope"]},
            {"model": "WorkOrderLifecycleEvent", "record_id": None, "fields": ["work_order_id", "event_type", "occurred_at"]},
        ],
    }


def build_member_works_source_query(
    *,
    user_id: int | None,
    role_context: str,
    question: str = "",
) -> dict:
    """Build a member/resident-scoped Works source query for GAR."""
    if not user_id:
        return {
            "context_type": "gar_member_works_source_query",
            "query_ready": False,
            "error": "user_context_missing",
            "source_references": [],
        }

    from app.models.members.member import Member
    from app.services.members.works_context import build_member_works_context, member_works_feed_payload

    member = Member.query.filter_by(user_id=user_id).first()
    if not member:
        return {
            "context_type": "gar_member_works_source_query",
            "query_ready": False,
            "error": "member_profile_missing",
            "source_references": [],
        }

    memberships = (
        UnitMembership.query
        .filter_by(member_id=member.id, is_current=True)
        .order_by(UnitMembership.role.asc())
        .all()
    )
    works_context = build_member_works_context(member, memberships)
    payload = member_works_feed_payload(member, memberships, works_context)
    records = {
        "requests": payload.get("requests", [])[:8],
        "open_work_orders": payload.get("open_work_orders", [])[:8],
        "closed_work_orders": payload.get("closed_work_orders", [])[:8],
        "reopen_requests": payload.get("reopen_requests", [])[:8],
    }
    stats = {
        "linked_units": len(payload.get("linked_units", []) or []),
        "requests": len(payload.get("requests", []) or []),
        "open_work_orders": len(payload.get("open_work_orders", []) or []),
        "closed_work_orders": len(payload.get("closed_work_orders", []) or []),
        "reopen_requests": len(payload.get("reopen_requests", []) or []),
        "feedback_needed": len(works_context.get("feedback_needed_work_orders", []) or []),
    }

    safe_summary = (
        f"Members Logix source query found {stats['linked_units']} linked unit(s), "
        f"{stats['requests']} submitted request(s), {stats['open_work_orders']} open work order(s), "
        f"{stats['closed_work_orders']} closed work order(s), and {stats['reopen_requests']} reopen request(s) "
        "visible to this member profile."
    )

    return {
        "context_type": "gar_member_works_source_query",
        "query_ready": True,
        "question": question or "",
        "role_context": _normalise_role_context(role_context) or "member",
        "safe_summary": safe_summary,
        "stats": stats,
        "next_actions": payload.get("next_actions", []),
        "attention_queues": payload.get("attention_queues", []),
        "records": records,
        "visibility": {
            "scope": "linked_member_units",
            "linked_unit_ids": [
                item.get("unit", {}).get("id")
                for item in payload.get("linked_units", [])
                if isinstance(item.get("unit"), dict)
            ],
            "owner_finance_records_included": False,
            "other_member_records_included": False,
            "management_quality_records_included": False,
        },
        "source_references": [
            {"model": "Member", "record_id": member.id, "fields": ["id", "user_id", "client_id"]},
            {"model": "UnitMembership", "record_id": None, "fields": ["member_id", "unit_id", "role", "is_current"]},
            {"model": "MaintenanceRequest", "record_id": None, "fields": ["member_id", "unit_id", "status", "title"]},
            {"model": "WorkOrder", "record_id": None, "fields": ["unit_id", "status", "title"]},
            {"model": "WorkOrderReopenRequest", "record_id": None, "fields": ["work_order_id", "requested_by_member_id", "status"]},
        ],
    }
