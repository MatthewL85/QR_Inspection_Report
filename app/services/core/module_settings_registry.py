from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Iterable

from app.services.core.document_template_service import DOCUMENT_TEMPLATE_OWNERSHIP


@dataclass(frozen=True)
class ModuleSettingsContract:
    key: str
    name: str
    status: str
    owner_scope: str
    standalone_ready: bool
    connected_ready: bool
    primary_setting_endpoint: str | None
    settings_sections: tuple[str, ...]
    document_owner_names: tuple[str, ...]
    shared_foundations: tuple[str, ...]
    notes: str


MODULE_SETTINGS_CONTRACTS: tuple[ModuleSettingsContract, ...] = (
    ModuleSettingsContract(
        key="core_platform",
        name="Core Platform",
        status="active",
        owner_scope="Shared foundation",
        standalone_ready=True,
        connected_ready=True,
        primary_setting_endpoint="settings.profile_index",
        settings_sections=(
            "Organisation identity",
            "Users, roles and permissions",
            "Company profile and branding",
            "Module subscriptions",
            "Organisation connections",
            "Notifications and audit logs",
            "Shared document template engine",
        ),
        document_owner_names=(),
        shared_foundations=(
            "company_id",
            "user_id",
            "role_id",
            "organisation_uid",
            "organisation_connection_id",
            "audit_log_id",
        ),
        notes="Provides shared identity and setup services. It should not own operational business rules.",
    ),
    ModuleSettingsContract(
        key="property_management_logix",
        name="Property Management Logix",
        status="active",
        owner_scope="Management company",
        standalone_ready=True,
        connected_ready=True,
        primary_setting_endpoint="settings.profile_index",
        settings_sections=(
            "Client and development setup",
            "Unit generation rules",
            "Client team assignment",
            "Key site information",
            "Management-side work order settings",
            "Contract and renewal controls",
        ),
        document_owner_names=("Property Management Logix", "Contracts Logix"),
        shared_foundations=("client_id", "unit_id", "company_id", "user_id"),
        notes="Owns development setup and management-side records while reading linked Works, Members and Finance summaries.",
    ),
    ModuleSettingsContract(
        key="works_logix",
        name="Works Logix",
        status="partial",
        owner_scope="Management company",
        standalone_ready=False,
        connected_ready=True,
        primary_setting_endpoint=None,
        settings_sections=(
            "Work order lifecycle",
            "Member request triage",
            "Contractor routing rules",
            "Completion review",
            "Reopen request rules",
            "Evidence visibility",
        ),
        document_owner_names=("Property Management Logix",),
        shared_foundations=(
            "work_order_id",
            "member_request_id",
            "contractor_id",
            "organisation_connection_id",
        ),
        notes="Owns the work order lifecycle. Contractor Logix can update assigned jobs but does not own the work order.",
    ),
    ModuleSettingsContract(
        key="contractor_logix",
        name="Contractor Logix",
        status="foundation",
        owner_scope="Contractor company",
        standalone_ready=True,
        connected_ready=True,
        primary_setting_endpoint="contractor.contractor_settings",
        settings_sections=(
            "Contractor profile",
            "Engineers and teams",
            "Job docket numbering",
            "Calendar and scheduling",
            "Private materials and time log",
            "Payment request terms",
            "Quotation response setup",
        ),
        document_owner_names=("Contractor Logix",),
        shared_foundations=("contractor_id", "company_id", "work_order_id", "organisation_connection_id"),
        notes="Can run independently with manual job dockets, or connect to Works Logix through organisation connections.",
    ),
    ModuleSettingsContract(
        key="finance_logix",
        name="Finance Logix",
        status="shell",
        owner_scope="Finance company or management company",
        standalone_ready=True,
        connected_ready=True,
        primary_setting_endpoint="finance.dashboard",
        settings_sections=(
            "Chart of accounts",
            "Service charge setup",
            "Invoice numbering and terms",
            "Payment request intake",
            "Debtors and creditors",
            "Financial reporting",
        ),
        document_owner_names=("Finance Logix",),
        shared_foundations=("client_id", "unit_id", "member_id", "work_order_id", "payment_request_id"),
        notes="Owns ledgers and invoices. It may read Works payment requests without taking over Works lifecycle control.",
    ),
    ModuleSettingsContract(
        key="hr_logix",
        name="HR Logix",
        status="planned",
        owner_scope="Employer organisation",
        standalone_ready=True,
        connected_ready=True,
        primary_setting_endpoint=None,
        settings_sections=(
            "Employee profile fields",
            "Leave rules",
            "Policy documents",
            "Employment templates",
            "Staff notifications",
            "Manager approvals",
        ),
        document_owner_names=(),
        shared_foundations=("user_id", "company_id", "employee_profile_id"),
        notes="Should link to Core users for login and roles, but own staff records, HR documents and employee workflows.",
    ),
    ModuleSettingsContract(
        key="members_logix",
        name="Members Logix",
        status="foundation",
        owner_scope="Owner, resident and member portal",
        standalone_ready=True,
        connected_ready=True,
        primary_setting_endpoint="members.dashboard",
        settings_sections=(
            "Portal access codes",
            "Unit membership verification",
            "Owner and resident visibility",
            "Maintenance request settings",
            "Member notifications",
            "Mobile/PWA readiness",
        ),
        document_owner_names=(),
        shared_foundations=("unit_uid", "unit_membership_id", "client_id", "unit_id", "member_id", "resident_id"),
        notes="Owns member and resident access. It reads permitted unit, Works and Finance data without duplicating source records.",
    ),
    ModuleSettingsContract(
        key="director_logix",
        name="Director Logix",
        status="shell",
        owner_scope="OMC/director governance",
        standalone_ready=True,
        connected_ready=True,
        primary_setting_endpoint="director.dashboard",
        settings_sections=(
            "Director access rules",
            "Governance visibility",
            "Quotation approval settings",
            "CAPEX voting",
            "Board packs and reporting",
        ),
        document_owner_names=(),
        shared_foundations=("client_id", "unit_id", "member_id", "director_assignment_id"),
        notes="Owns director-facing governance workflows and should only show records the director is allowed to review.",
    ),
    ModuleSettingsContract(
        key="gar_ai",
        name="GAR AI",
        status="foundation",
        owner_scope="Role-aware intelligence layer",
        standalone_ready=False,
        connected_ready=True,
        primary_setting_endpoint="super_admin.gar_insights",
        settings_sections=(
            "Role visibility rules",
            "Source adapter registry",
            "Digest settings",
            "GAR report templates",
            "Explainability and audit",
        ),
        document_owner_names=("GAR AI",),
        shared_foundations=("source_reference_id", "visibility_rule_id", "audit_log_id", "organisation_connection_id"),
        notes="GAR reads governed source records. It should recommend and summarise, not become the source of truth.",
    ),
)


def _template_types_for_owner(owner_names: Iterable[str]) -> tuple[dict[str, Any], ...]:
    wanted = set(owner_names)
    entries: list[dict[str, Any]] = []
    for (module_key, document_type), ownership in sorted(DOCUMENT_TEMPLATE_OWNERSHIP.items()):
        owner = ownership.get("owner_module")
        if owner not in wanted:
            continue
        entries.append(
            {
                "module_key": module_key,
                "document_type": document_type,
                "owner_module": owner,
                "created_by": ownership.get("created_by", "-"),
                "reviewed_by": ownership.get("reviewed_by", "-"),
                "handoff": bool(ownership.get("handoff")),
            }
        )
    return tuple(entries)


def module_settings_registry() -> tuple[dict[str, Any], ...]:
    payload: list[dict[str, Any]] = []
    for contract in MODULE_SETTINGS_CONTRACTS:
        payload.append(
            {
                "key": contract.key,
                "name": contract.name,
                "status": contract.status,
                "owner_scope": contract.owner_scope,
                "standalone_ready": contract.standalone_ready,
                "connected_ready": contract.connected_ready,
                "primary_setting_endpoint": contract.primary_setting_endpoint,
                "settings_sections": contract.settings_sections,
                "document_template_types": _template_types_for_owner(contract.document_owner_names),
                "shared_foundations": contract.shared_foundations,
                "notes": contract.notes,
            }
        )
    return tuple(payload)


def module_settings_by_key(key: str) -> dict[str, Any] | None:
    normalised = (key or "").strip().lower()
    return next((item for item in module_settings_registry() if item["key"] == normalised), None)


def combined_settings_sections(enabled_module_keys: Iterable[str] | None = None) -> tuple[dict[str, Any], ...]:
    enabled = {item.strip().lower() for item in enabled_module_keys or [] if item}
    registry = module_settings_registry()
    if not enabled:
        return registry
    return tuple(item for item in registry if item["key"] == "core_platform" or item["key"] in enabled)


def module_settings_feed_payload(company: Any | None = None, user: Any | None = None) -> dict[str, Any]:
    registry = module_settings_registry()
    return {
        "context_type": "module_settings_registry",
        "contract_version": "phase3-module-settings-registry-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "read_only": True,
        "scope": {
            "company_id": getattr(company, "id", None),
            "company_name": getattr(company, "name", None),
            "organisation_uid": getattr(company, "organisation_uid", None),
            "user_id": getattr(user, "id", None),
            "role": getattr(getattr(user, "role", None), "name", None),
            "server_side_visibility": True,
        },
        "summary": {
            "module_count": len(registry),
            "standalone_ready_count": sum(1 for item in registry if item["standalone_ready"]),
            "connected_ready_count": sum(1 for item in registry if item["connected_ready"]),
            "document_template_type_count": sum(len(item["document_template_types"]) for item in registry),
        },
        "settings_policy": {
            "core_owns_shared_foundations": True,
            "modules_own_operational_settings": True,
            "standalone_modules_expose_own_settings_only": True,
            "connected_modules_group_in_one_settings_centre": True,
            "shared_engine_does_not_transfer_document_ownership": True,
        },
        "registry": list(registry),
        "mutation_policy": {
            "feed_allows_mutation": False,
            "settings_changes_require_module_owner_route": True,
            "requires_authenticated_session": True,
            "requires_csrf": True,
            "gar_may_execute_actions": False,
        },
        "source_references": [
            {
                "model": "ModuleSettingsContract",
                "record_id": None,
                "label": "Core module settings registry",
                "fields": [
                    "key",
                    "settings_sections",
                    "standalone_ready",
                    "connected_ready",
                    "document_template_types",
                    "shared_foundations",
                ],
            },
            {
                "model": "CoreDocumentTemplate",
                "record_id": None,
                "label": "Document template ownership registry",
                "fields": ["module_key", "document_type", "owner_module", "created_by", "reviewed_by"],
            },
        ],
    }
