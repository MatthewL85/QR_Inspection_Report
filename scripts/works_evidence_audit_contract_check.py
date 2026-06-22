"""Verify the Works Evidence and Audit Pack contract stays stable."""

from __future__ import annotations

from datetime import datetime
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


EXPECTED_COMPLETION_EVIDENCE_KEYS = {
    "submitted",
    "notes_present",
    "evidence_reference_present",
    "media_uploaded",
    "attachments_count",
    "evidence_reference_type",
    "quality_status",
    "review_flags",
    "source_references",
}

EXPECTED_SUBMITTED_EVIDENCE_KEYS = EXPECTED_COMPLETION_EVIDENCE_KEYS.union({
    "submitted_at",
    "completed_by",
    "contractor",
    "notes_excerpt",
    "evidence_reference",
    "gar_verdict",
    "gar_recommendation",
    "gar_confidence_score",
    "attachment_quality_score",
})

EXPECTED_AUDIT_PACK_KEYS = {
    "summary",
    "review_cycle",
    "completion_evidence",
    "closure_readiness",
    "access_context",
    "evidence_items",
    "source_references",
    "record_dates",
}

EXPECTED_SUMMARY_KEYS = {
    "source_request",
    "contractor_completion",
    "member_feedback",
    "reopen_requests",
    "pending_reopen_requests",
    "lifecycle_events",
    "cover_events",
    "evidence_items",
    "completion_submissions",
    "completion_returns",
}

EXPECTED_REVIEW_CYCLE_KEYS = {
    "completion_submissions",
    "completion_returns",
    "resubmissions",
    "latest_return_reason",
    "latest_returned_at",
    "needs_management_attention",
}

EXPECTED_CLOSURE_KEYS = {
    "completion_submitted",
    "evidence_available",
    "feedback_received",
    "pending_reopen_requests",
    "risk_flags",
    "ready_for_review",
}


def _missing(container: dict, expected: set[str]) -> set[str]:
    return expected.difference(set(container or {}))


def main() -> int:
    from app import create_app
    from app.models.contractor.contractor_feedback import ContractorFeedback
    from app.models.maintenance.maintenance_request import MaintenanceRequest
    from app.models.works.work_order import WorkOrder
    from app.models.works.work_order_completion import WorkOrderCompletion
    from app.models.works.work_order_lifecycle_event import WorkOrderLifecycleEvent
    from app.models.works.work_order_reopen_request import WorkOrderReopenRequest
    from app.services.works.audit_pack_service import (
        build_completion_evidence_pack,
        build_work_order_audit_pack,
    )

    app = create_app()
    failures: list[str] = []

    with app.app_context():
        missing_pack = build_completion_evidence_pack(None)
        missing_keys = _missing(missing_pack, EXPECTED_COMPLETION_EVIDENCE_KEYS)
        if missing_keys:
            failures.append("Missing empty completion evidence keys: " + ", ".join(sorted(missing_keys)))
        if missing_pack.get("quality_status") != "missing":
            failures.append("Empty completion evidence should report quality_status=missing.")
        if "No contractor completion has been submitted." not in missing_pack.get("review_flags", []):
            failures.append("Empty completion evidence lost its missing-completion review flag.")

        completion = WorkOrderCompletion(
            id=201,
            work_order_id=101,
            completed_by_id=1,
            completion_notes="Repaired leak, tested pipework and cleaned area.",
            completed_at=datetime(2026, 6, 11, 9, 0),
            external_reference="https://example.invalid/evidence/completion-photo.jpg",
            attachments_count=2,
            media_uploaded=True,
            consent_verified=True,
            access_masked=False,
            gar_verdict="Review Ready",
            gar_recommendation="Evidence is clear enough for PM review.",
            gar_confidence_score=0.91,
            attachment_quality_score=0.87,
        )
        submitted_pack = build_completion_evidence_pack(completion)
        submitted_missing = _missing(submitted_pack, EXPECTED_SUBMITTED_EVIDENCE_KEYS)
        if submitted_missing:
            failures.append("Missing submitted completion evidence keys: " + ", ".join(sorted(submitted_missing)))
        if submitted_pack.get("quality_status") != "review_ready":
            failures.append("Complete evidence should report quality_status=review_ready.")
        if submitted_pack.get("evidence_reference_type") != "image":
            failures.append("Image completion reference should be classified as image.")
        if submitted_pack.get("source_references", [{}])[0].get("model") != "WorkOrderCompletion":
            failures.append("Completion evidence lost its WorkOrderCompletion source reference.")

        work_order = WorkOrder(
            id=101,
            title="Recurring leak in riser",
            description="Water ingress reported again.",
            status="Completion Submitted",
            created_at=datetime(2026, 6, 10, 8, 30),
            company_id=1,
            client_id=2,
            unit_id=3,
        )
        member_request = MaintenanceRequest(
            id=301,
            member_id=401,
            unit_id=3,
            title="Leak reported",
            status="Converted",
            attachment_url="https://example.invalid/evidence/member-request.pdf",
            created_at=datetime(2026, 6, 9, 14, 0),
        )
        feedback = ContractorFeedback(
            id=401,
            work_order_id=101,
            contractor_id=501,
            given_by_id=601,
            overall_rating=2.0,
            comments="Still damp after visit.",
            evidence_reference="https://example.invalid/evidence/member-feedback.mp4",
            created_at=datetime(2026, 6, 11, 12, 0),
        )
        reopen_request = WorkOrderReopenRequest(
            id=501,
            work_order_id=101,
            unit_id=3,
            requested_by_member_id=401,
            reason="Issue not resolved",
            additional_details="The same area is still leaking.",
            evidence_reference="https://example.invalid/evidence/reopen-photo.png",
            status="Pending",
            created_at=datetime(2026, 6, 11, 13, 0),
        )
        events = [
            WorkOrderLifecycleEvent(
                id=601,
                work_order_id=101,
                event_type="completion_submitted",
                title="Completion submitted",
                note="Initial completion.",
                status_snapshot="Completion Submitted",
                source_module="Contractor Logix",
                event_metadata={"access_context": "assistant_manager_cover"},
                occurred_at=datetime(2026, 6, 11, 9, 5),
            ),
            WorkOrderLifecycleEvent(
                id=602,
                work_order_id=101,
                event_type="completion_returned",
                title="Completion returned",
                note="Evidence did not show the affected area.",
                status_snapshot="Returned",
                source_module="Works Logix",
                event_metadata={"access_context": "assigned_property_manager"},
                occurred_at=datetime(2026, 6, 11, 10, 0),
            ),
            WorkOrderLifecycleEvent(
                id=603,
                work_order_id=101,
                event_type="completion_returned",
                title="Completion returned again",
                note="Member reports damp remains.",
                status_snapshot="Returned",
                source_module="Works Logix",
                event_metadata={"access_context": "assigned_property_manager"},
                occurred_at=datetime(2026, 6, 11, 11, 0),
            ),
        ]

        work_order.maintenance_request = member_request
        work_order.completion = completion
        work_order.feedback = feedback
        work_order.reopen_requests = [reopen_request]
        work_order.lifecycle_events = events

        audit_pack = build_work_order_audit_pack(work_order)

    audit_missing = _missing(audit_pack, EXPECTED_AUDIT_PACK_KEYS)
    if audit_missing:
        failures.append("Missing audit pack keys: " + ", ".join(sorted(audit_missing)))

    summary = audit_pack.get("summary", {})
    summary_missing = _missing(summary, EXPECTED_SUMMARY_KEYS)
    if summary_missing:
        failures.append("Missing audit summary keys: " + ", ".join(sorted(summary_missing)))
    if summary.get("source_request") != "Yes":
        failures.append("Audit pack should detect the source member request.")
    if summary.get("contractor_completion") != "Yes":
        failures.append("Audit pack should detect contractor completion.")
    if summary.get("member_feedback") != "Yes":
        failures.append("Audit pack should detect member/resident feedback.")
    if summary.get("pending_reopen_requests") != 1:
        failures.append("Audit pack should count pending reopen requests.")
    if summary.get("evidence_items") != 4:
        failures.append("Audit pack should count request, completion, feedback and reopen evidence.")

    review_cycle = audit_pack.get("review_cycle", {})
    review_missing = _missing(review_cycle, EXPECTED_REVIEW_CYCLE_KEYS)
    if review_missing:
        failures.append("Missing review-cycle keys: " + ", ".join(sorted(review_missing)))
    if review_cycle.get("completion_returns") != 2:
        failures.append("Review cycle should count repeated completion returns.")
    if not review_cycle.get("needs_management_attention"):
        failures.append("Repeated returns should require management attention.")
    if review_cycle.get("latest_return_reason") != "Member reports damp remains.":
        failures.append("Review cycle should expose the latest return reason.")

    closure = audit_pack.get("closure_readiness", {})
    closure_missing = _missing(closure, EXPECTED_CLOSURE_KEYS)
    if closure_missing:
        failures.append("Missing closure-readiness keys: " + ", ".join(sorted(closure_missing)))
    if closure.get("ready_for_review"):
        failures.append("Pending reopen requests should prevent ready_for_review.")
    expected_flags = {
        "Member/resident feedback indicates unresolved or poor outcome.",
        "A member/resident reopen request is pending review.",
        "Completion has been returned more than once and may need management review.",
    }
    risk_flags = set(closure.get("risk_flags", []))
    missing_flags = expected_flags.difference(risk_flags)
    if missing_flags:
        failures.append("Missing closure risk flags: " + ", ".join(sorted(missing_flags)))

    access_context = audit_pack.get("access_context", {})
    if not access_context.get("cover_context_used"):
        failures.append("Audit pack should preserve Assistant Manager cover context.")
    if access_context.get("cover_event_count") != 1:
        failures.append("Audit pack should count cover lifecycle events.")

    evidence_labels = {item.get("label") for item in audit_pack.get("evidence_items", [])}
    for label in {
        "Member request media",
        "Completion evidence",
        "Member feedback evidence",
        "Reopen request evidence",
    }:
        if label not in evidence_labels:
            failures.append(f"Audit evidence list is missing {label}.")

    source_models = {item.get("model") for item in audit_pack.get("source_references", [])}
    for model in {
        "WorkOrder",
        "MaintenanceRequest",
        "WorkOrderCompletion",
        "ContractorFeedback",
        "WorkOrderReopenRequest",
        "WorkOrderLifecycleEvent",
    }:
        if model not in source_models:
            failures.append(f"Audit source references missing {model}.")

    print("Works evidence/audit contract check")
    print("- Empty completion evidence checked: yes")
    print("- Submitted completion evidence checked: yes")
    print("- Audit pack evidence sources checked: 4")
    print("- Review cycle and reopen risk checked: yes")
    print("- GAR/source reference contract checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
