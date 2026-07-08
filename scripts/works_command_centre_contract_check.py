"""Verify the Works command-centre queue/feed contract stays stable."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


EXPECTED_OPERATIONAL_QUEUES = {
    "member_request_triage",
    "unassigned_work_orders",
    "completion_review",
    "reopen_requests",
    "payment_requests",
    "contractor_follow_up",
    "repeated_returns",
}

EXPECTED_OPERATIONAL_QUEUE_FIELDS = {
    "label",
    "count",
    "anchor",
    "tone",
    "description",
    "next_action",
    "priority_rank",
}

EXPECTED_STATS = {
    "open_work_orders",
    "open_member_requests",
    "closed_work_orders",
    "total_work_orders",
    "pending_reopen_requests",
    "payment_requests",
    "unassigned_work_orders",
    "completion_review",
    "returned_work_orders",
    "contractor_follow_up",
    "repeated_returns",
    "attention_total",
}

EXPECTED_FEED_QUEUES = {
    "member_requests",
    "open_work_orders",
    "closed_work_orders",
    "unassigned_work_orders",
    "completion_review",
    "returned_work_orders",
    "contractor_follow_up",
    "repeated_returns",
    "reopen_requests",
    "payment_requests",
}

EXPECTED_GAR_KEYS = {
    "signal_count",
    "attention_total",
    "summary",
    "cover_context",
    "contractor_quality",
    "history_review",
}


def _missing(container: dict, expected: set[str]) -> set[str]:
    return expected.difference(set(container or {}))


def main() -> int:
    from app import create_app
    from app.services.works.workflow_service import (
        WorksFilters,
        build_command_centre,
        works_command_centre_payload,
    )

    app = create_app()
    failures: list[str] = []

    with app.app_context():
        filters = WorksFilters()
        # An impossible company id keeps the check read-only while still exercising
        # the service and payload builders against the real app/database model.
        data = build_command_centre(
            company_id=-999999,
            filters=filters,
            include_gar_history=True,
        )
        payload = works_command_centre_payload(
            data,
            filters,
            role_context="super_admin",
        )

    if payload.get("context_type") != "works_command_centre":
        failures.append("Works command-centre payload lost its context_type.")
    if payload.get("role_context") != "super_admin":
        failures.append("Works command-centre payload lost its role_context.")

    missing_stats = _missing(payload.get("stats", {}), EXPECTED_STATS)
    if missing_stats:
        failures.append("Missing Works stats keys: " + ", ".join(sorted(missing_stats)))

    operational_queues = payload.get("operational_queues", {})
    missing_operational = _missing(operational_queues, EXPECTED_OPERATIONAL_QUEUES)
    if missing_operational:
        failures.append("Missing operational queue definitions: " + ", ".join(sorted(missing_operational)))

    for key in EXPECTED_OPERATIONAL_QUEUES.intersection(operational_queues):
        queue = operational_queues.get(key, {})
        missing_queue_fields = _missing(queue, EXPECTED_OPERATIONAL_QUEUE_FIELDS)
        if missing_queue_fields:
            failures.append(
                f"{key} queue is missing fields: {', '.join(sorted(missing_queue_fields))}"
            )
        if not isinstance(queue.get("count"), int):
            failures.append(f"{key} queue count must be an integer.")
        if not isinstance(queue.get("priority_rank"), int):
            failures.append(f"{key} queue priority_rank must be an integer.")

    missing_feed_queues = _missing(payload.get("queues", {}), EXPECTED_FEED_QUEUES)
    if missing_feed_queues:
        failures.append("Missing Works feed queues: " + ", ".join(sorted(missing_feed_queues)))

    for queue_key, queue_items in (payload.get("queues") or {}).items():
        if not isinstance(queue_items, list):
            failures.append(f"{queue_key} feed queue must be a list.")

    missing_gar = _missing(payload.get("gar", {}), EXPECTED_GAR_KEYS)
    if missing_gar:
        failures.append("Missing Works GAR payload keys: " + ", ".join(sorted(missing_gar)))

    filters_payload = payload.get("filters", {})
    for key in ("search", "client_id", "status", "client_scope"):
        if key not in filters_payload:
            failures.append(f"Works command-centre filters missing {key}.")
    if filters_payload.get("client_scope") != "company":
        failures.append("Default Works command-centre client scope should be company.")

    print("Works command-centre contract check")
    print(f"- Operational queues checked: {len(EXPECTED_OPERATIONAL_QUEUES)}")
    print(f"- Feed queues checked: {len(EXPECTED_FEED_QUEUES)}")
    print("- GAR command-centre payload checked: yes")
    print("- Read-only service exercise checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
