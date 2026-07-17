"""GAR AI service layer."""

from .capability_registry import (
    attach_gar_capability_readiness,
    build_gar_answer_readiness,
    build_gar_capability_registry,
    classify_gar_question,
)
from .context import (
    build_client_context,
    build_development_health_register,
    build_operational_digest,
    build_portfolio_context,
    build_unit_context,
    build_work_order_context,
    build_work_order_relevant_history,
    build_works_issue_pattern_memory,
    build_works_intelligence_queue,
)
from .inquiry import build_gar_inquiry_response
from .role_digest import build_contractor_role_digest, build_member_role_digest

__all__ = [
    "attach_gar_capability_readiness",
    "build_client_context",
    "build_contractor_role_digest",
    "build_development_health_register",
    "build_gar_answer_readiness",
    "build_gar_capability_registry",
    "build_gar_inquiry_response",
    "build_member_role_digest",
    "build_operational_digest",
    "build_portfolio_context",
    "build_unit_context",
    "build_work_order_context",
    "build_work_order_relevant_history",
    "build_works_issue_pattern_memory",
    "build_works_intelligence_queue",
    "classify_gar_question",
]
