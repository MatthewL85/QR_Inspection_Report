"""Verify governed Phase 3 workflow actions stay POST-only."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


EXPECTED_ACTION_ENDPOINTS = {
    "super_admin.convert_member_request_to_work_order": "/super-admin/work-orders/member-requests/<int:request_id>/convert",
    "super_admin.assign_work_order_contractor": "/super-admin/work-orders/<int:work_order_id>/assign-contractor",
    "admin_portal.convert_member_request": "/admin-portal/work-orders/member-requests/<int:request_id>/convert",
    "admin_portal.assign_work_order_contractor": "/admin-portal/work-orders/<int:work_order_id>/assign-contractor",
    "property_manager.convert_member_request": "/pm/work-orders/member-requests/<int:request_id>/convert",
    "property_manager.assign_work_order_contractor": "/pm/work-orders/<int:work_order_id>/assign-contractor",
    "assistant.convert_member_request": "/assistant/work-orders/member-requests/<int:request_id>/convert",
    "assistant.assign_work_order_contractor": "/assistant/work-orders/<int:work_order_id>/assign-contractor",
    "contractor.update_work_order": "/contractor/work-orders/<int:work_order_id>/<action>",
    "contractor.add_progress_update": "/contractor/work-orders/<int:work_order_id>/progress",
    "contractor.schedule_job_docket": "/contractor/job-dockets/<int:docket_id>/schedule",
    "members.create_maintenance_request": "/members/works/requests",
    "members.submit_work_order_feedback": "/members/works/<int:work_order_id>/feedback",
    "members.request_reopen": "/members/works/<int:work_order_id>/reopen",
    "unit_bp.work_order_reopen": "/units/<int:unit_id>/work-orders/<int:work_order_id>/reopen",
    "unit_bp.reopen_request_approve": "/units/reopen-requests/<int:request_id>/approve",
    "unit_bp.reopen_request_reject": "/units/reopen-requests/<int:request_id>/reject",
    "notifications.mark_read": "/notifications/<int:notification_id>/mark-read",
    "notifications.mark_all_read": "/notifications/mark-all-read",
}


def main() -> int:
    from app import create_app

    app = create_app()
    failures: list[str] = []
    rules_by_endpoint = {rule.endpoint: rule for rule in app.url_map.iter_rules()}

    for endpoint, expected_rule in sorted(EXPECTED_ACTION_ENDPOINTS.items()):
        rule = rules_by_endpoint.get(endpoint)
        if not rule:
            failures.append(f"Missing governed action endpoint: {endpoint}")
            continue
        if rule.rule != expected_rule:
            failures.append(f"{endpoint} route changed from {expected_rule} to {rule.rule}")

        methods = set(rule.methods or set())
        if "POST" not in methods:
            failures.append(f"{endpoint} does not allow POST")
        if "GET" in methods:
            failures.append(f"{endpoint} allows GET but lifecycle actions must be POST-only")
        forbidden_methods = {"PUT", "PATCH", "DELETE"}.intersection(methods)
        if forbidden_methods:
            failures.append(
                f"{endpoint} allows undeclared mutating methods: {', '.join(sorted(forbidden_methods))}"
            )

    print("Workflow action contract check")
    print(f"- Governed action endpoints checked: {len(EXPECTED_ACTION_ENDPOINTS)}")
    print("- POST-only lifecycle action contract checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
