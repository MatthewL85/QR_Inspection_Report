from __future__ import annotations

from typing import Any

from app.models.works.work_order_completion import WorkOrderCompletion
from app.models.works.work_order import WorkOrder


def _date_value(value):
    return value.isoformat() if value else None


def _source_reference(model: str, record_id: int | None, label: str, status: str = "") -> dict[str, Any]:
    return {
        "model": model,
        "id": record_id,
        "label": label,
        "status": status or "-",
    }


def _reference_type(reference: str | None) -> str:
    value = (reference or "").strip().lower()
    if not value:
        return "none"
    if any(value.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic")):
        return "image"
    if any(value.endswith(ext) for ext in (".mp4", ".mov", ".webm", ".avi", ".m4v")):
        return "video"
    if any(value.endswith(ext) for ext in (".pdf", ".doc", ".docx", ".xls", ".xlsx")):
        return "document"
    if value.startswith(("http://", "https://")):
        return "external_link"
    return "reference"


def _completion_evidence_links(completion: WorkOrderCompletion | None) -> list[str]:
    if not completion:
        return []
    links: list[str] = []
    extracted_data = completion.extracted_data if isinstance(completion.extracted_data, dict) else {}
    for value in [completion.external_reference, *(extracted_data.get("evidence_links") or [])]:
        value = (value or "").strip()
        if value and value not in links:
            links.append(value)
    return links


def build_completion_evidence_pack(completion: WorkOrderCompletion | None) -> dict[str, Any]:
    """Build a GAR-readable completion evidence assessment."""
    if not completion:
        return {
            "submitted": False,
            "notes_present": False,
            "evidence_reference_present": False,
            "media_uploaded": False,
            "attachments_count": 0,
            "evidence_reference_type": "none",
            "quality_status": "missing",
            "review_flags": ["No contractor completion has been submitted."],
            "source_references": [],
        }

    evidence_links = _completion_evidence_links(completion)
    evidence_reference = evidence_links[0] if evidence_links else ""
    notes_present = bool((completion.completion_notes or "").strip())
    attachments_count = max(completion.attachments_count or 0, len(evidence_links))
    evidence_present = bool(evidence_reference) or bool(completion.media_uploaded) or attachments_count > 0
    review_flags = []
    if not notes_present:
        review_flags.append("Completion notes are missing.")
    if not evidence_present:
        review_flags.append("Completion evidence reference or media is missing.")
    if completion.access_masked:
        review_flags.append("Completion access is masked and may need authorised review.")
    if not completion.consent_verified:
        review_flags.append("Completion consent has not been verified.")

    if not evidence_present:
        quality_status = "missing_evidence"
    elif review_flags:
        quality_status = "needs_review"
    else:
        quality_status = "review_ready"

    return {
        "submitted": True,
        "submitted_at": _date_value(completion.completed_at),
        "completed_by": completion.completed_by.full_name if completion.completed_by else None,
        "contractor": completion.contractor.company_name if completion.contractor else None,
        "notes_present": notes_present,
        "notes_excerpt": (completion.completion_notes or "").strip()[:240],
        "evidence_reference_present": bool(evidence_reference),
        "evidence_reference_type": _reference_type(evidence_reference),
        "evidence_reference": evidence_reference or None,
        "evidence_links": evidence_links,
        "media_uploaded": bool(completion.media_uploaded),
        "attachments_count": attachments_count,
        "quality_status": quality_status,
        "review_flags": review_flags,
        "gar_verdict": completion.gar_verdict,
        "gar_recommendation": completion.gar_recommendation,
        "gar_confidence_score": completion.gar_confidence_score,
        "attachment_quality_score": completion.attachment_quality_score,
        "source_references": [
            _source_reference("WorkOrderCompletion", completion.id, "Contractor completion", quality_status),
        ],
    }


def build_work_order_audit_pack(work_order: WorkOrder) -> dict[str, Any]:
    """Build a source-record audit pack for PM/Admin review and GAR context."""

    maintenance_request = work_order.maintenance_request
    completion = work_order.completion
    completion_evidence = build_completion_evidence_pack(completion)
    feedback = work_order.feedback
    reopen_requests = list(work_order.reopen_requests or [])
    lifecycle_events = list(work_order.lifecycle_events or [])

    evidence_items = []
    if maintenance_request:
        request_links = []
        for value in [
            maintenance_request.attachment_url,
            *(maintenance_request.doc_links or []),
            *(maintenance_request.photo_links or []),
        ]:
            value = (value or "").strip()
            if value and value not in request_links:
                request_links.append(value)
        for index, reference in enumerate(request_links, start=1):
            evidence_items.append({
                "source": "Members Logix",
                "label": f"Member request media {index}",
                "reference": reference,
            })
    for index, reference in enumerate(_completion_evidence_links(completion), start=1):
        evidence_items.append({
            "source": "Contractor Logix",
            "label": f"Completion evidence {index}",
            "reference": reference,
        })
    if feedback and feedback.evidence_reference:
        evidence_items.append({
            "source": "Members Logix",
            "label": "Member feedback evidence",
            "reference": feedback.evidence_reference,
        })
    for reopen_request in work_order.reopen_requests or []:
        if reopen_request.evidence_reference:
            evidence_items.append({
                "source": "Members Logix",
                "label": "Reopen request evidence",
                "reference": reopen_request.evidence_reference,
            })

    pending_reopen_requests = [
        item for item in reopen_requests
        if (item.status or "").strip().lower() == "pending"
    ]
    access_contexts = [
        (item.event_metadata or {}).get("access_context")
        for item in lifecycle_events
        if (item.event_metadata or {}).get("access_context")
    ]
    cover_events = [
        item for item in lifecycle_events
        if (item.event_metadata or {}).get("access_context") == "assistant_manager_cover"
    ]
    completion_submit_events = [
        item for item in lifecycle_events
        if (item.event_type or "").strip().lower() == "completion_submitted"
    ]
    completion_return_events = [
        item for item in lifecycle_events
        if (item.event_type or "").strip().lower() == "completion_returned"
    ]
    latest_return_event = (
        sorted(
            completion_return_events,
            key=lambda item: item.occurred_at or item.created_at,
            reverse=True,
        )[0]
        if completion_return_events
        else None
    )

    risk_flags = []
    if not lifecycle_events:
        risk_flags.append("No lifecycle events recorded yet.")
    if completion or (work_order.status or "").strip().lower() == "completion submitted":
        for flag in completion_evidence.get("review_flags", []):
            if flag not in risk_flags:
                risk_flags.append(flag)
    if feedback and feedback.overall_rating and feedback.overall_rating <= 2:
        risk_flags.append("Member/resident feedback indicates unresolved or poor outcome.")
    if pending_reopen_requests:
        risk_flags.append("A member/resident reopen request is pending review.")
    if len(completion_return_events) >= 2:
        risk_flags.append("Completion has been returned more than once and may need management review.")

    source_references = [
        _source_reference("WorkOrder", work_order.id, "Works Logix work order", work_order.status),
    ]
    if maintenance_request:
        source_references.append(
            _source_reference("MaintenanceRequest", maintenance_request.id, "Members Logix request", maintenance_request.status)
        )
    if completion:
        source_references.append(
            _source_reference("WorkOrderCompletion", completion.id, "Contractor completion", "Submitted")
        )
    if feedback:
        source_references.append(
            _source_reference("ContractorFeedback", feedback.id, "Member/resident feedback", f"{feedback.overall_rating}/5")
        )
    for reopen_request in reopen_requests:
        source_references.append(
            _source_reference("WorkOrderReopenRequest", reopen_request.id, "Reopen request", reopen_request.status)
        )
    for lifecycle_event in cover_events:
        source_references.append(
            _source_reference(
                "WorkOrderLifecycleEvent",
                lifecycle_event.id,
                "Assistant cover action",
                lifecycle_event.status_snapshot or lifecycle_event.event_type,
            )
        )

    return {
        "summary": {
            "source_request": "Yes" if maintenance_request else "No",
            "contractor_completion": "Yes" if completion else "No",
            "member_feedback": "Yes" if feedback else "No",
            "reopen_requests": len(reopen_requests),
            "pending_reopen_requests": len(pending_reopen_requests),
            "lifecycle_events": len(lifecycle_events),
            "cover_events": len(cover_events),
            "evidence_items": len(evidence_items),
            "completion_submissions": len(completion_submit_events),
            "completion_returns": len(completion_return_events),
        },
        "review_cycle": {
            "completion_submissions": len(completion_submit_events),
            "completion_returns": len(completion_return_events),
            "resubmissions": max(len(completion_submit_events) - 1, 0),
            "latest_return_reason": latest_return_event.note if latest_return_event else None,
            "latest_returned_at": _date_value(latest_return_event.occurred_at) if latest_return_event else None,
            "needs_management_attention": len(completion_return_events) >= 2,
        },
        "completion_evidence": completion_evidence,
        "closure_readiness": {
            "completion_submitted": bool(completion),
            "evidence_available": bool(evidence_items),
            "feedback_received": bool(feedback),
            "pending_reopen_requests": len(pending_reopen_requests),
            "risk_flags": risk_flags,
            "ready_for_review": bool(completion) and not pending_reopen_requests,
        },
        "access_context": {
            "contexts": sorted(set(access_contexts)),
            "cover_context_used": bool(cover_events),
            "cover_event_count": len(cover_events),
        },
        "evidence_items": evidence_items,
        "source_references": source_references,
        "record_dates": {
            "work_order_created": _date_value(work_order.created_at),
            "request_created": _date_value(maintenance_request.created_at) if maintenance_request else None,
            "completion_submitted": _date_value(completion.completed_at) if completion else None,
            "feedback_submitted": _date_value(feedback.created_at) if feedback else None,
        },
    }
