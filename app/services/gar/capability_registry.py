"""GAR capability and answer-readiness helpers.

This layer keeps GAR honest: it describes which questions can be answered
from source-backed records today and which areas still need module services.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GarCapability:
    key: str
    name: str
    status: str
    answer_mode: str
    source_backed: bool
    source_records: tuple[str, ...]
    can_answer_examples: tuple[str, ...]
    not_ready_examples: tuple[str, ...] = ()
    limitation: str = ""
    recommended_next_build: str = ""
    role_visibility: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "name": self.name,
            "status": self.status,
            "answer_mode": self.answer_mode,
            "source_backed": self.source_backed,
            "source_records": list(self.source_records),
            "can_answer_examples": list(self.can_answer_examples),
            "not_ready_examples": list(self.not_ready_examples),
            "limitation": self.limitation,
            "recommended_next_build": self.recommended_next_build,
            "role_visibility": list(self.role_visibility),
        }


ROLE_ALL = (
    "super_admin",
    "admin",
    "property_manager",
    "assistant",
    "finance",
    "director",
    "contractor",
    "member",
    "resident",
)


CAPABILITIES: tuple[GarCapability, ...] = (
    GarCapability(
        key="clients_units",
        name="Clients, Developments and Units",
        status="available",
        answer_mode="source_summary",
        source_backed=True,
        source_records=("Client", "Unit", "UnitOwner", "UnitResident", "ClientContract"),
        can_answer_examples=(
            "Summarise the Matthew Lavery development.",
            "Show units, blocks, owner/resident signals and development structure.",
        ),
        limitation="Role permissions still decide whether owner, resident or contract details are visible.",
        role_visibility=ROLE_ALL,
    ),
    GarCapability(
        key="works",
        name="Works Logix and Maintenance Requests",
        status="available",
        answer_mode="source_summary_and_recommendation",
        source_backed=True,
        source_records=(
            "MaintenanceRequest",
            "WorkOrder",
            "WorkOrderLifecycleEvent",
            "WorkOrderCompletion",
            "WorkOrderReopenRequest",
            "ContractorFeedback",
        ),
        can_answer_examples=(
            "What open works are linked to this unit?",
            "Has this issue happened before and what was done last time?",
            "Which contractors have repeated returns or low feedback?",
        ),
        limitation="GAR recommends and summarises only. Works Logix still owns routing, closure and reopening.",
        role_visibility=ROLE_ALL,
    ),
    GarCapability(
        key="notifications",
        name="Notifications and Action Queue",
        status="available",
        answer_mode="source_summary",
        source_backed=True,
        source_records=("Notification",),
        can_answer_examples=(
            "What notifications need my attention?",
            "Show my unread action queue.",
        ),
        limitation="Notification answers are recipient-scoped. GAR should not expose another user's notification queue.",
        role_visibility=ROLE_ALL,
    ),
    GarCapability(
        key="contracts",
        name="Contracts and Renewals",
        status="available_partial",
        answer_mode="source_summary",
        source_backed=True,
        source_records=("ClientContract", "ContractRenewalAlert", "Client"),
        can_answer_examples=(
            "Which contracts are expired?",
            "Which clients have renewal risk in the next 90 days?",
        ),
        limitation="Contract intelligence is available for current PSRA expiry and fee signals; document-level contract clause extraction is not complete yet.",
        recommended_next_build="Add signed contract document extraction and immutable renewal audit links.",
        role_visibility=("super_admin", "admin", "property_manager", "assistant", "finance", "director"),
    ),
    GarCapability(
        key="finance",
        name="Finance Logix",
        status="foundation_present_not_query_ready",
        answer_mode="not_live_until_finance_services_exist",
        source_backed=False,
        source_records=(
            "Budget",
            "BudgetCategory",
            "Debtor",
            "AgedDebtor",
            "Invoice",
            "Payment",
            "LedgerEntry",
            "ServiceCharge",
        ),
        can_answer_examples=(
            "GAR can currently report finance readiness fields on units and developments.",
        ),
        not_ready_examples=(
            "Tell me the debtors in Matthew Lavery.",
            "How much of the budget has been spent?",
            "Which owners are in arrears and by how much?",
        ),
        limitation=(
            "Finance models exist, but GAR should not answer live debtor, arrears, spend-against-budget "
            "or payment questions until Finance Logix has source-backed query services, seeded/validated "
            "ledger records and role-gated finance visibility."
        ),
        recommended_next_build=(
            "Build Finance Logix read services for debtor balances, budgets, spend, invoices and payments, "
            "then expose finance-safe GAR summaries from those services."
        ),
        role_visibility=("super_admin", "admin", "property_manager", "finance", "director", "member"),
    ),
    GarCapability(
        key="documents",
        name="Documents and AI Extraction",
        status="available_partial",
        answer_mode="metadata_source_summary",
        source_backed=True,
        source_records=("Document", "MediaFile", "ExportedFileLog", "ClientComplianceDocument"),
        can_answer_examples=(
            "Which documents are expiring or need review?",
            "Show document metadata and GAR parsing readiness for this development.",
        ),
        not_ready_examples=(
            "Read every lease and summarise all special covenants.",
            "Extract all invoice totals from uploaded PDFs.",
        ),
        limitation="Document metadata is source-backed. Full document extraction, clause interpretation and invoice/PDF parsing are not complete.",
        recommended_next_build="Create document ingestion, classification, extraction, source citation and approval workflows.",
        role_visibility=("super_admin", "admin", "property_manager", "assistant", "finance", "director", "member", "resident"),
    ),
    GarCapability(
        key="team_hr",
        name="Team, Users and HR Logix",
        status="available_partial",
        answer_mode="source_summary",
        source_backed=True,
        source_records=("User", "Role", "Company", "LeaveBalanceLedger"),
        can_answer_examples=(
            "Who is assigned to this client?",
            "Which users are active in the team directory?",
        ),
        not_ready_examples=(
            "Calculate full HR holiday cover impact across all future leave.",
            "Assess staff performance from HR records.",
        ),
        limitation="User/team records are available. HR Logix operational services are still a later module build.",
        recommended_next_build="Build HR Logix leave, rota and cover services linked to Works routing.",
        role_visibility=("super_admin", "admin"),
    ),
    GarCapability(
        key="governance",
        name="Director, Governance and Compliance",
        status="available_partial",
        answer_mode="source_summary",
        source_backed=True,
        source_records=("Client", "ComplianceDocument", "AGMRecord", "CapexRequest"),
        can_answer_examples=(
            "Which developments have compliance or governance attention signals?",
        ),
        limitation="Governance summaries exist where structured records exist; director appointment and board-pack workflows are still incomplete.",
        recommended_next_build="Add director appointment records, board-pack preparation and governance decision logs.",
        role_visibility=("super_admin", "admin", "property_manager", "assistant", "director"),
    ),
)


QUESTION_KEYWORDS = {
    "finance": (
        "arrears",
        "debtor",
        "debtors",
        "owed",
        "budget",
        "spent",
        "invoice",
        "payment",
        "ledger",
        "service charge",
        "balance",
        "financial",
        "cost",
    ),
    "works": (
        "work order",
        "works",
        "maintenance",
        "repair",
        "contractor",
        "contractor quality",
        "contractor performance",
        "quality review",
        "quality signal",
        "quality signals",
        "repeated return",
        "repeated returns",
        "repeat return",
        "repeat returns",
        "returned completion",
        "returned completions",
        "low feedback",
        "poor feedback",
        "bad feedback",
        "reopen",
        "completion",
        "issue",
        "request",
    ),
    "notifications": (
        "notification",
        "notifications",
        "alert",
        "alerts",
        "action queue",
        "unread",
        "needs attention",
        "need my attention",
        "what do i need to do",
        "priority action",
        "priority actions",
    ),
    "contracts": (
        "contract",
        "psra",
        "renewal",
        "expiry",
        "expired",
        "fee increase",
        "out of contract",
    ),
    "clients_units": (
        "client",
        "development",
        "property",
        "unit",
        "owner",
        "resident",
        "tenant",
        "block",
        "core",
    ),
    "documents": (
        "document",
        "documents",
        "file",
        "files",
        "lease",
        "certificate",
        "cert",
        "pdf",
        "report",
        "reports",
        "metadata",
        "extract",
        "read",
    ),
    "team_hr": (
        "staff",
        "team",
        "user",
        "holiday",
        "leave",
        "assistant",
        "property manager",
        "financial controller",
    ),
    "governance": (
        "director",
        "governance",
        "compliance",
        "agm",
        "capex",
        "risk",
    ),
}

DOMAIN_PRIORITY = {
    "finance": 1,
    "notifications": 2,
    "works": 3,
    "contracts": 4,
    "documents": 5,
    "governance": 6,
    "team_hr": 7,
    "clients_units": 8,
}

ROLE_ALIASES = {
    "assigned_assistant": "assistant",
    "assistant_manager_cover": "assistant",
    "assistant_manager": "assistant",
    "master_assistant": "assistant",
    "director_governance": "director",
    "financial_controller": "finance",
    "property_manager": "property_manager",
    "super_admin": "super_admin",
}


def _normalise_role(role_context: str | None) -> str | None:
    if not role_context:
        return None
    role = role_context.strip().lower().replace(" ", "_").replace("-", "_")
    return ROLE_ALIASES.get(role, role)


def _matches_role(capability: GarCapability, role_context: str | None) -> bool:
    role = _normalise_role(role_context)
    if not role:
        return True
    return role in capability.role_visibility


def _capability_by_key(key: str) -> GarCapability | None:
    return next((capability for capability in CAPABILITIES if capability.key == key), None)


def _keyword_matches(text: str, keyword: str) -> bool:
    if " " in keyword:
        return keyword in text
    return bool(re.search(rf"\b{re.escape(keyword)}\b", text))


def classify_gar_question(question: str) -> dict:
    """Classify a user question into likely GAR data domains."""
    text = (question or "").lower()
    matches: list[dict] = []
    for key, keywords in QUESTION_KEYWORDS.items():
        matched_terms = [term for term in keywords if _keyword_matches(text, term)]
        if matched_terms:
            matches.append({
                "domain": key,
                "matched_terms": matched_terms,
                "score": len(matched_terms),
            })

    matches.sort(key=lambda row: (-row["score"], DOMAIN_PRIORITY.get(row["domain"], 99), row["domain"]))
    primary = matches[0]["domain"] if matches else "general"
    return {
        "question": question or "",
        "primary_domain": primary,
        "matches": matches,
    }


def build_gar_capability_registry(role_context: str | None = None) -> dict:
    """Return the role-filtered GAR capability map."""
    visible_capabilities = [
        capability.as_dict()
        for capability in CAPABILITIES
        if _matches_role(capability, role_context)
    ]
    return {
        "context_type": "gar_capability_registry",
        "role_context": _normalise_role(role_context) or "all",
        "principle": "GAR must answer from source-backed records and role-permitted visibility only.",
        "capabilities": visible_capabilities,
        "summary": {
            "available": sum(1 for item in visible_capabilities if item["status"] == "available"),
            "partial": sum(1 for item in visible_capabilities if "partial" in item["status"]),
            "not_query_ready": sum(
                1 for item in visible_capabilities
                if item["status"] in {"foundation_present_not_query_ready", "planned_partial"}
            ),
        },
    }


def build_gar_answer_readiness(question: str, role_context: str | None = None) -> dict:
    """Explain whether GAR can answer a question from current source records."""
    classification = classify_gar_question(question)
    primary_domain = classification["primary_domain"]
    capability = _capability_by_key(primary_domain)

    if capability is None:
        return {
            "context_type": "gar_answer_readiness",
            "question": question or "",
            "classification": classification,
            "role_context": _normalise_role(role_context) or "all",
            "answer_ready": False,
            "answer_mode": "needs_clarification",
            "message": "GAR needs a clearer property-management domain before choosing source records.",
            "source_records": [],
            "recommended_next_build": "Route the question through GAR intent handling once the chat interface is built.",
        }

    role_allowed = _matches_role(capability, role_context)
    answer_ready = role_allowed and capability.source_backed and capability.status in {
        "available",
        "available_partial",
    }
    if not role_allowed:
        message = "GAR recognises the domain, but this role should not receive this data without permission checks."
    elif answer_ready:
        message = f"GAR can answer this from {capability.name} source records, subject to record-level permissions."
    else:
        message = (
            f"GAR recognises this as {capability.name}, but the current build is not safe for live answers yet."
        )

    return {
        "context_type": "gar_answer_readiness",
        "question": question or "",
        "classification": classification,
        "role_context": _normalise_role(role_context) or "all",
        "domain": capability.key,
        "domain_name": capability.name,
        "status": capability.status,
        "answer_ready": answer_ready,
        "role_allowed": role_allowed,
        "answer_mode": capability.answer_mode,
        "source_backed": capability.source_backed,
        "source_records": list(capability.source_records),
        "limitation": capability.limitation,
        "message": message,
        "recommended_next_build": capability.recommended_next_build,
    }


def attach_gar_capability_readiness(
    payload: dict,
    role_context: str | None = None,
    question: str | None = None,
) -> dict:
    """Return a payload with GAR capability metadata attached."""
    enriched = dict(payload or {})
    enriched["capability_registry"] = build_gar_capability_registry(role_context=role_context)
    if question:
        enriched["answer_readiness"] = build_gar_answer_readiness(
            question,
            role_context=role_context,
        )
    return enriched
