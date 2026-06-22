"""Smoke check the GAR context service against the active database."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    from app import create_app
    from app.models.client.client import Client
    from app.models.core.user import User
    from app.models.members.unit import Unit
    from app.models.works.work_order import WorkOrder
    from app.services.gar import (
        attach_gar_capability_readiness,
        build_client_context,
        build_contractor_role_digest,
        build_development_health_register,
        build_gar_answer_readiness,
        build_gar_capability_registry,
        build_gar_inquiry_response,
        build_member_role_digest,
        build_operational_digest,
        build_portfolio_context,
        build_unit_context,
        build_work_order_context,
        build_works_intelligence_queue,
    )

    app = create_app()
    failures: list[str] = []

    with app.app_context():
        portfolio_context = build_portfolio_context()
        if portfolio_context.get("context_type") != "portfolio":
            failures.append("Portfolio context did not return context_type=portfolio")
        if "source_references" not in portfolio_context:
            failures.append("Portfolio context is missing source_references")

        development_register = build_development_health_register()
        if development_register.get("context_type") != "development_health_register":
            failures.append("Development health register returned the wrong context type")
        if "rows" not in development_register:
            failures.append("Development health register is missing rows")

        works_intelligence = build_works_intelligence_queue()
        if works_intelligence.get("context_type") != "works_intelligence":
            failures.append("Works intelligence did not return context_type=works_intelligence")
        if "signals" not in works_intelligence:
            failures.append("Works intelligence is missing signals")
        pattern_memory = works_intelligence.get("pattern_memory", {})
        if "patterns" not in pattern_memory:
            failures.append("Works intelligence is missing GAR pattern memory")

        operational_digest = build_operational_digest(role_context="super_admin")
        if operational_digest.get("context_type") != "gar_operational_digest":
            failures.append("GAR operational digest returned the wrong context type")
        for key in ("summary", "priority_actions", "development_attention", "works_attention", "quality_signals", "source_references"):
            if key not in operational_digest:
                failures.append(f"GAR operational digest is missing {key}")
        if operational_digest.get("role_context") != "super_admin":
            failures.append("GAR operational digest did not preserve role context")
        quality_signals = operational_digest.get("quality_signals", {})
        if not quality_signals.get("contractor_quality_visible"):
            failures.append("GAR super-admin digest did not expose contractor quality visibility")
        contractor_digest = build_operational_digest(role_context="contractor")
        if contractor_digest.get("quality_signals", {}).get("contractor_quality_visible"):
            failures.append("GAR contractor digest exposed management quality signals")
        scoped_digest = build_operational_digest(
            role_context="property_manager",
            allowed_client_ids=tuple(),
        )
        if scoped_digest.get("visibility_scope", {}).get("allowed_client_count") != 0:
            failures.append("GAR scoped digest did not preserve empty client scope")
        if scoped_digest.get("summary", {}).get("portfolio", {}).get("clients") != 0:
            failures.append("GAR scoped digest leaked portfolio clients for empty scope")

        member_role_digest = build_member_role_digest(
            SimpleNamespace(id=1, user_id=2),
            [
                SimpleNamespace(
                    id=10,
                    unit_id=20,
                    role="resident",
                    is_primary=True,
                    unit=SimpleNamespace(id=20, unit_number="A-001", unit_label="A-001", block_name="Block A"),
                )
            ],
            {
                "member_requests": [],
                "open_work_orders": [],
                "closed_work_orders": [],
                "reopen_requests": [],
                "feedback_needed_work_orders": [],
                "member_attention_queues": [],
                "member_next_actions": [],
            },
        )
        if member_role_digest.get("context_type") != "gar_role_digest":
            failures.append("GAR member role digest returned the wrong context type")
        if member_role_digest.get("role_context") != "resident":
            failures.append("GAR member role digest did not infer resident-only scope")

        contractor_role_digest = build_contractor_role_digest(
            SimpleNamespace(id=3, contractor_id=4),
            {
                "assigned_work_orders": [],
                "active_work_orders": [],
                "submitted_work_orders": [],
                "returned_work_orders": [],
                "next_actions": [],
                "stats": {"total": 0, "attention_total": 0},
            },
        )
        if contractor_role_digest.get("context_type") != "gar_role_digest":
            failures.append("GAR contractor role digest returned the wrong context type")
        if contractor_role_digest.get("role_context") != "contractor":
            failures.append("GAR contractor role digest did not preserve contractor role")

        capability_registry = build_gar_capability_registry(role_context="super_admin")
        if capability_registry.get("context_type") != "gar_capability_registry":
            failures.append("GAR capability registry returned the wrong context type")
        capability_keys = {
            item.get("key")
            for item in capability_registry.get("capabilities", [])
        }
        for key in ("clients_units", "works", "contracts", "finance"):
            if key not in capability_keys:
                failures.append(f"GAR capability registry is missing {key}")

        finance_readiness = build_gar_answer_readiness(
            "Tell me the debtors in Matthew Lavery",
            role_context="super_admin",
        )
        if finance_readiness.get("domain") != "finance":
            failures.append("GAR answer readiness did not classify debtor question as finance")
        if finance_readiness.get("answer_ready"):
            failures.append("GAR answer readiness incorrectly marked finance debtor answers as ready")
        if "Finance Logix" not in finance_readiness.get("domain_name", ""):
            failures.append("GAR finance readiness did not identify Finance Logix")

        assistant_registry = build_gar_capability_registry(role_context="assigned_assistant")
        if assistant_registry.get("role_context") != "assistant":
            failures.append("GAR capability registry did not normalise assigned assistant role")
        if not assistant_registry.get("capabilities"):
            failures.append("GAR capability registry returned no capabilities for assigned assistant")

        finance_controller_readiness = build_gar_answer_readiness(
            "How much of the budget has been spent?",
            role_context="financial controller",
        )
        if finance_controller_readiness.get("role_context") != "finance":
            failures.append("GAR answer readiness did not normalise Financial Controller role")
        if finance_controller_readiness.get("answer_ready"):
            failures.append("GAR answer readiness incorrectly marked finance budget answers as ready")

        works_readiness = build_gar_answer_readiness(
            "What open work orders are linked to this unit?",
            role_context="property_manager",
        )
        if works_readiness.get("domain") != "works":
            failures.append("GAR answer readiness did not classify work-order question as works")
        if not works_readiness.get("answer_ready"):
            failures.append("GAR answer readiness did not mark Works questions as source-backed")

        contractor_quality_readiness = build_gar_answer_readiness(
            "Which contractors have repeated returns or low feedback?",
            role_context="property_manager",
        )
        if contractor_quality_readiness.get("domain") != "works":
            failures.append("GAR answer readiness did not classify contractor quality question as works")
        if not contractor_quality_readiness.get("answer_ready"):
            failures.append("GAR answer readiness did not mark contractor quality questions as source-backed")

        enriched_payload = attach_gar_capability_readiness(
            {"context_type": "test_payload"},
            role_context="director_governance",
            question="Which contracts are expired?",
        )
        if "capability_registry" not in enriched_payload:
            failures.append("GAR capability attachment did not add registry")
        if enriched_payload.get("answer_readiness", {}).get("domain") != "contracts":
            failures.append("GAR capability attachment did not classify contract question")

        finance_inquiry = build_gar_inquiry_response(
            "Tell me the debtors in Matthew Lavery",
            role_context="super_admin",
        )
        if finance_inquiry.get("context_type") != "gar_inquiry_response":
            failures.append("GAR inquiry response returned the wrong context type")
        if finance_inquiry.get("response_status") != "not_query_ready":
            failures.append("GAR inquiry did not keep finance debtor question behind query readiness")
        if finance_inquiry.get("answer") is not None:
            failures.append("GAR inquiry generated an answer for a finance-not-ready question")
        if finance_inquiry.get("source_policy", {}).get("allow_model_only_answer"):
            failures.append("GAR inquiry allowed model-only answers")

        works_inquiry = build_gar_inquiry_response(
            "What open work orders are linked to this unit?",
            role_context="property_manager",
        )
        if works_inquiry.get("response_status") != "ready_for_source_query":
            failures.append("GAR inquiry did not route Works question to source-query readiness")
        if not works_inquiry.get("source_query", {}).get("adapter"):
            failures.append("GAR inquiry did not identify a Works source adapter")

        contractor_finance_inquiry = build_gar_inquiry_response(
            "Show the service charge balance for this owner",
            role_context="contractor",
        )
        if contractor_finance_inquiry.get("response_status") != "permission_blocked":
            failures.append("GAR inquiry did not block contractor finance visibility")

        client = Client.query.order_by(Client.id.asc()).first()
        first_user = User.query.filter(User.company_id.isnot(None)).order_by(User.id.asc()).first()
        company_id = client.company_id if client else (first_user.company_id if first_user else None)
        team_checked = False
        governance_checked = False
        documents_checked = False
        notifications_checked = False
        if company_id:
            if first_user:
                notification_inquiry = build_gar_inquiry_response(
                    "What notifications need my attention?",
                    role_context="super_admin",
                    company_id=company_id,
                    user_id=first_user.id,
                    execute_source_query=True,
                )
                notifications_checked = True
                if notification_inquiry.get("response_status") != "ready_for_source_query":
                    failures.append("GAR notification inquiry was not ready for source query")
                notification_result = notification_inquiry.get("source_query_result", {})
                if notification_result.get("context_type") != "gar_notification_source_query":
                    failures.append("GAR notification inquiry returned the wrong source query type")
                if not notification_result.get("query_ready"):
                    failures.append("GAR notification inquiry did not return a query-ready result")
                notification_visibility = notification_result.get("visibility", {})
                if not notification_visibility.get("recipient_scoped"):
                    failures.append("GAR notification inquiry did not preserve recipient scope")
                if notification_visibility.get("other_users_included"):
                    failures.append("GAR notification inquiry leaked other users")
                if notification_visibility.get("mutating_actions_included"):
                    failures.append("GAR notification inquiry included mutating actions")
                if not notification_inquiry.get("source_references"):
                    failures.append("GAR notification inquiry did not return source references")
                notification_stats = notification_result.get("stats", {})
                if "acknowledged_count" not in notification_stats:
                    failures.append("GAR notification inquiry did not expose acknowledged_count")
                if "last_acknowledged_at" not in notification_stats:
                    failures.append("GAR notification inquiry did not expose last_acknowledged_at")

            team_inquiry = build_gar_inquiry_response(
                "Who is active in the team directory?",
                role_context="super_admin",
                company_id=company_id,
                execute_source_query=True,
            )
            team_checked = True
            if team_inquiry.get("response_status") != "ready_for_source_query":
                failures.append("GAR team inquiry was not ready for source query")
            team_result = team_inquiry.get("source_query_result", {})
            if team_result.get("context_type") != "gar_team_source_query":
                failures.append("GAR team inquiry returned the wrong source query type")
            if not team_result.get("query_ready"):
                failures.append("GAR team inquiry did not return a query-ready result")
            if team_result.get("visibility", {}).get("hr_leave_records_included"):
                failures.append("GAR team inquiry incorrectly included HR leave records")
            if team_result.get("visibility", {}).get("performance_records_included"):
                failures.append("GAR team inquiry incorrectly included HR performance records")
            if not team_inquiry.get("source_references"):
                failures.append("GAR team inquiry did not return source references")

            contractor_team_inquiry = build_gar_inquiry_response(
                "Who is active in the team directory?",
                role_context="contractor",
                company_id=company_id,
                execute_source_query=True,
            )
            if contractor_team_inquiry.get("response_status") != "permission_blocked":
                failures.append("GAR inquiry did not block contractor team-directory visibility")

            governance_inquiry = build_gar_inquiry_response(
                "Which developments have compliance or governance attention signals?",
                role_context="director_governance",
                company_id=company_id,
                execute_source_query=True,
            )
            governance_checked = True
            if governance_inquiry.get("response_status") != "ready_for_source_query":
                failures.append("GAR governance inquiry was not ready for source query")
            governance_result = governance_inquiry.get("source_query_result", {})
            if governance_result.get("context_type") != "gar_governance_source_query":
                failures.append("GAR governance inquiry returned the wrong source query type")
            if not governance_result.get("query_ready"):
                failures.append("GAR governance inquiry did not return a query-ready result")
            if governance_result.get("visibility", {}).get("document_text_extraction_included"):
                failures.append("GAR governance inquiry incorrectly included document extraction")
            if governance_result.get("visibility", {}).get("director_appointment_scope_included"):
                failures.append("GAR governance inquiry incorrectly claimed director appointment scope")
            if not governance_inquiry.get("source_references"):
                failures.append("GAR governance inquiry did not return source references")

            contractor_governance_inquiry = build_gar_inquiry_response(
                "Which developments have compliance or governance attention signals?",
                role_context="contractor",
                company_id=company_id,
                execute_source_query=True,
            )
            if contractor_governance_inquiry.get("response_status") != "permission_blocked":
                failures.append("GAR inquiry did not block contractor governance visibility")

            document_inquiry = build_gar_inquiry_response(
                "Which documents are expiring or need review?",
                role_context="super_admin",
                company_id=company_id,
                execute_source_query=True,
            )
            documents_checked = True
            if document_inquiry.get("response_status") != "ready_for_source_query":
                failures.append("GAR document inquiry was not ready for source query")
            document_result = document_inquiry.get("source_query_result", {})
            if document_result.get("context_type") != "gar_document_source_query":
                failures.append("GAR document inquiry returned the wrong source query type")
            if not document_result.get("query_ready"):
                failures.append("GAR document inquiry did not return a query-ready result")
            visibility = document_result.get("visibility", {})
            if not visibility.get("metadata_only"):
                failures.append("GAR document inquiry did not declare metadata-only visibility")
            if visibility.get("file_paths_included"):
                failures.append("GAR document inquiry exposed file paths")
            if visibility.get("document_text_extraction_included"):
                failures.append("GAR document inquiry incorrectly included document text extraction")
            if visibility.get("extracted_payloads_included"):
                failures.append("GAR document inquiry incorrectly included extracted payloads")
            if not document_inquiry.get("source_references"):
                failures.append("GAR document inquiry did not return source references")

            contractor_document_inquiry = build_gar_inquiry_response(
                "Which documents are expiring or need review?",
                role_context="contractor",
                company_id=company_id,
                execute_source_query=True,
            )
            if contractor_document_inquiry.get("response_status") != "permission_blocked":
                failures.append("GAR inquiry did not block contractor document visibility")

        client_checked = False
        if client:
            works_source_inquiry = build_gar_inquiry_response(
                "What open work orders are linked to this unit?",
                role_context="super_admin",
                company_id=client.company_id,
                execute_source_query=True,
            )
            if works_source_inquiry.get("response_status") != "ready_for_source_query":
                failures.append("GAR source inquiry did not keep Works question ready for source query")
            if not works_source_inquiry.get("source_query_result", {}).get("query_ready"):
                failures.append("GAR source inquiry did not return a query-ready Works source result")
            if not works_source_inquiry.get("source_references"):
                failures.append("GAR source inquiry did not return source references")
            if not works_source_inquiry.get("answer"):
                failures.append("GAR source inquiry did not return a source-backed safe summary")

            client_unit_inquiry = build_gar_inquiry_response(
                f"Summarise the {client.name} development and units",
                role_context="super_admin",
                company_id=client.company_id,
                execute_source_query=True,
            )
            if client_unit_inquiry.get("response_status") != "ready_for_source_query":
                failures.append("GAR client/unit inquiry was not ready for source query")
            client_unit_result = client_unit_inquiry.get("source_query_result", {})
            if client_unit_result.get("context_type") != "gar_client_unit_source_query":
                failures.append("GAR client/unit inquiry returned the wrong source query type")
            if not client_unit_result.get("query_ready"):
                failures.append("GAR client/unit inquiry did not return a query-ready result")
            if client_unit_result.get("client", {}).get("id") != client.id:
                failures.append("GAR client/unit inquiry did not identify the requested client")
            if not client_unit_inquiry.get("source_references"):
                failures.append("GAR client/unit inquiry did not return source references")

            contractor_client_unit_inquiry = build_gar_inquiry_response(
                f"Summarise the {client.name} development and units",
                role_context="contractor",
                company_id=client.company_id,
                execute_source_query=True,
            )
            if contractor_client_unit_inquiry.get("source_query_result", {}).get("visibility", {}).get("owner_resident_names_included"):
                failures.append("GAR client/unit inquiry leaked owner/resident names to contractor role")

            contract_inquiry = build_gar_inquiry_response(
                "Which contracts are expired?",
                role_context="super_admin",
                company_id=client.company_id,
                execute_source_query=True,
            )
            if contract_inquiry.get("response_status") != "ready_for_source_query":
                failures.append("GAR contract inquiry was not ready for source query")
            contract_result = contract_inquiry.get("source_query_result", {})
            if contract_result.get("context_type") != "gar_contract_source_query":
                failures.append("GAR contract inquiry returned the wrong source query type")
            if not contract_result.get("query_ready"):
                failures.append("GAR contract inquiry did not return a query-ready result")
            if contract_result.get("visibility", {}).get("archived_in_operational_counts"):
                failures.append("GAR contract inquiry included archived contracts in operational counts")
            if not contract_inquiry.get("source_references"):
                failures.append("GAR contract inquiry did not return source references")

            client_context = build_client_context(client.id)
            client_checked = True
            if client_context.get("client_context", {}).get("id") != client.id:
                failures.append("Client context returned the wrong client id")
            if "recommended_actions" not in client_context:
                failures.append("Client context is missing recommended_actions")
            if "development_health" not in client_context:
                failures.append("Client context is missing development_health")
            elif "signals" not in client_context["development_health"]:
                failures.append("Development health is missing signal definitions")

        unit = Unit.query.order_by(Unit.id.asc()).first()
        unit_checked = False
        if unit:
            unit_context = build_unit_context(unit.id)
            unit_checked = True
            if unit_context.get("unit_context", {}).get("id") != unit.id:
                failures.append("Unit context returned the wrong unit id")
            if "visibility_rules" not in unit_context:
                failures.append("Unit context is missing visibility_rules")

        work_order = WorkOrder.query.order_by(WorkOrder.id.asc()).first()
        work_order_checked = False
        if work_order:
            work_order_context = build_work_order_context(work_order.id)
            work_order_checked = True
            if work_order_context.get("work_order_context", {}).get("id") != work_order.id:
                failures.append("Work order context returned the wrong work order id")
            if "lifecycle_context" not in work_order_context:
                failures.append("Work order context is missing lifecycle_context")

    print("GAR context check")
    print("- Portfolio context checked: yes")
    print("- Development health register checked: yes")
    print("- Works intelligence checked: yes")
    print("- Operational digest checked: yes")
    print("- Role-aware member/contractor digests checked: yes")
    print("- Capability registry checked: yes")
    print("- Answer readiness checked: yes")
    print("- Inquiry contract checked: yes")
    print(f"- Team source inquiry checked: {'yes' if team_checked else 'skipped, no company-scoped users'}")
    print(f"- Governance source inquiry checked: {'yes' if governance_checked else 'skipped, no company scope'}")
    print(f"- Document source inquiry checked: {'yes' if documents_checked else 'skipped, no company scope'}")
    print(f"- Notification source inquiry checked: {'yes' if notifications_checked else 'skipped, no company-scoped user'}")
    print(f"- Client context checked: {'yes' if client_checked else 'skipped, no clients'}")
    print(f"- Unit context checked: {'yes' if unit_checked else 'skipped, no units'}")
    print(f"- Work order context checked: {'yes' if work_order_checked else 'skipped, no work orders'}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
