"""Verify GAR capability readiness and source adapter coverage.

GAR must only answer from source-backed module records. This check protects
that contract by ensuring query-ready domains have declared adapters, while
not-ready domains stay behind the readiness gate.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


READY_STATUSES = {"available", "available_partial"}


def main() -> int:
    from app import create_app
    from app.models.client.client import Client
    from app.models.core.user import User
    from app.models.members.member import Member
    from app.models.onboarding.company import Company
    from app.services.gar.capability_registry import (
        CAPABILITIES,
        ROLE_ALL,
        build_gar_answer_readiness,
        build_gar_capability_registry,
    )
    from app.services.gar.inquiry import SOURCE_ADAPTERS, build_gar_inquiry_response

    from app.services.gar.source_queries import (
        _notification_source_references,
        build_client_unit_source_query,
        build_contract_source_query,
        build_contractor_works_source_query,
        build_document_source_query,
        build_governance_source_query,
        build_member_works_source_query,
        build_notification_source_query,
        build_platform_setup_source_query,
        build_team_source_query,
        build_works_source_query,
    )

    failures: list[str] = []
    capability_keys = {capability.key for capability in CAPABILITIES}
    failure_envelopes_checked = 0
    ready_envelopes_checked = 0
    source_references_checked = 0

    for capability in CAPABILITIES:
        is_query_ready = capability.source_backed and capability.status in READY_STATUSES
        if is_query_ready and capability.key not in SOURCE_ADAPTERS:
            failures.append(f"{capability.key} is query-ready but has no declared source adapter")
        if not capability.source_backed and capability.key in SOURCE_ADAPTERS:
            response = build_gar_inquiry_response(
                capability.not_ready_examples[0] if capability.not_ready_examples else capability.name,
                role_context=(capability.role_visibility[0] if capability.role_visibility else "super_admin"),
            )
            if response.get("response_status") == "ready_for_source_query":
                failures.append(f"{capability.key} is not source-backed but was marked ready for source query")

    extra_adapters = set(SOURCE_ADAPTERS) - capability_keys
    if extra_adapters:
        failures.append(f"Source adapters declared without capabilities: {', '.join(sorted(extra_adapters))}")

    for role in ROLE_ALL:
        registry = build_gar_capability_registry(role_context=role)
        for item in registry.get("capabilities", []):
            if item.get("status") in READY_STATUSES and item.get("source_backed"):
                readiness = build_gar_answer_readiness(
                    item.get("can_answer_examples", [item["name"]])[0],
                    role_context=role,
                )
                if not readiness.get("role_allowed"):
                    failures.append(f"{role} received {item['key']} in registry but readiness blocks role")

    finance_readiness = build_gar_answer_readiness(
        "Tell me the debtors in Matthew Lavery and how much of the budget has been spent",
        role_context="finance",
    )
    if finance_readiness.get("domain") != "finance":
        failures.append("Finance debtor/budget question did not classify as finance")
    if finance_readiness.get("answer_ready"):
        failures.append("Finance debtor/budget question was incorrectly marked answer-ready")

    finance_inquiry = build_gar_inquiry_response(
        "Tell me the debtors in Matthew Lavery and how much of the budget has been spent",
        role_context="finance",
        execute_source_query=True,
    )
    if finance_inquiry.get("response_status") != "not_query_ready":
        failures.append("Finance inquiry did not stay behind the not-query-ready gate")
    if finance_inquiry.get("answer") is not None:
        failures.append("Finance inquiry returned an answer before Finance Logix query services exist")
    if finance_inquiry.get("source_policy", {}).get("allow_model_only_answer"):
        failures.append("GAR source policy allowed model-only answers")
    if finance_inquiry.get("source_policy", {}).get("allow_mutating_actions"):
        failures.append("GAR source policy allowed mutating actions")

    setup_readiness = build_gar_answer_readiness(
        "Show the platform setup readiness and enabled modules for this organisation",
        role_context="super_admin",
    )
    if setup_readiness.get("domain") != "platform_setup":
        failures.append("Platform setup question did not classify as platform_setup")
    if not setup_readiness.get("answer_ready"):
        failures.append("Platform setup readiness was not marked answer-ready for Super Admin")

    contractor_setup_inquiry = build_gar_inquiry_response(
        "Show organisation connections and enabled modules",
        role_context="contractor",
        execute_source_query=True,
    )
    if contractor_setup_inquiry.get("response_status") != "permission_blocked":
        failures.append("Contractor setup inquiry was not permission blocked")

    notification_references = _notification_source_references([
        {
            "source_reference": {
                "model": "WorkOrder",
                "record_id": 42,
                "label": "Work Order #42",
                "module_key": "works",
                "module_label": "Works Logix",
                "source_field": "work_order_id",
                "url": "/super-admin/work-orders#work-order-42",
            }
        }
    ])
    if not any(
        reference.get("model") == "WorkOrder" and reference.get("record_id") == 42
        for reference in notification_references
    ):
        failures.append("GAR notification source adapter did not expose the source record reference")
    if not all(isinstance(reference.get("fields"), list) and reference.get("fields") for reference in notification_references):
        failures.append("GAR notification source adapter returned source references without fields")

    def _check_failure_envelope(label: str, result: dict, expected_context_type: str) -> None:
        nonlocal failure_envelopes_checked
        failure_envelopes_checked += 1
        if result.get("context_type") != expected_context_type:
            failures.append(f"{label} failure envelope returned the wrong context type")
        if result.get("query_ready") is not False:
            failures.append(f"{label} failure envelope did not return query_ready=False")
        if not isinstance(result.get("source_references"), list):
            failures.append(f"{label} failure envelope is missing source_references list")
        if not result.get("error"):
            failures.append(f"{label} failure envelope is missing an error code")

    def _check_ready_envelope(label: str, result: dict, expected_context_type: str) -> None:
        nonlocal ready_envelopes_checked, source_references_checked
        if result.get("query_ready") is not True:
            return
        ready_envelopes_checked += 1
        if result.get("context_type") != expected_context_type:
            failures.append(f"{label} ready envelope returned the wrong context type")
        if not result.get("safe_summary"):
            failures.append(f"{label} ready envelope is missing safe_summary")
        source_references = result.get("source_references")
        if not isinstance(source_references, list) or not source_references:
            failures.append(f"{label} ready envelope is missing source references")
            return
        for index, reference in enumerate(source_references, start=1):
            source_references_checked += 1
            if not isinstance(reference, dict):
                failures.append(f"{label} source reference #{index} is not an object")
                continue
            if not reference.get("model"):
                failures.append(f"{label} source reference #{index} is missing model")
            if "record_id" not in reference:
                failures.append(f"{label} source reference #{index} is missing record_id")
            if not isinstance(reference.get("fields"), list) or not reference.get("fields"):
                failures.append(f"{label} source reference #{index} is missing fields list")

    _check_failure_envelope(
        "Team",
        build_team_source_query(company_id=None, role_context="super_admin"),
        "gar_team_source_query",
    )
    _check_failure_envelope(
        "Platform setup",
        build_platform_setup_source_query(company_id=None, role_context="super_admin"),
        "gar_platform_setup_source_query",
    )
    _check_failure_envelope(
        "Governance",
        build_governance_source_query(company_id=None, role_context="super_admin"),
        "gar_governance_source_query",
    )
    _check_failure_envelope(
        "Document",
        build_document_source_query(company_id=None, role_context="super_admin"),
        "gar_document_source_query",
    )
    _check_failure_envelope(
        "Notification",
        build_notification_source_query(user_id=None, role_context="super_admin"),
        "gar_notification_source_query",
    )
    _check_failure_envelope(
        "Contract",
        build_contract_source_query(company_id=None, role_context="super_admin"),
        "gar_contract_source_query",
    )
    _check_failure_envelope(
        "Client/unit",
        build_client_unit_source_query(company_id=None, role_context="super_admin"),
        "gar_client_unit_source_query",
    )
    _check_failure_envelope(
        "Works",
        build_works_source_query(company_id=None, role_context="super_admin"),
        "gar_works_source_query",
    )
    _check_failure_envelope(
        "Contractor works",
        build_contractor_works_source_query(user_id=None, role_context="contractor"),
        "gar_contractor_works_source_query",
    )
    _check_failure_envelope(
        "Member works",
        build_member_works_source_query(user_id=None, role_context="member"),
        "gar_member_works_source_query",
    )

    app = create_app()
    with app.app_context():
        company = Company.query.order_by(Company.id.asc()).first()
        user = User.query.filter(User.company_id.isnot(None)).order_by(User.id.asc()).first()
        client = Client.query.order_by(Client.id.asc()).first()
        contractor_user = User.query.filter(User.contractor_id.isnot(None)).order_by(User.id.asc()).first()
        member = Member.query.filter(Member.user_id.isnot(None)).order_by(Member.id.asc()).first()

        company_id = company.id if company else (user.company_id if user else None)
        if company_id:
            platform_setup_result = build_platform_setup_source_query(company_id=company_id, role_context="super_admin")
            _check_ready_envelope(
                "Platform setup",
                platform_setup_result,
                "gar_platform_setup_source_query",
            )
            setup_records = platform_setup_result.get("records") or {}
            setup_actions = setup_records.get("governed_actions") or []
            if not any(action.get("key") == "create_connection_invite" for action in setup_actions):
                failures.append("Platform setup source query did not expose governed setup actions")
            setup_mutation_policy = setup_records.get("mutation_policy") or {}
            if setup_mutation_policy.get("gar_may_execute_actions") is not False:
                failures.append("Platform setup source query allowed GAR to execute setup actions")
            _check_ready_envelope(
                "Team",
                build_team_source_query(company_id=company_id, role_context="super_admin"),
                "gar_team_source_query",
            )
            _check_ready_envelope(
                "Governance",
                build_governance_source_query(company_id=company_id, role_context="super_admin"),
                "gar_governance_source_query",
            )
            _check_ready_envelope(
                "Document",
                build_document_source_query(company_id=company_id, role_context="super_admin"),
                "gar_document_source_query",
            )
            _check_ready_envelope(
                "Contract",
                build_contract_source_query(company_id=company_id, role_context="super_admin"),
                "gar_contract_source_query",
            )
            _check_ready_envelope(
                "Works",
                build_works_source_query(company_id=company_id, role_context="super_admin"),
                "gar_works_source_query",
            )
        if client:
            _check_ready_envelope(
                "Client/unit",
                build_client_unit_source_query(
                    company_id=client.company_id,
                    role_context="super_admin",
                    question=f"Summarise the {client.name} development",
                ),
                "gar_client_unit_source_query",
            )
        if user:
            _check_ready_envelope(
                "Notification",
                build_notification_source_query(user_id=user.id, role_context="super_admin"),
                "gar_notification_source_query",
            )
        if contractor_user:
            _check_ready_envelope(
                "Contractor works",
                build_contractor_works_source_query(user_id=contractor_user.id, role_context="contractor"),
                "gar_contractor_works_source_query",
            )
        if member:
            _check_ready_envelope(
                "Member works",
                build_member_works_source_query(user_id=member.user_id, role_context="member"),
                "gar_member_works_source_query",
            )

    print("GAR source adapter contract check")
    print(f"- Capabilities checked: {len(CAPABILITIES)}")
    print(f"- Declared source adapters checked: {len(SOURCE_ADAPTERS)}")
    print(f"- Role registries checked: {len(ROLE_ALL)}")
    print("- Finance readiness gate checked: yes")
    print(f"- Failure envelopes checked: {failure_envelopes_checked}")
    print(f"- Ready envelopes checked: {ready_envelopes_checked}")
    print(f"- Source references checked: {source_references_checked}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
