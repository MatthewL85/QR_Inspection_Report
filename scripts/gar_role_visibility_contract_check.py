"""Verify GAR role visibility boundaries for external-facing roles."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    from app.services.gar import build_gar_capability_registry, build_gar_inquiry_response
    from app.services.gar.source_queries import (
        build_client_unit_source_query,
        build_contractor_works_source_query,
        build_member_works_source_query,
    )

    failures: list[str] = []

    forbidden_registry = {
        "contractor": {"contracts", "finance", "team_hr", "governance", "documents"},
        "member": {"contracts", "team_hr", "governance"},
        "resident": {"contracts", "finance", "team_hr", "governance"},
        "finance": {"team_hr", "governance"},
        "director": {"team_hr"},
    }
    registries_checked = 0
    for role_context, forbidden_keys in forbidden_registry.items():
        registry = build_gar_capability_registry(role_context=role_context)
        registries_checked += 1
        visible_keys = {
            item.get("key")
            for item in registry.get("capabilities", [])
        }
        leaked = sorted(forbidden_keys.intersection(visible_keys))
        if leaked:
            failures.append(f"{role_context} registry exposed forbidden capabilities: {', '.join(leaked)}")

    blocked_cases = (
        ("contractor", "Show the service charge balance for this owner", "finance"),
        ("contractor", "Who is active in the team directory?", "team_hr"),
        ("contractor", "Which developments have governance attention signals?", "governance"),
        ("contractor", "Which contracts are expired?", "contracts"),
        ("member", "Who is active in the team directory?", "team_hr"),
        ("member", "Which contracts are expired?", "contracts"),
        ("resident", "Tell me the debtors in Matthew Lavery", "finance"),
        ("resident", "Which developments have governance attention signals?", "governance"),
    )
    blocked_inquiries_checked = 0
    for role_context, question, expected_domain in blocked_cases:
        response = build_gar_inquiry_response(question, role_context=role_context)
        blocked_inquiries_checked += 1
        readiness = response.get("readiness", {})
        if readiness.get("domain") != expected_domain:
            failures.append(
                f"{role_context} blocked question classified as {readiness.get('domain')}, expected {expected_domain}"
            )
        if response.get("response_status") != "permission_blocked":
            failures.append(
                f"{role_context} {expected_domain} inquiry returned {response.get('response_status')}, expected permission_blocked"
            )

    contractor_query = build_contractor_works_source_query(
        user_id=None,
        role_context="contractor",
        question="Show my assigned work orders",
    )
    contractor_visibility = contractor_query.get("visibility", {})
    if contractor_query.get("query_ready") is False and contractor_query.get("error") != "user_context_missing":
        failures.append("Contractor Works query did not fail safely without user context")
    for key in ("management_quality_records_included", "member_private_contact_included", "finance_records_included"):
        if contractor_visibility.get(key):
            failures.append(f"Contractor Works query exposed forbidden visibility flag: {key}")

    member_query = build_member_works_source_query(
        user_id=None,
        role_context="member",
        question="Show my linked work orders",
    )
    member_visibility = member_query.get("visibility", {})
    if member_query.get("query_ready") is False and member_query.get("error") != "user_context_missing":
        failures.append("Member Works query did not fail safely without user context")
    for key in ("owner_finance_records_included", "other_member_records_included", "management_quality_records_included"):
        if member_visibility.get(key):
            failures.append(f"Member Works query exposed forbidden visibility flag: {key}")

    client_unit_query = build_client_unit_source_query(
        company_id=None,
        role_context="contractor",
        question="Summarise this development and units",
    )
    if client_unit_query.get("query_ready") is False and client_unit_query.get("error") != "company_context_missing":
        failures.append("Contractor client/unit query did not fail safely without company context")

    print("GAR role visibility contract check")
    print(f"- Role registries checked: {registries_checked}")
    print(f"- Blocked inquiries checked: {blocked_inquiries_checked}")
    print("- External-role visibility flags checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
