"""GAR inquiry response contract.

This is the boundary future GAR chat/UI surfaces should use before any
generated answer is shown to a user.
"""

from __future__ import annotations

from .capability_registry import build_gar_answer_readiness


SOURCE_ADAPTERS = {
    "clients_units": "gar.client_unit_source_query",
    "works": "gar.works_source_query",
    "notifications": "gar.notification_source_query",
    "contracts": "gar.contract_source_query",
    "platform_setup": "gar.platform_setup_source_query",
    "finance": "finance.gar_finance_query_service",
    "documents": "gar.document_source_query",
    "team_hr": "gar.team_source_query",
    "governance": "gar.governance_source_query",
}


def _status_from_readiness(readiness: dict) -> str:
    if not readiness.get("question"):
        return "needs_question"
    if not readiness.get("role_allowed", True):
        return "permission_blocked"
    if readiness.get("answer_ready"):
        return "ready_for_source_query"
    if readiness.get("source_backed") is False:
        return "not_query_ready"
    return "needs_source_adapter"


def _message_for_status(readiness: dict, status: str) -> str:
    if status == "needs_question":
        return "Ask GAR a question so it can choose the correct source records."
    if status == "permission_blocked":
        return "GAR recognises the question, but this role is not permitted to access that information."
    if status == "ready_for_source_query":
        return (
            "GAR can answer this after routing to the owning source service and returning source references."
        )
    if status == "not_query_ready":
        return readiness.get("message") or "GAR recognises the question, but this module is not query-ready yet."
    return "GAR recognises the question, but a source query adapter is still required before answer generation."


def _execute_source_query(
    *,
    domain: str | None,
    company_id: int | None,
    user_id: int | None,
    role_context: str,
    allowed_client_ids: tuple[int, ...] | None,
    question: str,
) -> dict | None:
    if domain == "works":
        role_key = (role_context or "").strip().lower().replace(" ", "_").replace("-", "_")
        if role_key == "contractor":
            from .source_queries import build_contractor_works_source_query

            return build_contractor_works_source_query(
                user_id=user_id,
                role_context=role_context,
                question=question,
            )
        if role_key in {"member", "resident"}:
            from .source_queries import build_member_works_source_query

            return build_member_works_source_query(
                user_id=user_id,
                role_context=role_context,
                question=question,
            )

        from .source_queries import build_works_source_query

        return build_works_source_query(
            company_id=company_id,
            role_context=role_context,
            allowed_client_ids=allowed_client_ids,
            question=question,
        )
    if domain == "notifications":
        from .source_queries import build_notification_source_query

        return build_notification_source_query(
            user_id=user_id,
            role_context=role_context,
            question=question,
        )
    if domain == "clients_units":
        from .source_queries import build_client_unit_source_query

        return build_client_unit_source_query(
            company_id=company_id,
            role_context=role_context,
            allowed_client_ids=allowed_client_ids,
            question=question,
        )
    if domain == "contracts":
        from .source_queries import build_contract_source_query

        return build_contract_source_query(
            company_id=company_id,
            role_context=role_context,
            allowed_client_ids=allowed_client_ids,
            question=question,
        )
    if domain == "platform_setup":
        from .source_queries import build_platform_setup_source_query

        return build_platform_setup_source_query(
            company_id=company_id,
            role_context=role_context,
            allowed_client_ids=allowed_client_ids,
            question=question,
        )
    if domain == "documents":
        from .source_queries import build_document_source_query

        return build_document_source_query(
            company_id=company_id,
            role_context=role_context,
            allowed_client_ids=allowed_client_ids,
            question=question,
        )
    if domain == "team_hr":
        from .source_queries import build_team_source_query

        return build_team_source_query(
            company_id=company_id,
            role_context=role_context,
            allowed_client_ids=allowed_client_ids,
            question=question,
        )
    if domain == "governance":
        from .source_queries import build_governance_source_query

        return build_governance_source_query(
            company_id=company_id,
            role_context=role_context,
            allowed_client_ids=allowed_client_ids,
            question=question,
        )
    return None


def build_gar_inquiry_response(
    question: str,
    role_context: str | None = None,
    *,
    company_id: int | None = None,
    user_id: int | None = None,
    allowed_client_ids: tuple[int, ...] | None = None,
    execute_source_query: bool = False,
) -> dict:
    """Build the standard GAR inquiry envelope for future chat/app surfaces."""
    readiness = build_gar_answer_readiness(question, role_context=role_context)
    status = _status_from_readiness(readiness)
    domain = readiness.get("domain")
    normalised_role = readiness.get("role_context") or "all"
    source_result = None
    if execute_source_query and status == "ready_for_source_query":
        source_result = _execute_source_query(
            domain=domain,
            company_id=company_id,
            user_id=user_id,
            role_context=normalised_role,
            allowed_client_ids=allowed_client_ids,
            question=question,
        )
        if source_result is None:
            status = "needs_source_adapter"

    response = {
        "context_type": "gar_inquiry_response",
        "question": question or "",
        "role_context": normalised_role,
        "response_status": status,
        "answer_ready": status == "ready_for_source_query" and (
            not execute_source_query or bool(source_result and source_result.get("query_ready"))
        ),
        "answer": None,
        "safe_message": _message_for_status(readiness, status),
        "readiness": readiness,
        "source_policy": {
            "must_use_source_records": True,
            "must_return_source_references": True,
            "respect_role_visibility": True,
            "allow_model_only_answer": False,
            "allow_mutating_actions": False,
        },
        "source_query": {
            "domain": domain,
            "adapter": SOURCE_ADAPTERS.get(domain),
            "required_before_final_answer": status == "ready_for_source_query",
        },
        "source_references": [],
        "recommended_next_build": readiness.get("recommended_next_build") or "",
    }
    if source_result:
        response["source_query_result"] = source_result
        response["source_references"] = source_result.get("source_references", [])
        if source_result.get("query_ready"):
            response["answer"] = source_result.get("safe_summary")
            response["safe_message"] = (
                "GAR returned a source-backed summary from permitted records."
            )
    return response
