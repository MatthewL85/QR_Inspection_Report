"""Validate declared module contracts against active Flask endpoints."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_MODULE_ITEMS = {
    "works": {
        "owned_data": {
            "work_orders",
            "work_order_lifecycle_events",
            "completion_evidence",
            "completion_reviews",
            "reopen_requests",
        },
        "shared_links": {
            "work_order_id",
            "client_id",
            "unit_id",
            "contractor_id",
            "member_request_id",
            "completion_id",
            "reopen_request_id",
            "user_id",
        },
    },
    "gar_ai": {
        "owned_data": {"context_summaries", "risk_recommendations", "explainability"},
        "shared_links": {
            "source_references",
            "visibility_rules",
            "audit_ids",
            "work_order_lifecycle_event_ids",
        },
    },
}

REQUIRED_GAR_INQUIRY_ENDPOINTS = {
    "super_admin.gar_inquiry",
    "admin_portal.gar_inquiry",
    "property_manager.gar_inquiry",
    "assistant.gar_inquiry",
    "finance.gar_inquiry",
    "director.gar_inquiry",
    "contractor.gar_inquiry",
    "members.gar_inquiry",
}


def main() -> int:
    from app import create_app
    from app.services.core.module_registry import module_contracts

    app = create_app()
    endpoints = set(app.view_functions)
    missing: list[str] = []
    contract_gaps: list[str] = []
    checked = 0

    for contract in module_contracts():
        if not contract.dashboard_endpoint:
            continue
        checked += 1
        if contract.dashboard_endpoint not in endpoints:
            missing.append(f"{contract.name}: {contract.dashboard_endpoint}")

    contracts_by_key = {contract.key: contract for contract in module_contracts()}
    for key, required in REQUIRED_MODULE_ITEMS.items():
        contract = contracts_by_key.get(key)
        if not contract:
            contract_gaps.append(f"Missing required module contract: {key}")
            continue

        missing_owned = sorted(required["owned_data"].difference(contract.owned_data))
        missing_links = sorted(required["shared_links"].difference(contract.shared_links))
        if missing_owned:
            contract_gaps.append(
                f"{contract.name} missing owned data: {', '.join(missing_owned)}"
            )
        if missing_links:
            contract_gaps.append(
                f"{contract.name} missing shared links: {', '.join(missing_links)}"
            )

    missing_gar_inquiry_endpoints = sorted(
        endpoint for endpoint in REQUIRED_GAR_INQUIRY_ENDPOINTS
        if endpoint not in endpoints
    )
    if missing_gar_inquiry_endpoints:
        contract_gaps.append(
            "GAR AI Layer missing role-scoped inquiry endpoints: "
            + ", ".join(missing_gar_inquiry_endpoints)
        )

    print("Module contract check")
    print(f"- Module contracts declared: {len(module_contracts())}")
    print(f"- Dashboard endpoints checked: {checked}")
    print(f"- GAR inquiry endpoints checked: {len(REQUIRED_GAR_INQUIRY_ENDPOINTS)}")

    if missing or contract_gaps:
        print("\nFAILED")
        for item in missing:
            print(f"- Missing endpoint: {item}")
        for item in contract_gaps:
            print(f"- Contract gap: {item}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
