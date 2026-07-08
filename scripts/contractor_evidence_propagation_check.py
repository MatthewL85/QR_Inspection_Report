"""Verify contractor-facing evidence stays openable across Works Logix."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


EXPECTED_MEMBER_REFERENCES = {
    "/static/uploads/member_requests/9101/photo.jpg": "image",
    "https://example.invalid/evidence/report.pdf": "document",
    "/static/uploads/member_requests/9101/site-video.mp4": "video",
}

EXPECTED_TEMPLATE_TOKENS = {
    "app/templates/contractor/work_order_detail.html": [
        "docket.evidence_items",
        "works-evidence-link",
        "item.reference_url",
        "Open Evidence",
        "contractor-evidence-preview",
    ],
    "app/templates/contractor/job_docket_detail.html": [
        "work_pack.evidence_items",
        "works-evidence-link",
        "item.reference_url",
        "Open Evidence",
    ],
    "app/templates/units/work_order_review.html": [
        "work_order_audit_pack.evidence_items",
        "works-evidence-link",
        "Open Evidence",
    ],
    "app/templates/works/member_request_detail.html": [
        "works-evidence-link",
        "Open attached evidence",
    ],
}


def _fail_if_missing_template_tokens(failures: list[str]) -> None:
    for relative_path, expected_tokens in EXPECTED_TEMPLATE_TOKENS.items():
        template_path = PROJECT_ROOT / relative_path
        if not template_path.exists():
            failures.append(f"Template missing: {relative_path}")
            continue

        content = template_path.read_text(encoding="utf-8")
        for token in expected_tokens:
            if token not in content:
                failures.append(f"{relative_path} is missing contractor evidence token: {token}")


def main() -> int:
    from app import create_app
    from app.models.maintenance.maintenance_request import MaintenanceRequest
    from app.models.works.work_order import WorkOrder
    from app.models.works.work_order_completion import WorkOrderCompletion
    from app.services.works.work_order_docket_service import build_contractor_work_order_docket

    app = create_app()
    failures: list[str] = []

    with app.app_context():
        member_request = MaintenanceRequest(
            id=9101,
            member_id=1,
            unit_id=None,
            title="Evidence propagation request",
            description="Resident uploaded media that must follow the job.",
            category="Plumbing",
            urgency_level="Urgent",
            status="Converted",
            attachment_url="/static/uploads/member_requests/9101/photo.jpg",
            doc_links=["https://example.invalid/evidence/report.pdf"],
            photo_links=["/static/uploads/member_requests/9101/site-video.mp4"],
            created_at=datetime(2026, 7, 1, 9, 0),
        )
        completion = WorkOrderCompletion(
            id=9201,
            work_order_id=9001,
            completed_by_id=1,
            completion_notes="Completion uploaded with before and after evidence.",
            external_reference="https://example.invalid/evidence/completion-photo.png",
            extracted_data={"evidence_links": ["/static/uploads/work_orders/9001/completion-video.mp4"]},
            attachments_count=2,
            media_uploaded=True,
            consent_verified=True,
            completed_at=datetime(2026, 7, 1, 16, 30),
        )
        work_order = WorkOrder(
            id=9001,
            title="Evidence propagation work order",
            description="Confirm member evidence appears in contractor-facing views.",
            request_type="Work Order",
            business_type="Plumbing",
            status="Accepted",
            attachments_count=1,
            created_at=datetime(2026, 7, 1, 10, 0),
        )
        work_order.maintenance_request = member_request
        work_order.completion = completion
        work_order.lifecycle_events = []

        docket = build_contractor_work_order_docket(work_order)
        evidence_items = docket.get("evidence_items") or []

        if len(evidence_items) < 6:
            failures.append(f"Expected at least 6 evidence items, found {len(evidence_items)}.")

        member_items = [item for item in evidence_items if item.get("source") == "Members Logix"]
        if len(member_items) != 3:
            failures.append(f"Expected 3 Members Logix evidence items, found {len(member_items)}.")

        for reference, expected_type in EXPECTED_MEMBER_REFERENCES.items():
            item = next((candidate for candidate in member_items if candidate.get("reference") == reference), None)
            if not item:
                failures.append(f"Missing propagated member evidence reference: {reference}")
                continue
            if item.get("display_reference") != "Open evidence":
                failures.append(f"Member evidence {reference} is not displayed as Open evidence.")
            if item.get("reference_url") != reference:
                failures.append(f"Member evidence {reference} does not expose a clickable reference_url.")
            if item.get("reference_type") != expected_type:
                failures.append(
                    f"Member evidence {reference} should be classified as {expected_type}, "
                    f"got {item.get('reference_type')}."
                )

        works_item = next((item for item in evidence_items if item.get("source") == "Works Logix"), None)
        if not works_item or works_item.get("display_reference") != "1 attachment(s) recorded":
            failures.append("Works Logix attachment count was not preserved as a contractor-facing evidence item.")

        contractor_items = [item for item in evidence_items if item.get("source") == "Contractor Logix"]
        if len(contractor_items) != 2:
            failures.append(f"Expected 2 Contractor Logix completion evidence items, found {len(contractor_items)}.")
        for item in contractor_items:
            if item.get("display_reference") != "Open evidence" or not item.get("reference_url"):
                failures.append("Contractor completion evidence should remain openable in the contractor pack.")

    _fail_if_missing_template_tokens(failures)

    if failures:
        print("FAILED: Contractor evidence propagation contract failed")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASSED: Contractor evidence propagation contract is stable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
