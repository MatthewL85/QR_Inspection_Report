"""Verify tile-driven operational queue surfaces do not regress into long duplicate pages."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTOR_QUEUE = ROOT / "app" / "templates" / "contractor" / "work_orders.html"
CONTRACTOR_DASHBOARD = ROOT / "app" / "templates" / "contractor_dashboard.html"
CONTRACTOR_PACK = ROOT / "app" / "templates" / "contractor" / "work_order_detail.html"
CONTRACTOR_DOCKET = ROOT / "app" / "templates" / "contractor" / "job_docket_detail.html"
CONTRACTOR_ROUTES = ROOT / "app" / "routes" / "contractor.py"
CONTRACTOR_KEY_INFO_ROUTES = ROOT / "app" / "routes" / "contractor" / "key_info.py"
CONTRACTOR_ACCESS = ROOT / "app" / "services" / "core" / "contractor_access.py"
JOB_DOCKET_SERVICE = ROOT / "app" / "services" / "contractor" / "job_docket_service.py"
WORKS_COMMAND_CENTRE = ROOT / "app" / "templates" / "works" / "_command_centre.html"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE))


def _require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def _check_contractor_queue(text: str, failures: list[str]) -> None:
    expected_queues = {
        "assigned": "New Assignments",
        "quote_requests": "Quotation Requests",
        "active": "Active",
        "submitted": "Submitted",
        "returned": "Returned",
        "to_be_invoiced": "To Be Invoiced",
        "closed": "Closed / Paid",
    }

    _require("macro queue_tile" in text, "Contractor queue must use the shared queue_tile macro.", failures)
    _require("contractor-work-summary-grid" in text, "Contractor queue tiles must remain in the summary grid.", failures)
    _require("contractor-work-filter-panel" in text, "Contractor queue filters must remain separate from the data lists.", failures)
    _require("Needs Attention" not in text, "Contractor work queue should not reintroduce duplicated Needs Attention tiles.", failures)

    for key, label in expected_queues.items():
        _require(f"queue_tile('{key}', '{label}'" in text, f"Missing contractor queue tile: {label}.", failures)
        _require(
            f"selected_queue == '{key}'" in text,
            f"Contractor queue list for {label} must be gated by selected_queue.",
            failures,
        )

    _require(
        "mark_job_docket_invoice_prepared" in text and "Send Request" in text,
        "Contractor To Be Invoiced queue must expose the payment-request handoff action.",
        failures,
    )

    ungated_sections = _count(r"^\s*<section class=\"contract-manager-panel\"", text)
    gated_sections = _count(r"^\s*\{%\s*if selected_queue ==", text)
    _require(
        gated_sections >= 7 and ungated_sections <= gated_sections + 1,
        "Contractor queue lists should render one selected queue at a time, not a long stacked page.",
        failures,
    )

    _require(
        _count(r"Track lifecycle", text) >= 5,
        "Contractor queue sections should retain collapsible lifecycle access.",
        failures,
    )


def _check_contractor_dashboard(text: str, failures: list[str]) -> None:
    _require(
        _count(r"New Job Docket", text) == 1,
        "Contractor dashboard should expose one clear New Job Docket action only.",
        failures,
    )
    for queue in ("quote_requests", "to_be_invoiced"):
        _require(
            f"queue='{queue}'" in text,
            f"Contractor dashboard must link to the {queue} queue tile.",
            failures,
        )


def _check_contractor_pack(text: str, failures: list[str]) -> None:
    _require(
        "active_quote_invite" in text,
        "Contractor pack must gate live quote actions behind active_quote_invite.",
        failures,
    )
    _require(
        "quote_outcome" in text and "Quote Outcome" in text,
        "Contractor pack must show selected/not-selected quote outcomes.",
        failures,
    )
    _require(
        "can_manage_work_order and not active_quote_invite" in text,
        "Contractor pack must only show accept/reject work-order controls to the assigned contractor after quote selection.",
        failures,
    )


def _check_contractor_docket(text: str, service_text: str, route_text: str, failures: list[str]) -> None:
    _require(
        "selected_quote_response" in text and "Approved Quote Basis" in text,
        "Contractor job docket must show the approved quote basis when a quote-selected work order is accepted.",
        failures,
    )
    _require(
        "Payment Request" in text and "Send Payment Request" in text,
        "Contractor job docket must show the payment-request handoff panel.",
        failures,
    )
    _require(
        "mark_job_docket_invoice_prepared" in route_text and "contractor_invoice_prepared" in route_text,
        "Contractor routes must record the invoice-prepared lifecycle handoff.",
        failures,
    )
    _require(
        "quotation_reference" in service_text and "Quote Approved" in service_text,
        "Job docket service must carry approved quote metadata into the docket for future Finance Logix handoff.",
        failures,
    )


def _check_contractor_access(route_text: str, key_info_text: str, access_text: str, failures: list[str]) -> None:
    _require(
        "contractor_portal_denial_reason" in route_text,
        "Main Contractor Logix routes must enforce the contractor portal boundary helper.",
        failures,
    )
    _require(
        "property_management_company" in access_text and "missing_contractor_profile" in access_text,
        "Contractor access helper must reject property-management companies and users without a contractor profile.",
        failures,
    )
    _require(
        "can_access_contractor_portal(current_user)" in key_info_text,
        "Contractor key-info routes must use the shared Contractor Logix access helper.",
        failures,
    )
    _require(
        '("contractor_id", "contractorId")' in key_info_text and '"company_id"' not in key_info_text,
        "Contractor key-info routes must not treat a management company_id as a contractor id.",
        failures,
    )


def _check_works_command_centre(text: str, failures: list[str]) -> None:
    expected_queues = {
        "open": "Open Work Orders",
        "member_requests": "Member Requests",
        "quote_requests": "Quote Requests",
        "closed": "Closed",
        "payment_requests": "Payment Requests",
        "reopen": "Reopen Requests",
        "gar": "GAR Signals",
    }

    _require(
        "selected_queue = request.args.get('queue', 'open')" in text,
        "Works command centre must derive selected_queue from the tile route.",
        failures,
    )
    _require(
        "works-filter-disclosure" in text,
        "Works command centre filters must stay collapsed behind a disclosure control.",
        failures,
    )
    _require(
        "Show prioritised next actions" not in text and "Needs Attention" not in text,
        "Works command centre should not reintroduce duplicated attention/list sections.",
        failures,
    )

    for key, label in expected_queues.items():
        _require(
            f"queue='{key}'" in text and label in text,
            f"Missing Works command tile: {label}.",
            failures,
        )
        _require(
            f"selected_queue == '{key}'" in text,
            f"Works list for {label} must be gated by selected_queue.",
            failures,
        )

    _require(
        "request_quotes_endpoint" in text and "works-quote-request-form" in text,
        "Works command centre must expose a controlled role-routed request-quotes workflow from open work orders.",
        failures,
    )
    _require(
        "select_quote_endpoint" in text and "works-select-quote-form" in text,
        "Works command centre must expose a controlled role-routed select-quote workflow from quote requests.",
        failures,
    )
    _require(
        "work_order_payment_request_document" in text and "Preview Request" in text,
        "Works Payment Requests queue must expose a management-safe payment request document preview.",
        failures,
    )
    _require(
        _count(r"^\s*<section class=\"contract-manager-panel\"", text) <= 7,
        "Works command centre should not stack every queue list on one page.",
        failures,
    )


def main() -> int:
    failures: list[str] = []
    contractor_queue = _read(CONTRACTOR_QUEUE)
    contractor_dashboard = _read(CONTRACTOR_DASHBOARD)
    contractor_pack = _read(CONTRACTOR_PACK)
    contractor_docket = _read(CONTRACTOR_DOCKET)
    contractor_routes = _read(CONTRACTOR_ROUTES)
    contractor_key_info_routes = _read(CONTRACTOR_KEY_INFO_ROUTES)
    contractor_access = _read(CONTRACTOR_ACCESS)
    job_docket_service = _read(JOB_DOCKET_SERVICE)
    works_command_centre = _read(WORKS_COMMAND_CENTRE)

    _check_contractor_queue(contractor_queue, failures)
    _check_contractor_dashboard(contractor_dashboard, failures)
    _check_contractor_pack(contractor_pack, failures)
    _check_contractor_docket(contractor_docket, job_docket_service, contractor_routes, failures)
    _check_contractor_access(contractor_routes, contractor_key_info_routes, contractor_access, failures)
    _check_works_command_centre(works_command_centre, failures)

    print("Queue surface contract check")
    print("- Contractor tile-driven queues checked: yes")
    print("- Contractor dashboard action links checked: yes")
    print("- Contractor quote pack state gating checked: yes")
    print("- Contractor quote-to-docket handoff checked: yes")
    print("- Contractor invoice-readiness handoff checked: yes")
    print("- Contractor portal access boundary checked: yes")
    print("- Works Logix tile-driven queues checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
