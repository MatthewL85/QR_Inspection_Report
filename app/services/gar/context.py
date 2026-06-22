from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
import re
from typing import Any

from app.models.client.client import Client
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.models.contracts import ClientContract
from app.models.maintenance.maintenance_request import MaintenanceRequest
from app.models.members.unit import Unit
from app.models.members.unit_membership import UnitMembership
from app.models.works.work_order import WorkOrder
from app.models.works.work_order_reopen_request import WorkOrderReopenRequest


OPEN_WORK_STATUSES = {
    "open",
    "quote requested",
    "quote submitted",
    "quote approved",
    "accepted",
    "available",
    "completion submitted",
    "returned",
    "returned to creator",
    "in progress",
    "pending",
}

CLOSED_WORK_STATUSES = {
    "completed",
    "closed",
    "resolved",
    "cancelled",
}

STUCK_WORK_DAYS = 14
PATTERN_MEMORY_MIN_COUNT = 2


ROLE_ALIASES = {
    "assigned_assistant": "assistant",
    "assistant_manager_cover": "assistant",
    "assistant_manager": "assistant",
    "master_assistant": "assistant",
    "financial_controller": "finance",
    "director_governance": "director",
}

CONTRACTOR_QUALITY_MANAGEMENT_ROLES = {
    "super_admin",
    "admin",
    "property_manager",
    "assistant",
}


def _normalise_role_context(role_context: str | None) -> str:
    role = (role_context or "").strip().lower().replace(" ", "_").replace("-", "_")
    return ROLE_ALIASES.get(role, role)


def _iso(value: date | datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _money(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _full_name(person: Any) -> str:
    first_name = getattr(person, "first_name", None) or ""
    last_name = getattr(person, "last_name", None) or ""
    full_name = f"{first_name} {last_name}".strip()
    return full_name or getattr(person, "full_name", None) or getattr(person, "name", None) or "-"


def _unit_label(unit: Unit) -> str:
    return unit.unit_name or unit.unit_label or unit.unit_number or f"Unit {unit.id}"


def _source(model_name: str, record_id: int | None, fields: list[str]) -> dict[str, Any]:
    return {
        "model": model_name,
        "id": record_id,
        "fields": fields,
    }


def build_unit_context(unit_id: int, viewer_user_id: int | None = None) -> dict[str, Any]:
    """Build a GAR-ready context object for a unit without changing source data."""

    unit = Unit.query.get(unit_id)
    if not unit:
        raise ValueError(f"Unit {unit_id} was not found")

    owner_links = (
        unit.membership_links
        .filter_by(role="owner", is_current=True)
        .all()
        if unit.membership_links
        else []
    )
    resident_links = (
        unit.membership_links
        .filter(UnitMembership.role.in_(["resident", "tenant"]))
        .filter_by(is_current=True)
        .all()
        if unit.membership_links
        else []
    )

    open_work_orders = [
        work_order for work_order in (unit.work_orders or [])
        if (work_order.status or "").strip().lower() in OPEN_WORK_STATUSES
    ]
    closed_work_orders = [
        work_order for work_order in (unit.work_orders or [])
        if (work_order.status or "").strip().lower() in CLOSED_WORK_STATUSES
    ]
    maintenance_requests = (
        MaintenanceRequest.query
        .filter_by(unit_id=unit.id)
        .order_by(MaintenanceRequest.created_at.desc())
        .limit(10)
        .all()
    )

    context = {
        "context_type": "unit",
        "viewer_user_id": viewer_user_id,
        "unit_context": {
            "id": unit.id,
            "client_id": unit.client_id,
            "label": _unit_label(unit),
            "unit_number": unit.unit_number,
            "unit_type": unit.unit_type,
            "unit_category": unit.unit_category,
            "block_name": unit.block_name,
            "core_name": unit.core_name,
            "area_name": unit.area_name,
            "status": unit.status,
            "occupancy_status": unit.occupancy_status,
            "sale_status": unit.sale_status,
            "conveyancing_status": unit.conveyancing_status,
            "gar_risk_score": unit.gar_risk_score,
            "gar_alignment_status": unit.gar_alignment_status,
            "gar_chat_ready": unit.gar_chat_ready,
        },
        "client_context": {
            "id": unit.client.id if unit.client else None,
            "name": unit.client.name if unit.client else None,
            "property_name": unit.client.property_name if unit.client else None,
            "city": unit.client.city if unit.client else None,
            "region": unit.client.region if unit.client else None,
        },
        "ownership_context": [
            {
                "member_id": link.member_id,
                "name": _full_name(link.member) if link.member else "-",
                "email": getattr(link.member, "email", None) if link.member else None,
                "phone": getattr(link.member, "phone", None) if link.member else None,
                "is_primary": link.is_primary,
                "ownership_start_date": _iso(link.ownership_start_date),
                "ownership_end_date": _iso(link.ownership_end_date),
            }
            for link in owner_links
        ],
        "occupancy_context": [
            {
                "member_id": link.member_id,
                "name": _full_name(link.member) if link.member else "-",
                "email": getattr(link.member, "email", None) if link.member else None,
                "phone": getattr(link.member, "phone", None) if link.member else None,
                "tenancy_start_date": _iso(link.tenancy_start_date),
                "tenancy_end_date": _iso(link.tenancy_end_date),
            }
            for link in resident_links
        ],
        "works_context": {
            "open_work_orders": len(open_work_orders),
            "closed_work_orders": len(closed_work_orders),
            "recent_member_requests": [
                {
                    "id": request.id,
                    "title": request.title,
                    "status": request.status,
                    "urgency": request.urgency_level,
                    "created_at": _iso(request.created_at),
                }
                for request in maintenance_requests
            ],
        },
        "finance_context": {
            "currency": unit.currency or "EUR",
            "service_charge_scheme": unit.service_charge_scheme,
            "service_charge_percent": unit.service_charge_percent,
            "service_charge_amount": _money(unit.service_charge_amount),
            "finance_ledger_code": unit.finance_ledger_code,
            "finance_external_ref": unit.finance_external_ref,
        },
        "risk_context": {
            "unit_gar_risk_score": unit.gar_risk_score,
            "service_charge_risks": unit.ai_service_charge_risks,
            "flagged_clauses": unit.gar_flagged_clauses,
            "recommendations": unit.gar_recommendations,
        },
        "visibility_rules": {
            "personal_data": "role-gated",
            "finance_data": "owner/finance/admin gated",
            "contractor_access": "work-order scoped",
        },
        "source_references": [
            _source("Unit", unit.id, ["client_id", "unit_number", "block_name", "occupancy_status", "status"]),
            _source("Client", unit.client_id, ["name", "property_name", "city", "region"]),
            _source("UnitMembership", None, ["member_id", "unit_id", "role", "is_current"]),
            _source("WorkOrder", None, ["unit_id", "status"]),
            _source("MaintenanceRequest", None, ["unit_id", "status", "urgency_level"]),
        ],
    }
    return context


def build_work_order_context(
    work_order_id: int,
    viewer_user_id: int | None = None,
    audience: str = "admin",
) -> dict[str, Any]:
    """Build a GAR-ready context object for a cross-module work order workflow."""

    from app.services.works.workflow_service import build_work_order_lifecycle_for_audience

    work_order = WorkOrder.query.get(work_order_id)
    if not work_order:
        raise ValueError(f"Work order {work_order_id} was not found")

    unit = work_order.unit
    client = work_order.client or (unit.client if unit else None)
    maintenance_request = work_order.maintenance_request
    completion = work_order.completion
    feedback = work_order.feedback
    lifecycle_events = build_work_order_lifecycle_for_audience(work_order, audience)
    recommended_actions = _work_order_recommended_actions(work_order)
    operational_intelligence = _work_order_operational_intelligence(
        work_order=work_order,
        maintenance_request=maintenance_request,
        completion=completion,
        feedback=feedback,
        lifecycle_events=lifecycle_events,
        recommended_actions=recommended_actions,
    )
    relevant_history = build_work_order_relevant_history(
        work_order.id,
        audience=audience,
        _work_order=work_order,
    )

    return {
        "context_type": "work_order",
        "viewer_user_id": viewer_user_id,
        "audience": audience,
        "work_order_context": {
            "id": work_order.id,
            "title": work_order.title,
            "description": work_order.description,
            "request_type": work_order.request_type,
            "business_type": work_order.business_type,
            "status": work_order.status,
            "created_at": _iso(work_order.created_at),
            "preferred_visit_date": _iso(work_order.preferred_visit_date),
            "privacy_scope": work_order.privacy_scope,
            "attachments_count": work_order.attachments_count,
            "gar_urgency_score": work_order.gar_urgency_score,
            "gar_recommended_action": work_order.gar_recommended_action,
            "gar_explanation": work_order.gar_explanation,
        },
        "client_context": {
            "id": client.id if client else None,
            "name": client.name if client else None,
            "property_name": client.property_name if client else None,
            "city": client.city if client else None,
            "region": client.region if client else None,
        },
        "unit_context": {
            "id": unit.id if unit else None,
            "label": _unit_label(unit) if unit else None,
            "unit_number": unit.unit_number if unit else None,
            "block_name": unit.block_name if unit else None,
            "core_name": unit.core_name if unit else None,
            "occupancy_status": unit.occupancy_status if unit else None,
        },
        "member_request_context": {
            "id": maintenance_request.id if maintenance_request else None,
            "title": maintenance_request.title if maintenance_request else None,
            "status": maintenance_request.status if maintenance_request else None,
            "category": maintenance_request.category if maintenance_request else None,
            "urgency": maintenance_request.urgency_level if maintenance_request else None,
            "created_at": _iso(maintenance_request.created_at) if maintenance_request else None,
            "media_uploaded": maintenance_request.media_uploaded if maintenance_request else None,
            "attachments_count": maintenance_request.attachments_count if maintenance_request else None,
        },
        "contractor_context": {
            "contractor_id": work_order.contractor_id,
            "contractor_name": work_order.contractor_company.company_name if work_order.contractor_company else None,
            "accepted_by_user_id": work_order.accepted_contractor_id,
            "accepted_by": work_order.accepted_contractor.full_name if work_order.accepted_contractor else None,
        },
        "completion_context": {
            "submitted": bool(completion),
            "completed_at": _iso(completion.completed_at) if completion else None,
            "completed_by": completion.completed_by.full_name if completion and completion.completed_by else None,
            "confirmed_by": completion.confirmed_by_admin.full_name if completion and completion.confirmed_by_admin else None,
            "media_uploaded": completion.media_uploaded if completion else None,
            "attachments_count": completion.attachments_count if completion else None,
            "external_reference": completion.external_reference if completion else None,
            "completion_notes": completion.completion_notes if completion else None,
        },
        "feedback_context": {
            "submitted": bool(feedback),
            "rating": feedback.overall_rating if feedback else None,
            "comments": feedback.comments if feedback else None,
            "source": feedback.feedback_source if feedback else None,
            "submitted_at": _iso(feedback.created_at) if feedback else None,
        },
        "reopen_context": [
            {
                "id": request.id,
                "status": request.status,
                "reason": request.reason,
                "additional_details": request.additional_details,
                "created_at": _iso(request.created_at),
                "reviewed_at": _iso(request.reviewed_at),
                "review_notes": request.review_notes,
            }
            for request in sorted(
                work_order.reopen_requests or [],
                key=lambda item: item.created_at or datetime.min,
                reverse=True,
            )
        ],
        "lifecycle_context": [
            {
                "title": event.get("title"),
                "source": event.get("source"),
                "actor": event.get("actor"),
                "status": event.get("status"),
                "note": event.get("note"),
                "occurred_at": _iso(event.get("occurred_at")),
                "persisted": bool(event.get("persisted")),
                "access_context": event.get("access_context") or "",
            }
            for event in lifecycle_events
        ],
        "risk_context": {
            "is_open": (work_order.status or "").strip().lower() in OPEN_WORK_STATUSES,
            "is_closed": (work_order.status or "").strip().lower() in CLOSED_WORK_STATUSES,
            "returned_to_contractor": (work_order.status or "").strip().lower() == "returned",
            "completion_waiting_for_review": (work_order.status or "").strip().lower() == "completion submitted",
            "pending_reopen_requests": len([
                request for request in (work_order.reopen_requests or [])
                if request.status == "Pending"
            ]),
        },
        "relevant_history": relevant_history,
        "operational_intelligence": operational_intelligence,
        "recommended_actions": recommended_actions,
        "visibility_rules": {
            "personal_data": "role-gated",
            "member_data": "member/unit scoped",
            "contractor_data": "work-order scoped",
            "lifecycle_data": "audience filtered",
        },
        "source_references": [
            _source("WorkOrder", work_order.id, ["unit_id", "client_id", "contractor_id", "status"]),
            _source("WorkOrderLifecycleEvent", None, ["work_order_id", "source_module", "event_type", "occurred_at"]),
            _source("MaintenanceRequest", maintenance_request.id if maintenance_request else None, ["work_order_id", "unit_id", "status"]),
            _source("WorkOrderCompletion", completion.id if completion else None, ["work_order_id", "completed_at", "confirmed_by_admin_id"]),
            _source("ContractorFeedback", feedback.id if feedback else None, ["work_order_id", "overall_rating", "feedback_source"]),
            _source("WorkOrderReopenRequest", None, ["work_order_id", "status", "reviewed_at"]),
            _source("WorkOrder", None, ["unit_id", "client_id", "business_type", "status", "completion"]),
        ],
    }


def build_work_order_relevant_history(
    work_order_id: int,
    audience: str = "admin",
    limit: int = 5,
    _work_order: WorkOrder | None = None,
) -> dict[str, Any]:
    """Find previous related works and summarise them for the current audience."""

    work_order = _work_order or WorkOrder.query.get(work_order_id)
    if not work_order:
        raise ValueError(f"Work order {work_order_id} was not found")

    unit = work_order.unit
    client_id = work_order.client_id or (unit.client_id if unit else None)
    if not client_id and not work_order.unit_id:
        return _empty_relevant_history(work_order.id, audience)

    query = WorkOrder.query.filter(WorkOrder.id != work_order.id)
    if client_id:
        query = query.filter(WorkOrder.client_id == client_id)
    elif work_order.unit_id:
        query = query.filter(WorkOrder.unit_id == work_order.unit_id)

    candidates = query.order_by(WorkOrder.created_at.desc()).limit(120).all()
    scored = []
    for candidate in candidates:
        score, reasons = _related_work_score(work_order, candidate)
        if score >= 3:
            scored.append((score, candidate, reasons))

    scored.sort(
        key=lambda item: (
            -item[0],
            item[1].created_at or datetime.min,
        ),
        reverse=True,
    )
    related = scored[:limit]
    records = [
        _related_work_record(candidate, reasons, audience)
        for _, candidate, reasons in related
    ]
    latest = records[0] if records else None
    same_unit_count = len([
        record for record in records
        if "Same unit" in record.get("match_reasons", [])
    ])
    closed_count = len([
        record for record in records
        if (record.get("status") or "").strip().lower() in CLOSED_WORK_STATUSES
    ])
    reopened_count = sum(record.get("reopen_count", 0) for record in records)
    contractor_names = sorted({
        record.get("contractor")
        for record in records
        if record.get("contractor")
    })
    routing_recommendation = _history_routing_recommendation(
        records=records,
        same_unit_count=same_unit_count,
        reopened_count=reopened_count,
        contractor_names=contractor_names,
    )

    if latest:
        contractor_summary = (
            f"GAR found {len(records)} related previous work order"
            f"{'' if len(records) == 1 else 's'}. "
            f"Most recent: {latest['reference']} on {latest.get('created_at') or 'unknown date'}"
            f" for {latest.get('category') or 'general works'}. "
            f"Previous outcome: {latest.get('outcome') or 'review previous completion notes'}."
        )
        admin_summary = (
            f"{len(records)} related previous work order"
            f"{'' if len(records) == 1 else 's'} found; "
            f"{same_unit_count} same-unit, {closed_count} closed, {reopened_count} reopen request"
            f"{'' if reopened_count == 1 else 's'}."
        )
    else:
        contractor_summary = "GAR did not find related previous work for this unit/development."
        admin_summary = "No related work order history is currently linked by GAR."

    return {
        "context_type": "work_order_relevant_history",
        "work_order_id": work_order.id,
        "audience": audience,
        "summary": {
            "related_count": len(records),
            "same_unit_count": same_unit_count,
            "closed_count": closed_count,
            "reopen_count": reopened_count,
            "previous_contractor_count": len(contractor_names),
            "latest_reference": latest["reference"] if latest else None,
        },
        "contractor_safe_summary": contractor_summary,
        "admin_summary": admin_summary,
        "routing_recommendation": routing_recommendation,
        "records": records,
        "visibility_rules": {
            "contractor": "summary and operational completion outcome only",
            "admin": "source work order references visible",
            "restricted": ["owner finance", "private resident/member details", "internal-only notes"],
        },
        "source_references": [
            _source("WorkOrder", work_order.id, ["unit_id", "client_id", "business_type", "title", "description"]),
            _source("WorkOrder", None, ["unit_id", "client_id", "business_type", "status", "created_at"]),
            _source("WorkOrderCompletion", None, ["work_order_id", "completion_notes", "completed_at"]),
            _source("WorkOrderReopenRequest", None, ["work_order_id", "unit_id", "status"]),
        ],
    }


def build_client_context(client_id: int, viewer_user_id: int | None = None) -> dict[str, Any]:
    """Build a GAR-ready context object for a client/development."""

    client = Client.query.get(client_id)
    if not client:
        raise ValueError(f"Client {client_id} was not found")

    units = Unit.query.filter_by(client_id=client.id).all()
    work_orders = WorkOrder.query.filter_by(client_id=client.id).all()
    unit_ids = [unit.id for unit in units]
    maintenance_requests = (
        MaintenanceRequest.query
        .filter(MaintenanceRequest.unit_id.in_(unit_ids))
        .order_by(MaintenanceRequest.created_at.desc())
        .all()
        if unit_ids
        else []
    )
    contracts = (
        ClientContract.query
        .filter_by(client_id=client.id)
        .order_by(ClientContract.end_date.desc())
        .all()
    )
    compliance_documents = (
        ClientComplianceDocument.query
        .filter_by(client_id=client.id)
        .order_by(ClientComplianceDocument.uploaded_at.desc())
        .limit(10)
        .all()
    )

    open_work_orders = [
        work_order for work_order in work_orders
        if (work_order.status or "").strip().lower() in OPEN_WORK_STATUSES
    ]
    closed_work_orders = [
        work_order for work_order in work_orders
        if (work_order.status or "").strip().lower() in CLOSED_WORK_STATUSES
    ]
    latest_contract = contracts[0] if contracts else None
    works_intelligence = build_works_intelligence_queue(
        company_id=client.company_id,
        work_orders=work_orders,
        member_requests=maintenance_requests,
        client_id=client.id,
    )
    development_health = _development_health_snapshot(
        client=client,
        units=units,
        work_orders=work_orders,
        maintenance_requests=maintenance_requests,
        compliance_documents=compliance_documents,
        latest_contract=latest_contract,
        works_intelligence=works_intelligence,
    )

    return {
        "context_type": "client",
        "viewer_user_id": viewer_user_id,
        "client_context": {
            "id": client.id,
            "name": client.name,
            "property_name": client.property_name,
            "client_type": client.client_type,
            "address": client.address,
            "city": client.city,
            "region": client.region,
            "country": client.country,
            "currency": client.currency,
            "number_of_units": client.number_of_units,
            "development_structure": {
                "blocks": client.block_names,
                "apartments": client.units_apartments,
                "commercial": client.units_commercial,
                "other": client.units_other,
            },
        },
        "unit_context": {
            "total_units": len(units),
            "active_units": len([unit for unit in units if unit.status == "Active"]),
            "blocks": sorted({unit.block_name for unit in units if unit.block_name}),
            "occupancy_summary": {
                status or "unknown": len([unit for unit in units if (unit.occupancy_status or "unknown") == status])
                for status in sorted({unit.occupancy_status or "unknown" for unit in units})
            },
        },
        "works_context": {
            "open_work_orders": len(open_work_orders),
            "closed_work_orders": len(closed_work_orders),
            "total_work_orders": len(work_orders),
        },
        "contract_context": {
            "contract_count": len(contracts),
            "latest_contract_id": latest_contract.id if latest_contract else None,
            "latest_contract_end_date": _iso(latest_contract.end_date) if latest_contract else None,
            "latest_contract_status": latest_contract.sign_status if latest_contract else None,
            "latest_contract_value": _money(latest_contract.contract_value) if latest_contract else None,
        },
        "document_context": {
            "recent_compliance_documents": [
                {
                    "id": document.id,
                    "name": getattr(document, "document_name", None) or getattr(document, "file_name", None),
                    "type": document.document_type,
                    "status": document.status,
                    "expires_at": _iso(getattr(document, "expires_at", None) or getattr(document, "expiry_date", None)),
                    "ai_status": document.ai_status,
                }
                for document in compliance_documents
            ],
        },
        "risk_context": {
            "gar_ready_units": len([unit for unit in units if unit.gar_chat_ready]),
            "units_with_risk_score": len([unit for unit in units if unit.gar_risk_score is not None]),
            "open_work_pressure": len(open_work_orders),
        },
        "development_health": development_health,
        "works_intelligence": works_intelligence,
        "recommended_actions": _client_recommended_actions(
            client=client,
            units=units,
            open_work_orders=open_work_orders,
            latest_contract=latest_contract,
        ) + development_health["recommended_actions"][:3],
        "visibility_rules": {
            "personal_data": "role-gated",
            "finance_data": "finance/admin gated",
            "member_data": "member/unit scoped",
        },
        "source_references": [
            _source("Client", client.id, ["name", "property_name", "block_names", "number_of_units"]),
            _source("Unit", None, ["client_id", "status", "occupancy_status", "block_name"]),
            _source("WorkOrder", None, ["client_id", "unit_id", "status"]),
            _source("ClientContract", None, ["client_id", "end_date", "contract_value", "sign_status"]),
            _source("ClientComplianceDocument", None, ["client_id", "document_type", "status", "ai_status"]),
            _source("MaintenanceRequest", None, ["unit_id", "status", "urgency_level"]),
        ],
    }


def build_portfolio_context(
    company_id: int | None = None,
    *,
    client_id: int | None = None,
    allowed_client_ids: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    """Build a high-level GAR context object for the current managed portfolio."""

    client_query = Client.query
    unit_query = Unit.query
    work_query = WorkOrder.query

    if company_id:
        client_query = client_query.filter_by(company_id=company_id)
        unit_query = unit_query.filter_by(company_id=company_id)
        work_query = work_query.filter_by(company_id=company_id)
    if client_id:
        client_query = client_query.filter(Client.id == client_id)
        unit_query = unit_query.filter(Unit.client_id == client_id)
        work_query = work_query.filter(WorkOrder.client_id == client_id)
    if allowed_client_ids is not None:
        client_query = client_query.filter(Client.id.in_(allowed_client_ids))
        unit_query = unit_query.filter(Unit.client_id.in_(allowed_client_ids))
        work_query = work_query.filter(WorkOrder.client_id.in_(allowed_client_ids))

    clients = client_query.order_by(Client.name.asc()).all()
    units = unit_query.all()
    work_orders = work_query.all()
    client_ids = [client.id for client in clients]
    contracts = (
        ClientContract.query
        .filter(ClientContract.client_id.in_(client_ids))
        .all()
        if client_ids
        else []
    )

    open_work_orders = [
        work_order for work_order in work_orders
        if (work_order.status or "").strip().lower() in OPEN_WORK_STATUSES
    ]
    expired_contracts = [
        contract for contract in contracts
        if contract.end_date and contract.end_date < date.today()
    ]

    return {
        "context_type": "portfolio",
        "portfolio_context": {
            "clients": len(clients),
            "units": len(units),
            "contracts": len(contracts),
            "open_work_orders": len(open_work_orders),
            "expired_contracts": len(expired_contracts),
            "gar_ready_units": len([unit for unit in units if unit.gar_chat_ready]),
        },
        "recommended_actions": _portfolio_recommended_actions(
            expired_contracts=expired_contracts,
            open_work_orders=open_work_orders,
        ),
        "source_references": [
            _source("Client", None, ["company_id", "name", "property_name"]),
            _source("Unit", None, ["company_id", "client_id", "gar_chat_ready"]),
            _source("WorkOrder", None, ["company_id", "client_id", "status"]),
            _source("ClientContract", None, ["client_id", "end_date"]),
        ],
    }


def build_development_health_register(
    company_id: int | None = None,
    *,
    client_id: int | None = None,
    allowed_client_ids: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    """Build a GAR portfolio register of development health snapshots."""

    client_query = Client.query.order_by(Client.name.asc())
    if company_id:
        client_query = client_query.filter_by(company_id=company_id)
    if client_id:
        client_query = client_query.filter(Client.id == client_id)
    if allowed_client_ids is not None:
        client_query = client_query.filter(Client.id.in_(allowed_client_ids))

    rows: list[dict[str, Any]] = []
    for client in client_query.all():
        client_context = build_client_context(client.id)
        health = client_context.get("development_health", {})
        works_intelligence = client_context.get("works_intelligence", {})
        summary = health.get("summary", {})
        rows.append({
            "client_id": client.id,
            "client_name": client.name,
            "property_name": client.property_name,
            "city": client.city,
            "score": health.get("score", 0),
            "status": health.get("status", "Not assessed"),
            "tone": health.get("tone", "secondary"),
            "open_work_orders": summary.get("open_work_orders", 0),
            "resident_signals": summary.get("pending_member_requests", 0),
            "finance_ready_units": summary.get("finance_ready_units", 0),
            "generated_units": summary.get("generated_units", 0),
            "expected_units": summary.get("expected_units", 0),
            "expired_compliance_documents": summary.get("expired_compliance_documents", 0),
            "pattern_memory_groups": summary.get("gar_pattern_memory_groups", 0),
            "gar_attention_total": works_intelligence.get("attention_total", 0),
            "recommended_actions": health.get("recommended_actions", []),
        })

    rows.sort(key=lambda item: (item["score"], -item["gar_attention_total"], item["client_name"] or ""))
    at_risk = [row for row in rows if row["tone"] == "danger"]
    needs_review = [row for row in rows if row["tone"] == "warning"]
    watch = [row for row in rows if row["tone"] == "info"]
    healthy = [row for row in rows if row["tone"] == "success"]

    return {
        "context_type": "development_health_register",
        "summary": {
            "developments": len(rows),
            "at_risk": len(at_risk),
            "needs_review": len(needs_review),
            "watch": len(watch),
            "healthy": len(healthy),
            "average_score": round(sum(row["score"] for row in rows) / len(rows)) if rows else 0,
        },
        "rows": rows,
        "recommended_actions": _development_register_actions(rows),
        "source_references": [
            _source("Client", None, ["company_id", "name", "property_name"]),
            _source("Unit", None, ["client_id", "status", "service_charge_scheme"]),
            _source("WorkOrder", None, ["client_id", "unit_id", "status"]),
            _source("MaintenanceRequest", None, ["unit_id", "status"]),
            _source("ClientContract", None, ["client_id", "end_date"]),
            _source("ClientComplianceDocument", None, ["client_id", "status", "ai_status"]),
        ],
    }


def build_operational_digest(
    *,
    company_id: int | None = None,
    role_context: str = "super_admin",
    client_id: int | None = None,
    allowed_client_ids: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    """Build a compact GAR operational digest from source-backed contexts."""

    generated_at = datetime.utcnow()
    portfolio_context = build_portfolio_context(
        company_id=company_id,
        client_id=client_id,
        allowed_client_ids=allowed_client_ids,
    )
    development_health_register = build_development_health_register(
        company_id=company_id,
        client_id=client_id,
        allowed_client_ids=allowed_client_ids,
    )
    works_intelligence = build_works_intelligence_queue(
        company_id=company_id,
        client_id=client_id,
        allowed_client_ids=allowed_client_ids,
    )

    health_rows = list(development_health_register.get("rows", []))
    active_works_signals = [
        signal for signal in works_intelligence.get("signals", [])
        if signal.get("severity") != "clear"
    ]
    quality_signals = _management_quality_signals(
        works_intelligence=works_intelligence,
        role_context=role_context,
    )
    priority_actions = _digest_priority_actions(
        portfolio_context=portfolio_context,
        development_health_register=development_health_register,
        works_intelligence=works_intelligence,
    )

    return {
        "context_type": "gar_operational_digest",
        "generated_at": _iso(generated_at),
        "role_context": role_context,
        "visibility_scope": {
            "company_id": company_id,
            "client_id": client_id,
            "allowed_client_count": len(allowed_client_ids) if allowed_client_ids is not None else None,
        },
        "summary": {
            "portfolio": portfolio_context.get("portfolio_context", {}),
            "development_health": development_health_register.get("summary", {}),
            "works": works_intelligence.get("summary", {}),
            "gar_attention_total": works_intelligence.get("attention_total", 0),
            "priority_action_count": len(priority_actions),
        },
        "priority_actions": priority_actions,
        "development_attention": [
            row for row in health_rows
            if row.get("tone") in {"danger", "warning", "info"}
        ][:8],
        "works_attention": active_works_signals[:8],
        "quality_signals": quality_signals,
        "cover_context": works_intelligence.get("cover_context", {}),
        "pattern_memory": works_intelligence.get("pattern_memory", {}),
        "source_references": [
            _source("Client", None, ["company_id", "name", "property_name"]),
            _source("Unit", None, ["company_id", "client_id", "status", "gar_chat_ready"]),
            _source("WorkOrder", None, ["company_id", "client_id", "unit_id", "status"]),
            _source("MaintenanceRequest", None, ["unit_id", "status", "urgency_level"]),
            _source("ContractorFeedback", None, ["work_order_id", "overall_rating"]),
            _source("WorkOrderLifecycleEvent", None, ["work_order_id", "event_type", "event_metadata"]),
            _source("ClientContract", None, ["client_id", "start_date", "end_date"]),
            _source("ClientComplianceDocument", None, ["client_id", "status", "ai_status"]),
        ],
    }


def build_works_intelligence_queue(
    *,
    company_id: int | None = None,
    work_orders: list[WorkOrder] | None = None,
    member_requests: list[MaintenanceRequest] | None = None,
    reopen_requests: list[WorkOrderReopenRequest] | None = None,
    client_id: int | None = None,
    allowed_client_ids: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    """Build GAR-level Works intelligence without changing Works Logix ownership."""

    if work_orders is None:
        work_query = WorkOrder.query
        if company_id:
            work_query = work_query.filter(
                (WorkOrder.company_id == company_id)
                | WorkOrder.client.has(Client.company_id == company_id)
                | WorkOrder.unit.has(Unit.company_id == company_id)
            )
        if client_id:
            work_query = work_query.filter(WorkOrder.client_id == client_id)
        if allowed_client_ids is not None:
            work_query = work_query.filter(WorkOrder.client_id.in_(allowed_client_ids))
        work_orders = work_query.order_by(WorkOrder.created_at.desc()).all()

    if member_requests is None:
        request_query = MaintenanceRequest.query
        if company_id:
            request_query = request_query.filter(
                MaintenanceRequest.unit.has(Unit.company_id == company_id)
                | MaintenanceRequest.member.has(company_id=company_id)
            )
        member_requests = request_query.order_by(MaintenanceRequest.created_at.desc()).all()

    if reopen_requests is None:
        reopen_query = WorkOrderReopenRequest.query
        if company_id:
            reopen_query = reopen_query.join(Unit, WorkOrderReopenRequest.unit_id == Unit.id).filter(Unit.company_id == company_id)
        reopen_requests = reopen_query.order_by(WorkOrderReopenRequest.created_at.desc()).all()

    work_orders = _filter_work_orders_for_gar(work_orders, client_id, allowed_client_ids)
    member_requests = _filter_member_requests_for_gar(member_requests, client_id, allowed_client_ids)
    reopen_requests = _filter_reopen_requests_for_gar(reopen_requests, client_id, allowed_client_ids)

    now = datetime.utcnow()
    open_work_orders = [
        item for item in work_orders
        if (item.status or "").strip().lower() in OPEN_WORK_STATUSES or not item.status
    ]
    stuck_work_orders = [
        item for item in open_work_orders
        if item.created_at and item.created_at <= now - timedelta(days=STUCK_WORK_DAYS)
    ]
    unassigned_work_orders = [
        item for item in open_work_orders
        if not item.contractor_id
    ]
    completion_review_work_orders = [
        item for item in work_orders
        if (item.status or "").strip().lower() == "completion submitted"
    ]
    returned_work_orders = [
        item for item in work_orders
        if (item.status or "").strip().lower() == "returned"
    ]
    repeated_return_work_orders = _work_orders_with_repeated_completion_returns(work_orders)
    low_feedback_work_orders = [
        item for item in work_orders
        if item.feedback and item.feedback.overall_rating and item.feedback.overall_rating <= 2
    ]
    pending_reopen_requests = [
        item for item in reopen_requests
        if item.status == "Pending"
    ]
    cover_lifecycle_events = [
        event
        for work_order in work_orders
        for event in (work_order.lifecycle_events or [])
        if (event.event_metadata or {}).get("access_context") == "assistant_manager_cover"
    ]
    cover_work_order_ids = sorted(
        {event.work_order_id for event in cover_lifecycle_events if event.work_order_id}
    )
    pattern_memory = build_works_issue_pattern_memory(
        work_orders=work_orders,
        member_requests=member_requests,
        reopen_requests=reopen_requests,
    )
    repeated_units = pattern_memory["patterns"]["units"]
    contractor_quality_risks = pattern_memory["patterns"].get("contractor_quality", [])

    signals = [
        _works_signal(
            key="stuck_work",
            label="Stuck Work",
            severity="high" if stuck_work_orders else "clear",
            records=stuck_work_orders,
            anchor="open-work-orders",
            detail=f"Open work older than {STUCK_WORK_DAYS} days.",
            recommended_action="Review ownership, contractor progress and member impact.",
        ),
        _works_signal(
            key="unassigned_work",
            label="Unassigned Work",
            severity="high" if unassigned_work_orders else "clear",
            records=unassigned_work_orders,
            anchor="open-work-orders",
            detail="Open records that cannot progress until routed.",
            recommended_action="Assign a contractor or internal owner.",
        ),
        _works_signal(
            key="completion_review",
            label="Completion Review",
            severity="medium" if completion_review_work_orders else "clear",
            records=completion_review_work_orders,
            anchor="open-work-orders",
            detail="Contractor completion evidence awaiting approval or return.",
            recommended_action="Review completion, evidence and resident feedback.",
        ),
        _works_signal(
            key="returned_to_contractor",
            label="Returned Work",
            severity="medium" if returned_work_orders else "clear",
            records=returned_work_orders,
            anchor="open-work-orders",
            detail="Returned work orders waiting for contractor follow-up.",
            recommended_action="Check contractor response and expected resubmission.",
        ),
        _works_signal(
            key="repeated_completion_returns",
            label="Repeated Completion Returns",
            severity="high" if repeated_return_work_orders else "clear",
            records=repeated_return_work_orders,
            anchor="repeated-returns-review",
            detail="Contractor completions returned more than once.",
            recommended_action="Review evidence quality, return reasons and contractor performance before closure.",
        ),
        _works_signal(
            key="reopen_requests",
            label="Reopen Requests",
            severity="high" if pending_reopen_requests else "clear",
            records=pending_reopen_requests,
            anchor="reopen-requests",
            detail="Member/resident challenges to closed works.",
            recommended_action="Review reopen evidence and decide whether to reopen.",
        ),
        _works_signal(
            key="low_feedback",
            label="Low Feedback",
            severity="medium" if low_feedback_work_orders else "clear",
            records=low_feedback_work_orders,
            anchor="closed-work-orders",
            detail="Closed or reviewed work with poor member/resident feedback.",
            recommended_action="Validate outcome quality before treating as resolved.",
        ),
        {
            "key": "contractor_quality_risk",
            "label": "Contractor Quality Risk",
            "severity": "high" if contractor_quality_risks else "clear",
            "count": len(contractor_quality_risks),
            "anchor": "gar-works-intelligence",
            "detail": "Contractors linked to repeated returns or low member/resident feedback.",
            "recommended_action": "Review contractor outcomes before routing similar work.",
            "records": contractor_quality_risks[:5],
        },
        {
            "key": "repeated_unit_issues",
            "label": "Repeated Unit Issues",
            "severity": "medium" if repeated_units else "clear",
            "count": len(repeated_units),
            "anchor": "work-register",
            "detail": "Units with multiple linked work orders.",
            "recommended_action": "Review whether the issue is recurring, systemic or contractor-related.",
            "records": repeated_units[:5],
        },
    ]

    active_signals = [signal for signal in signals if signal["severity"] != "clear"]
    return {
        "context_type": "works_intelligence",
        "generated_at": _iso(now),
        "attention_total": sum(signal["count"] for signal in active_signals),
        "signal_count": len(active_signals),
        "signals": signals,
        "summary": {
            "open_work_orders": len(open_work_orders),
            "member_requests": len(member_requests),
            "pending_reopen_requests": len(pending_reopen_requests),
            "stuck_work_orders": len(stuck_work_orders),
            "repeated_completion_returns": len(repeated_return_work_orders),
            "contractor_quality_risks": len(contractor_quality_risks),
            "repeated_unit_issue_groups": len(repeated_units),
            "pattern_memory_groups": pattern_memory["pattern_count"],
            "cover_work_orders": len(cover_work_order_ids),
            "cover_events": len(cover_lifecycle_events),
        },
        "cover_context": {
            "cover_context_used": bool(cover_lifecycle_events),
            "cover_event_count": len(cover_lifecycle_events),
            "cover_work_order_count": len(cover_work_order_ids),
            "access_context": "assistant_manager_cover" if cover_lifecycle_events else "",
            "detail": (
                "Assistant Manager / Master Assistant cover has been used in this Works view."
                if cover_lifecycle_events
                else "No assistant cover routing is recorded in this Works view."
            ),
            "records": [
                {
                    "id": event.id,
                    "work_order_id": event.work_order_id,
                    "title": event.title,
                    "actor": event.actor_label or (event.actor_user.full_name if event.actor_user else "-"),
                    "occurred_at": _iso(event.occurred_at),
                }
                for event in cover_lifecycle_events[:5]
            ],
        },
        "pattern_memory": pattern_memory,
        "recommended_actions": [
            {
                "priority": signal["severity"],
                "message": signal["recommended_action"],
                "source": signal["label"],
            }
            for signal in active_signals
        ],
        "source_references": [
            _source("WorkOrder", None, ["company_id", "client_id", "unit_id", "status", "created_at"]),
            _source("MaintenanceRequest", None, ["unit_id", "status", "urgency_level"]),
            _source("WorkOrderReopenRequest", None, ["work_order_id", "unit_id", "status"]),
            _source("ContractorFeedback", None, ["work_order_id", "overall_rating"]),
            _source("WorkOrderLifecycleEvent", None, ["work_order_id", "event_type", "event_metadata"]),
        ],
    }


def _management_quality_signals(
    *,
    works_intelligence: dict[str, Any],
    role_context: str,
) -> dict[str, Any]:
    """Expose compact quality signals only to Works management roles."""

    normalised_role = _normalise_role_context(role_context)
    can_view_contractor_quality = normalised_role in CONTRACTOR_QUALITY_MANAGEMENT_ROLES
    contractor_quality = (
        works_intelligence.get("pattern_memory", {})
        .get("patterns", {})
        .get("contractor_quality", [])
    )

    return {
        "role_context": normalised_role or role_context,
        "contractor_quality_visible": can_view_contractor_quality,
        "contractor_quality_count": len(contractor_quality) if can_view_contractor_quality else 0,
        "contractor_quality": contractor_quality[:5] if can_view_contractor_quality else [],
        "visibility_note": (
            "Visible to Works management roles for quality review and routing decisions."
            if can_view_contractor_quality
            else "Contractor quality patterns are restricted to Works management roles."
        ),
    }


def _digest_priority_actions(
    *,
    portfolio_context: dict[str, Any],
    development_health_register: dict[str, Any],
    works_intelligence: dict[str, Any],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []

    for action in portfolio_context.get("recommended_actions", []):
        actions.append({
            "priority": action.get("priority", "medium"),
            "message": action.get("message", ""),
            "source": action.get("source", "Portfolio"),
        })
    for action in development_health_register.get("recommended_actions", []):
        actions.append({
            "priority": action.get("priority", "medium"),
            "message": action.get("message", ""),
            "source": action.get("source", "Development Health"),
        })
    for action in works_intelligence.get("recommended_actions", []):
        actions.append({
            "priority": action.get("priority", "medium"),
            "message": action.get("message", ""),
            "source": action.get("source", "GAR Works Intelligence"),
        })

    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "clear": 4}
    return sorted(
        [action for action in actions if action.get("message")],
        key=lambda item: (
            priority_order.get((item.get("priority") or "").lower(), 2),
            item.get("source") or "",
            item.get("message") or "",
        ),
    )[:10]


def build_works_issue_pattern_memory(
    *,
    work_orders: list[WorkOrder],
    member_requests: list[MaintenanceRequest] | None = None,
    reopen_requests: list[WorkOrderReopenRequest] | None = None,
) -> dict[str, Any]:
    """Summarise recurring Works patterns from source records."""

    member_requests = member_requests or []
    reopen_requests = reopen_requests or []
    category_counter: Counter[str] = Counter()
    contractor_counter: Counter[str] = Counter()
    development_counter: Counter[str] = Counter()
    block_counter: Counter[str] = Counter()
    unit_groups: dict[int, list[WorkOrder]] = defaultdict(list)

    for work_order in work_orders:
        unit = work_order.unit
        client = work_order.client or (unit.client if unit and unit.client else None)
        category = _works_category(work_order)
        if category:
            category_counter[category] += 1
        if work_order.contractor_company:
            contractor_counter[work_order.contractor_company.company_name] += 1
        if client:
            development_counter[client.name] += 1
        if unit and unit.block_name:
            block_counter[_pattern_scope_label(client.name if client else None, unit.block_name)] += 1
        if work_order.unit_id:
            unit_groups[work_order.unit_id].append(work_order)

    request_category_counter = Counter(
        item.category for item in member_requests if item.category
    )
    reopen_unit_counter = Counter(
        _unit_label(item.unit) for item in reopen_requests if item.unit
    )

    patterns = {
        "units": _repeated_unit_issue_records(work_orders),
        "blocks": _counter_patterns(block_counter, "block"),
        "developments": _counter_patterns(development_counter, "development"),
        "contractors": _counter_patterns(contractor_counter, "contractor"),
        "contractor_quality": _contractor_quality_risk_records(work_orders),
        "categories": _counter_patterns(category_counter + request_category_counter, "category"),
        "reopen_units": _counter_patterns(reopen_unit_counter, "reopen_unit"),
    }
    pattern_count = sum(len(items) for items in patterns.values())
    highest_signal = _highest_pattern_signal(patterns)

    return {
        "minimum_count": PATTERN_MEMORY_MIN_COUNT,
        "pattern_count": pattern_count,
        "highest_signal": highest_signal,
        "patterns": patterns,
        "recommended_actions": _pattern_memory_recommended_actions(patterns),
        "source_references": [
            _source("WorkOrder", None, ["unit_id", "client_id", "contractor_id", "business_type", "status"]),
            _source("MaintenanceRequest", None, ["unit_id", "category", "status"]),
            _source("WorkOrderReopenRequest", None, ["unit_id", "work_order_id", "status"]),
            _source("ContractorFeedback", None, ["work_order_id", "overall_rating"]),
            _source("WorkOrderLifecycleEvent", None, ["work_order_id", "event_type", "contractor_id"]),
        ],
    }


def _development_health_snapshot(
    *,
    client: Client,
    units: list[Unit],
    work_orders: list[WorkOrder],
    maintenance_requests: list[MaintenanceRequest],
    compliance_documents: list[ClientComplianceDocument],
    latest_contract: ClientContract | None,
    works_intelligence: dict[str, Any],
) -> dict[str, Any]:
    expected_units = client.number_of_units or (
        (getattr(client, "units_apartments", 0) or 0)
        + (getattr(client, "units_commercial", 0) or 0)
        + (getattr(client, "units_other", 0) or 0)
        + (getattr(client, "units_houses", 0) or 0)
        + (getattr(client, "units_duplexes", 0) or 0)
    )
    active_units = [unit for unit in units if (unit.status or "Active") == "Active"]
    open_work_orders = [
        work_order for work_order in work_orders
        if (work_order.status or "").strip().lower() in OPEN_WORK_STATUSES or not work_order.status
    ]
    pending_member_requests = [
        item for item in maintenance_requests
        if (item.status or "").strip().lower() in OPEN_WORK_STATUSES or not item.status
    ]
    finance_ready_units = [
        unit for unit in units
        if unit.service_charge_scheme
        or unit.service_charge_percent is not None
        or unit.service_charge_amount is not None
    ]
    expired_documents = [
        document for document in compliance_documents
        if _document_expiry_date(document) and _document_expiry_date(document) < date.today()
    ]
    documents_needing_ai_review = [
        document for document in compliance_documents
        if (getattr(document, "ai_status", None) or "").strip().lower() in {"pending", "not reviewed", ""}
    ]

    signals = [
        _health_signal(
            key="unit_structure",
            label="Unit Structure",
            score=_unit_structure_score(expected_units, units),
            summary=f"{len(units)} generated unit records against {expected_units or 0} expected.",
            recommended_action="Generate or review unit records so future modules share the same unit source.",
        ),
        _health_signal(
            key="works_pressure",
            label="Works Pressure",
            score=max(0, 100 - (len(open_work_orders) * 8) - ((works_intelligence.get("attention_total") or 0) * 4)),
            summary=f"{len(open_work_orders)} open work order(s), {works_intelligence.get('attention_total') or 0} GAR attention signal(s).",
            recommended_action="Review open Works Logix pressure and GAR intelligence signals.",
        ),
        _health_signal(
            key="resident_impact",
            label="Resident Impact",
            score=max(0, 100 - (len(pending_member_requests) * 10) - ((works_intelligence.get("summary", {}).get("pending_reopen_requests") or 0) * 15)),
            summary=f"{len(pending_member_requests)} open member request(s) and {works_intelligence.get('summary', {}).get('pending_reopen_requests') or 0} pending reopen request(s).",
            recommended_action="Review Members Logix requests and any disputed closed works.",
        ),
        _health_signal(
            key="contract_status",
            label="Contract Status",
            score=_contract_health_score(latest_contract),
            summary=_contract_health_summary(latest_contract),
            recommended_action="Review contract renewal dates and value controls.",
        ),
        _health_signal(
            key="compliance_readiness",
            label="Compliance Readiness",
            score=max(0, 100 - (len(expired_documents) * 20) - (len(documents_needing_ai_review) * 5)),
            summary=f"{len(expired_documents)} expired document(s), {len(documents_needing_ai_review)} needing GAR review.",
            recommended_action="Review compliance documents, expiry dates and GAR parsing status.",
        ),
        _health_signal(
            key="finance_readiness",
            label="Finance Readiness",
            score=_percentage_score(len(finance_ready_units), len(units)),
            summary=f"{len(finance_ready_units)} of {len(units)} unit(s) have service-charge structure data.",
            recommended_action="Complete service-charge structure fields before Finance Logix relies on the data.",
        ),
    ]

    score = round(sum(signal["score"] for signal in signals) / len(signals)) if signals else 0
    status = _health_status(score)
    recommended_actions = [
        {
            "priority": signal["tone"],
            "message": signal["recommended_action"],
            "source": signal["label"],
        }
        for signal in signals
        if signal["tone"] in {"danger", "warning"}
    ]

    return {
        "score": score,
        "status": status["label"],
        "tone": status["tone"],
        "summary": {
            "expected_units": expected_units or 0,
            "generated_units": len(units),
            "active_units": len(active_units),
            "open_work_orders": len(open_work_orders),
            "member_requests": len(maintenance_requests),
            "pending_member_requests": len(pending_member_requests),
            "finance_ready_units": len(finance_ready_units),
            "expired_compliance_documents": len(expired_documents),
            "gar_pattern_memory_groups": works_intelligence.get("pattern_memory", {}).get("pattern_count", 0),
        },
        "signals": signals,
        "recommended_actions": recommended_actions,
        "source_references": [
            _source("Client", client.id, ["number_of_units", "block_names", "is_gar_monitored"]),
            _source("Unit", None, ["client_id", "status", "service_charge_scheme"]),
            _source("WorkOrder", None, ["client_id", "unit_id", "status"]),
            _source("MaintenanceRequest", None, ["unit_id", "status"]),
            _source("ClientContract", latest_contract.id if latest_contract else None, ["end_date", "contract_value", "sign_status"]),
            _source("ClientComplianceDocument", None, ["client_id", "status", "ai_status"]),
        ],
    }


def _document_expiry_date(document: ClientComplianceDocument) -> date | None:
    return getattr(document, "expires_at", None) or getattr(document, "expiry_date", None)


def _percentage_score(done: int, total: int) -> int:
    if not total:
        return 0
    return round((done / total) * 100)


def _unit_structure_score(expected_units: int | None, units: list[Unit]) -> int:
    if not expected_units:
        return 0 if not units else 80
    score = min(100, round((len(units) / expected_units) * 100))
    return score


def _contract_health_score(contract: ClientContract | None) -> int:
    if not contract:
        return 30
    if not contract.end_date:
        return 55
    days = (contract.end_date - date.today()).days
    if days < 0:
        return 20
    if days <= 30:
        return 45
    if days <= 90:
        return 65
    return 95


def _contract_health_summary(contract: ClientContract | None) -> str:
    if not contract:
        return "No active contract record found."
    if not contract.end_date:
        return "Contract exists but no end date is recorded."
    days = (contract.end_date - date.today()).days
    if days < 0:
        return f"Latest contract expired {abs(days)} day(s) ago."
    return f"Latest contract has {days} day(s) remaining."


def _health_signal(
    *,
    key: str,
    label: str,
    score: int,
    summary: str,
    recommended_action: str,
) -> dict[str, Any]:
    status = _health_status(score)
    return {
        "key": key,
        "label": label,
        "score": score,
        "status": status["label"],
        "tone": status["tone"],
        "summary": summary,
        "recommended_action": recommended_action,
    }


def _health_status(score: int) -> dict[str, str]:
    if score >= 85:
        return {"label": "Healthy", "tone": "success"}
    if score >= 70:
        return {"label": "Watch", "tone": "info"}
    if score >= 50:
        return {"label": "Needs Review", "tone": "warning"}
    return {"label": "At Risk", "tone": "danger"}


def _client_recommended_actions(
    *,
    client: Client,
    units: list[Unit],
    open_work_orders: list[WorkOrder],
    latest_contract: ClientContract | None,
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []

    if not units:
        actions.append({
            "priority": "high",
            "message": "No unit records are linked to this development.",
            "source": "Unit",
        })

    if open_work_orders:
        actions.append({
            "priority": "medium",
            "message": f"{len(open_work_orders)} open work order(s) need operational review.",
            "source": "WorkOrder",
        })

    if latest_contract and latest_contract.end_date and latest_contract.end_date < date.today():
        actions.append({
            "priority": "high",
            "message": "Latest contract appears expired.",
            "source": "ClientContract",
        })

    if not client.block_names and len(units) > 1:
        actions.append({
            "priority": "low",
            "message": "Development has multiple units but no block/core structure recorded.",
            "source": "Client",
        })

    return actions


def _development_register_actions(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    at_risk = [row for row in rows if row["tone"] == "danger"]
    needs_review = [row for row in rows if row["tone"] == "warning"]
    highest_attention = sorted(
        [row for row in rows if row["gar_attention_total"]],
        key=lambda item: item["gar_attention_total"],
        reverse=True,
    )

    if at_risk:
        actions.append({
            "priority": "high",
            "message": f"{len(at_risk)} development(s) are at risk and should be reviewed first.",
            "source": "Development Health",
        })
    if needs_review:
        actions.append({
            "priority": "medium",
            "message": f"{len(needs_review)} development(s) need review across Works, contract, compliance or finance readiness.",
            "source": "Development Health",
        })
    if highest_attention:
        top = highest_attention[0]
        actions.append({
            "priority": "medium",
            "message": f"{top['client_name']} has {top['gar_attention_total']} GAR Works attention signal(s).",
            "source": "GAR Works Intelligence",
        })

    return actions


def _filter_work_orders_for_gar(
    work_orders: list[WorkOrder],
    client_id: int | None,
    allowed_client_ids: tuple[int, ...] | None,
) -> list[WorkOrder]:
    return [
        item for item in work_orders
        if (not client_id or item.client_id == client_id)
        and (
            allowed_client_ids is None
            or item.client_id in allowed_client_ids
            or (item.unit and item.unit.client_id in allowed_client_ids)
        )
    ]


def _filter_member_requests_for_gar(
    member_requests: list[MaintenanceRequest],
    client_id: int | None,
    allowed_client_ids: tuple[int, ...] | None,
) -> list[MaintenanceRequest]:
    return [
        item for item in member_requests
        if (not client_id or (item.unit and item.unit.client_id == client_id))
        and (
            allowed_client_ids is None
            or (item.unit and item.unit.client_id in allowed_client_ids)
        )
    ]


def _filter_reopen_requests_for_gar(
    reopen_requests: list[WorkOrderReopenRequest],
    client_id: int | None,
    allowed_client_ids: tuple[int, ...] | None,
) -> list[WorkOrderReopenRequest]:
    return [
        item for item in reopen_requests
        if (not client_id or (item.unit and item.unit.client_id == client_id))
        and (
            allowed_client_ids is None
            or (item.unit and item.unit.client_id in allowed_client_ids)
        )
    ]


def _works_signal(
    *,
    key: str,
    label: str,
    severity: str,
    records: list[Any],
    anchor: str,
    detail: str,
    recommended_action: str,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "severity": severity,
        "count": len(records),
        "anchor": anchor,
        "detail": detail,
        "recommended_action": recommended_action,
        "records": [
            _works_signal_record(item)
            for item in records[:5]
        ],
    }


def _works_signal_record(item: Any) -> dict[str, Any]:
    work_order = getattr(item, "work_order", None) or item
    unit = getattr(work_order, "unit", None) or getattr(item, "unit", None)
    client = getattr(work_order, "client", None) or (unit.client if unit and unit.client else None)
    return {
        "id": getattr(item, "id", None),
        "work_order_id": getattr(work_order, "id", None),
        "title": getattr(work_order, "title", None) or getattr(item, "reason", None) or getattr(item, "title", None),
        "status": getattr(work_order, "status", None) or getattr(item, "status", None),
        "unit": _unit_label(unit) if unit else None,
        "client": client.name if client else None,
        "created_at": _iso(getattr(work_order, "created_at", None) or getattr(item, "created_at", None)),
    }


def _works_category(work_order: WorkOrder) -> str | None:
    if work_order.business_type:
        return work_order.business_type.strip()
    if work_order.request_type:
        return work_order.request_type.strip()
    if work_order.maintenance_request and work_order.maintenance_request.category:
        return work_order.maintenance_request.category.strip()
    return None


_GAR_HISTORY_STOP_WORDS = {
    "and",
    "the",
    "for",
    "with",
    "from",
    "this",
    "that",
    "work",
    "order",
    "issue",
    "problem",
    "unit",
    "apt",
    "apartment",
    "please",
    "need",
    "needs",
}


def _empty_relevant_history(work_order_id: int, audience: str) -> dict[str, Any]:
    return {
        "context_type": "work_order_relevant_history",
        "work_order_id": work_order_id,
        "audience": audience,
        "summary": {
            "related_count": 0,
            "same_unit_count": 0,
            "closed_count": 0,
            "reopen_count": 0,
            "previous_contractor_count": 0,
            "latest_reference": None,
        },
        "contractor_safe_summary": "GAR did not find related previous work for this unit/development.",
        "admin_summary": "No related work order history is currently linked by GAR.",
        "routing_recommendation": {
            "tone": "clear",
            "action": "Proceed with normal triage",
            "detail": "No related previous work has been identified by GAR.",
        },
        "records": [],
        "visibility_rules": {
            "contractor": "summary and operational completion outcome only",
            "admin": "source work order references visible",
            "restricted": ["owner finance", "private resident/member details", "internal-only notes"],
        },
        "source_references": [
            _source("WorkOrder", work_order_id, ["unit_id", "client_id", "business_type", "title", "description"]),
        ],
    }


def _related_work_score(current: WorkOrder, candidate: WorkOrder) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    current_unit = current.unit
    candidate_unit = candidate.unit

    if current.unit_id and candidate.unit_id == current.unit_id:
        score += 5
        reasons.append("Same unit")

    current_block = getattr(current_unit, "block_name", None)
    candidate_block = getattr(candidate_unit, "block_name", None)
    if current_block and candidate_block and current_block.strip().lower() == candidate_block.strip().lower():
        score += 2
        reasons.append("Same block")

    current_core = getattr(current_unit, "core_name", None)
    candidate_core = getattr(candidate_unit, "core_name", None)
    if current_core and candidate_core and current_core.strip().lower() == candidate_core.strip().lower():
        score += 1
        reasons.append("Same core")

    current_category = (_works_category(current) or "").strip().lower()
    candidate_category = (_works_category(candidate) or "").strip().lower()
    if current_category and candidate_category and current_category == candidate_category:
        score += 3
        reasons.append("Same works category")

    current_tokens = _work_order_keywords(current)
    candidate_tokens = _work_order_keywords(candidate)
    overlap = sorted(current_tokens.intersection(candidate_tokens))
    if len(overlap) >= 2:
        score += min(3, len(overlap))
        reasons.append("Similar description")

    if (candidate.status or "").strip().lower() in CLOSED_WORK_STATUSES:
        score += 1
        reasons.append("Previous closed outcome")

    if candidate.reopen_requests:
        score += 1
        reasons.append("Reopen history")

    return score, reasons


def _work_order_keywords(work_order: WorkOrder) -> set[str]:
    text = " ".join([
        work_order.title or "",
        work_order.description or "",
        work_order.business_type or "",
        work_order.request_type or "",
        work_order.maintenance_request.category if work_order.maintenance_request else "",
    ])
    tokens = set(re.findall(r"[a-zA-Z0-9]{3,}", text.lower()))
    return {
        token for token in tokens
        if token not in _GAR_HISTORY_STOP_WORDS
    }


def _related_work_record(work_order: WorkOrder, reasons: list[str], audience: str) -> dict[str, Any]:
    completion = work_order.completion
    feedback = work_order.feedback
    contractor_visible = audience == "contractor"
    completion_summary = _completion_summary_for_audience(completion, contractor_visible)
    outcome = _history_outcome(work_order, completion, contractor_visible)

    return {
        "work_order_id": work_order.id,
        "reference": f"WO-{work_order.id}",
        "title": _trim_text(work_order.title, 110),
        "status": work_order.status or "Open",
        "created_at": _iso(work_order.created_at),
        "category": _works_category(work_order),
        "unit": _unit_label(work_order.unit) if work_order.unit else None,
        "contractor": None if contractor_visible else (
            work_order.contractor_company.company_name if work_order.contractor_company else None
        ),
        "outcome": outcome,
        "completion_summary": completion_summary,
        "feedback_signal": _feedback_signal(feedback, contractor_visible),
        "reopen_count": len(work_order.reopen_requests or []),
        "match_reasons": reasons,
        "source_visible": not contractor_visible,
    }


def _completion_summary_for_audience(completion: Any | None, contractor_visible: bool) -> str | None:
    if not completion:
        return None
    if contractor_visible:
        visibility = (completion.visibility_scope or "").lower()
        if completion.access_masked or "contractor" not in visibility:
            return "Completion recorded; details restricted."
    return _trim_text(completion.parsed_summary or completion.completion_notes, 180)


def _history_outcome(work_order: WorkOrder, completion: Any | None, contractor_visible: bool) -> str:
    status = (work_order.status or "").strip()
    if completion and completion.completion_notes:
        if contractor_visible and (completion.access_masked or "contractor" not in (completion.visibility_scope or "").lower()):
            return status or "Completion recorded; details restricted."
        return _trim_text(completion.completion_notes, 130)
    if status:
        return status
    return "Previous outcome not recorded"


def _feedback_signal(feedback: Any | None, contractor_visible: bool) -> str | None:
    if not feedback:
        return None
    if contractor_visible:
        return f"Feedback recorded ({feedback.overall_rating}/5)" if feedback.overall_rating else "Feedback recorded"
    if feedback.comments:
        return _trim_text(feedback.comments, 130)
    return f"Rating {feedback.overall_rating}/5" if feedback.overall_rating else "Feedback recorded"


def _history_routing_recommendation(
    *,
    records: list[dict[str, Any]],
    same_unit_count: int,
    reopened_count: int,
    contractor_names: list[str],
) -> dict[str, str]:
    if not records:
        return {
            "tone": "clear",
            "action": "Proceed with normal triage",
            "detail": "No related previous work has been identified by GAR.",
        }
    if reopened_count:
        return {
            "tone": "warning",
            "action": "Review before routing",
            "detail": (
                f"{reopened_count} related reopen request"
                f"{'' if reopened_count == 1 else 's'} found. Check prior outcome before assigning this job."
            ),
        }
    if same_unit_count >= 2:
        return {
            "tone": "warning",
            "action": "Check for recurring fault",
            "detail": (
                f"{same_unit_count} related jobs are linked to the same unit. Consider root cause review before closure."
            ),
        }
    if contractor_names:
        return {
            "tone": "info",
            "action": "Review previous contractor context",
            "detail": (
                f"Previous related work involved {', '.join(contractor_names[:2])}. "
                "Review the outcome before deciding whether to route to the same or a different contractor."
            ),
        }
    return {
        "tone": "info",
        "action": "Use previous outcome as context",
        "detail": "Related prior work exists. Include the relevant history when briefing the contractor.",
    }


def _trim_text(value: str | None, limit: int) -> str | None:
    if not value:
        return None
    cleaned = " ".join(str(value).split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: max(0, limit - 3)].rstrip()}..."


def _pattern_scope_label(parent: str | None, value: str | None) -> str:
    value = (value or "").strip()
    if not parent:
        return value
    return f"{parent} / {value}"


def _counter_patterns(counter: Counter[str], pattern_type: str) -> list[dict[str, Any]]:
    return [
        {
            "type": pattern_type,
            "label": label,
            "count": count,
            "severity": _pattern_severity(count),
        }
        for label, count in counter.most_common()
        if label and count >= PATTERN_MEMORY_MIN_COUNT
    ]


def _pattern_severity(count: int) -> str:
    if count >= 5:
        return "high"
    if count >= 3:
        return "medium"
    return "low"


def _highest_pattern_signal(patterns: dict[str, list[dict[str, Any]]]) -> dict[str, Any] | None:
    all_patterns = [
        item
        for pattern_items in patterns.values()
        for item in pattern_items
    ]
    if not all_patterns:
        return None

    severity_rank = {"high": 3, "medium": 2, "low": 1, "clear": 0}
    return sorted(
        all_patterns,
        key=lambda item: (severity_rank.get(item.get("severity", "clear"), 0), item.get("count", 0)),
        reverse=True,
    )[0]


def _pattern_memory_recommended_actions(patterns: dict[str, list[dict[str, Any]]]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []

    if patterns["units"]:
        actions.append({
            "priority": patterns["units"][0].get("severity", "medium"),
            "message": "Review repeated unit issues for root cause, resident impact and contractor history.",
            "source": "Unit Pattern",
        })
    if patterns["blocks"]:
        actions.append({
            "priority": patterns["blocks"][0].get("severity", "medium"),
            "message": "Review block-level patterns for common area or building-system causes.",
            "source": "Block Pattern",
        })
    if patterns["contractors"]:
        actions.append({
            "priority": patterns["contractors"][0].get("severity", "low"),
            "message": "Review contractor workload and outcome trends before routing more work.",
            "source": "Contractor Pattern",
        })
    if patterns.get("contractor_quality"):
        actions.append({
            "priority": patterns["contractor_quality"][0].get("severity", "medium"),
            "message": "Review contractors with repeated returns or low feedback before assigning similar work.",
            "source": "Contractor Quality",
        })
    if patterns["categories"]:
        actions.append({
            "priority": patterns["categories"][0].get("severity", "low"),
            "message": "Review repeated works categories for planned maintenance or budget impact.",
            "source": "Category Pattern",
        })
    if patterns["reopen_units"]:
        actions.append({
            "priority": patterns["reopen_units"][0].get("severity", "medium"),
            "message": "Review units with repeated reopen requests before approving closure.",
            "source": "Reopen Pattern",
        })

    return actions


def _contractor_quality_risk_records(work_orders: list[WorkOrder]) -> list[dict[str, Any]]:
    grouped: dict[int, dict[str, Any]] = {}
    for work_order in work_orders:
        if not work_order.contractor_id or not work_order.contractor_company:
            continue

        contractor = grouped.setdefault(work_order.contractor_id, {
            "type": "contractor_quality",
            "contractor_id": work_order.contractor_id,
            "label": work_order.contractor_company.company_name,
            "count": 0,
            "repeated_return_count": 0,
            "low_feedback_count": 0,
            "latest_created_at": None,
            "work_order_ids": [],
        })

        return_count = len([
            event for event in (work_order.lifecycle_events or [])
            if (event.event_type or "").strip().lower() == "completion_returned"
        ])
        low_feedback = bool(
            work_order.feedback
            and work_order.feedback.overall_rating
            and work_order.feedback.overall_rating <= 2
        )
        if return_count < 2 and not low_feedback:
            continue

        contractor["count"] += 1
        contractor["repeated_return_count"] += int(return_count >= 2)
        contractor["low_feedback_count"] += int(low_feedback)
        contractor["work_order_ids"].append(work_order.id)
        latest = work_order.created_at
        if latest and (not contractor["latest_created_at"] or latest.isoformat() > contractor["latest_created_at"]):
            contractor["latest_created_at"] = latest.isoformat()

    records = []
    for item in grouped.values():
        if not item["count"]:
            continue
        risk_count = item["repeated_return_count"] + item["low_feedback_count"]
        item["severity"] = "high" if risk_count >= 2 else "medium"
        records.append(item)

    return sorted(
        records,
        key=lambda item: (item["severity"] == "high", item["count"], item["latest_created_at"] or ""),
        reverse=True,
    )


def _repeated_unit_issue_records(work_orders: list[WorkOrder]) -> list[dict[str, Any]]:
    grouped: dict[int, list[WorkOrder]] = {}
    for work_order in work_orders:
        if not work_order.unit_id:
            continue
        grouped.setdefault(work_order.unit_id, []).append(work_order)

    repeated = []
    for unit_id, unit_work_orders in grouped.items():
        if len(unit_work_orders) < 2:
            continue
        unit = unit_work_orders[0].unit
        client = unit.client if unit and unit.client else unit_work_orders[0].client
        repeated.append({
            "type": "unit",
            "unit_id": unit_id,
            "label": _unit_label(unit) if unit else f"Unit {unit_id}",
            "unit": _unit_label(unit) if unit else f"Unit {unit_id}",
            "client": client.name if client else None,
            "count": len(unit_work_orders),
            "severity": _pattern_severity(len(unit_work_orders)),
            "open_count": len([
                item for item in unit_work_orders
                if (item.status or "").strip().lower() in OPEN_WORK_STATUSES or not item.status
            ]),
            "latest_created_at": _iso(max(
                [item.created_at for item in unit_work_orders if item.created_at],
                default=None,
            )),
        })

    return sorted(
        repeated,
        key=lambda item: (item["count"], item["latest_created_at"] or ""),
        reverse=True,
    )


def _work_orders_with_repeated_completion_returns(work_orders: list[WorkOrder]) -> list[WorkOrder]:
    repeated = []
    for work_order in work_orders:
        return_count = len([
            event for event in (work_order.lifecycle_events or [])
            if (event.event_type or "").strip().lower() == "completion_returned"
        ])
        if return_count >= 2:
            repeated.append(work_order)

    return sorted(
        repeated,
        key=lambda item: (
            len([
                event for event in (item.lifecycle_events or [])
                if (event.event_type or "").strip().lower() == "completion_returned"
            ]),
            getattr(item, "updated_at", None) or item.created_at or datetime.min,
        ),
        reverse=True,
    )


def _work_order_recommended_actions(work_order: WorkOrder) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    status = (work_order.status or "").strip().lower()

    if status == "completion submitted":
        actions.append({
            "priority": "high",
            "message": "Contractor completion is waiting for PM/Admin review.",
            "source": "WorkOrderCompletion",
        })

    if status == "returned":
        actions.append({
            "priority": "medium",
            "message": "Work order has been returned to the contractor and needs follow-up.",
            "source": "WorkOrder",
        })

    pending_reopens = [
        request for request in (work_order.reopen_requests or [])
        if request.status == "Pending"
    ]
    if pending_reopens:
        actions.append({
            "priority": "high",
            "message": f"{len(pending_reopens)} reopen request(s) need Works Logix review.",
            "source": "WorkOrderReopenRequest",
        })

    if work_order.feedback and work_order.feedback.overall_rating and work_order.feedback.overall_rating <= 2:
        actions.append({
            "priority": "medium",
            "message": "Member/resident feedback indicates the issue may not be resolved.",
            "source": "ContractorFeedback",
        })

    if not work_order.contractor_id and status in OPEN_WORK_STATUSES:
        actions.append({
            "priority": "medium",
            "message": "Open work order has not been routed to a contractor.",
            "source": "WorkOrder",
        })

    return actions


def _work_order_operational_intelligence(
    *,
    work_order: WorkOrder,
    maintenance_request: MaintenanceRequest | None,
    completion: Any,
    feedback: Any,
    lifecycle_events: list[dict[str, Any]],
    recommended_actions: list[dict[str, str]],
) -> dict[str, Any]:
    status = (work_order.status or "").strip().lower()
    pending_reopens = [
        request for request in (work_order.reopen_requests or [])
        if request.status == "Pending"
    ]
    high_priority_actions = [
        action for action in recommended_actions
        if (action.get("priority") or "").lower() == "high"
    ]
    medium_priority_actions = [
        action for action in recommended_actions
        if (action.get("priority") or "").lower() == "medium"
    ]
    access_contexts = sorted({
        event.get("access_context")
        for event in lifecycle_events
        if event.get("access_context")
    })
    cover_events = [
        event for event in lifecycle_events
        if event.get("access_context") == "assistant_manager_cover"
    ]
    completion_submission_events = [
        event for event in lifecycle_events
        if event.get("event_type") == "completion_submitted"
    ]
    completion_return_events = [
        event for event in lifecycle_events
        if event.get("event_type") == "completion_returned"
    ]

    blockers: list[dict[str, str]] = []
    if pending_reopens:
        blockers.append({
            "source": "Members Logix",
            "message": f"{len(pending_reopens)} reopen request(s) need review before the issue can be treated as closed.",
        })
    if status == "completion submitted":
        blockers.append({
            "source": "Contractor Logix",
            "message": "Contractor completion evidence is waiting for PM/Admin approval.",
        })
    if status == "returned":
        blockers.append({
            "source": "Works Logix",
            "message": "The work order has been returned and is back with the contractor.",
        })
    if len(completion_return_events) >= 2:
        blockers.append({
            "source": "Works Logix",
            "message": "The contractor completion has been returned more than once and may need management review.",
        })
    if not work_order.contractor_id and status in OPEN_WORK_STATUSES:
        blockers.append({
            "source": "Works Logix",
            "message": "No contractor is assigned yet.",
        })
    if feedback and feedback.overall_rating and feedback.overall_rating <= 2:
        blockers.append({
            "source": "Members Logix",
            "message": "Member/resident feedback suggests the issue may not be resolved.",
        })

    current_owner = _work_order_current_owner(work_order, pending_reopens)
    recommended_next_step = _work_order_next_step(work_order, pending_reopens, feedback)
    attention_level = "clear"
    if high_priority_actions or pending_reopens or status == "completion submitted":
        attention_level = "high"
    elif medium_priority_actions or blockers or status in OPEN_WORK_STATUSES:
        attention_level = "medium"
    elif status in CLOSED_WORK_STATUSES:
        attention_level = "closed"

    return {
        "attention_level": attention_level,
        "current_owner": current_owner,
        "recommended_next_step": recommended_next_step,
        "blockers": blockers,
        "member_impact": {
            "request_source": maintenance_request.source_system if maintenance_request else work_order.source_system,
            "urgency": maintenance_request.urgency_level if maintenance_request else None,
            "privacy_scope": work_order.privacy_scope,
            "media_available": bool(
                (maintenance_request and maintenance_request.media_uploaded)
                or work_order.attachments_count
                or (completion and completion.media_uploaded)
            ),
            "feedback_rating": feedback.overall_rating if feedback else None,
            "feedback_comment": feedback.comments if feedback else None,
        },
        "contractor_signal": {
            "contractor_name": work_order.contractor_company.company_name if work_order.contractor_company else None,
            "accepted_by": work_order.accepted_contractor.full_name if work_order.accepted_contractor else None,
            "completion_submitted": bool(completion),
            "completion_evidence_count": completion.attachments_count if completion else 0,
            "returned_for_follow_up": status == "returned",
            "completion_submissions": len(completion_submission_events),
            "completion_returns": len(completion_return_events),
            "resubmissions": max(len(completion_submission_events) - 1, 0),
            "needs_management_attention": len(completion_return_events) >= 2,
        },
        "audit_signal": {
            "lifecycle_event_count": len(lifecycle_events),
            "latest_event": lifecycle_events[-1].get("title") if lifecycle_events else None,
            "source_modules": sorted({
                event.get("source") for event in lifecycle_events if event.get("source")
            }),
            "access_contexts": access_contexts,
            "cover_event_count": len(cover_events),
            "cover_context_used": bool(cover_events),
        },
    }


def _work_order_current_owner(work_order: WorkOrder, pending_reopens: list[Any]) -> dict[str, str | None]:
    status = (work_order.status or "").strip().lower()

    if pending_reopens:
        return {
            "team": "PM/Admin",
            "reason": "A member/resident has asked for the issue to be reopened.",
        }
    if status == "completion submitted":
        return {
            "team": "PM/Admin",
            "reason": "Contractor completion needs review before closure.",
        }
    if status == "returned":
        return {
            "team": "Contractor",
            "reason": "The completion was returned for follow-up.",
        }
    if work_order.contractor_id and status in OPEN_WORK_STATUSES:
        return {
            "team": "Contractor",
            "reason": "The work is routed and remains open.",
        }
    if not work_order.contractor_id and status in OPEN_WORK_STATUSES:
        return {
            "team": "Works Logix",
            "reason": "The work order needs contractor routing.",
        }
    if status in CLOSED_WORK_STATUSES:
        return {
            "team": "No active owner",
            "reason": "The work order is closed; retain the audit trail.",
        }

    return {
        "team": "Works Logix",
        "reason": "Monitor the workflow state and next update.",
    }


def _work_order_next_step(
    work_order: WorkOrder,
    pending_reopens: list[Any],
    feedback: Any,
) -> dict[str, str]:
    status = (work_order.status or "").strip().lower()

    if pending_reopens:
        return {
            "action": "Review reopen request",
            "detail": "Check the member/resident reason, evidence and lifecycle before approving or declining.",
        }
    if status == "completion submitted":
        return {
            "action": "Review contractor completion",
            "detail": "Compare evidence, notes and member feedback, then approve closure or return to contractor.",
        }
    if status == "returned":
        return {
            "action": "Await contractor follow-up",
            "detail": "Contractor should resubmit completion with clearer notes or evidence.",
        }
    if not work_order.contractor_id and status in OPEN_WORK_STATUSES:
        return {
            "action": "Route to contractor",
            "detail": "Assign the work order to a suitable contractor or team.",
        }
    if feedback and feedback.overall_rating and feedback.overall_rating <= 2:
        return {
            "action": "Validate resident outcome",
            "detail": "Low feedback should be reviewed before treating the issue as fully resolved.",
        }
    if status in CLOSED_WORK_STATUSES:
        return {
            "action": "No immediate action",
            "detail": "Keep the closure, completion evidence and lifecycle available for audit.",
        }

    return {
        "action": "Monitor progress",
        "detail": "Keep the work order visible until the next contractor or member update.",
    }


def _portfolio_recommended_actions(
    *,
    expired_contracts: list[ClientContract],
    open_work_orders: list[WorkOrder],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []

    if expired_contracts:
        actions.append({
            "priority": "high",
            "message": f"{len(expired_contracts)} expired contract(s) require review.",
            "source": "ClientContract",
        })

    if open_work_orders:
        actions.append({
            "priority": "medium",
            "message": f"{len(open_work_orders)} open work order(s) exist across the portfolio.",
            "source": "WorkOrder",
        })

    return actions
