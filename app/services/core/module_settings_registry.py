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
        primary_setting_endpoint="finance.settings_connections",
        settings_sections=(
            "Chart of accounts",
            "Service charge setup",
            "Invoice numbering and terms",
            "Payment request intake",
            "Finance connections and accounting adapters",
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

ADMIN_SETTINGS_ROLES = {"Super Admin", "Admin"}
MANAGEMENT_SETTINGS_ROLES = {
    "Super Admin",
    "Admin",
    "Property Manager",
    "Assistant",
    "Financial Controller",
}

MODULE_SETTINGS_VISIBILITY_BY_ROLE: dict[str, set[str] | None] = {
    "Super Admin": None,
    "Admin": None,
    "Property Manager": {
        "core_platform",
        "property_management_logix",
        "works_logix",
        "finance_logix",
        "members_logix",
        "director_logix",
        "gar_ai",
    },
    "Assistant": {
        "core_platform",
        "property_management_logix",
        "works_logix",
        "members_logix",
        "gar_ai",
    },
    "Financial Controller": {
        "core_platform",
        "property_management_logix",
        "works_logix",
        "finance_logix",
        "members_logix",
        "gar_ai",
    },
    "Contractor": {"core_platform", "contractor_logix", "gar_ai"},
    "Director": {"core_platform", "director_logix", "members_logix", "gar_ai"},
    "Member": {"core_platform", "members_logix", "gar_ai"},
    "Resident": {"core_platform", "members_logix", "gar_ai"},
}


def module_settings_role_name(user: Any | None) -> str:
    if user is None:
        return "Anonymous"
    role = getattr(user, "role", None)
    name = getattr(role, "name", None) or getattr(user, "role_name", None) or "Unassigned"
    return str(name).strip() or "Unassigned"


def can_view_module_settings_centre(user: Any | None) -> bool:
    return module_settings_role_name(user) in MANAGEMENT_SETTINGS_ROLES


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


def module_settings_registry_for_role(role_name: str | None) -> tuple[dict[str, Any], ...]:
    normalised_role = (role_name or "Unassigned").strip() or "Unassigned"
    allowed = MODULE_SETTINGS_VISIBILITY_BY_ROLE.get(normalised_role, {"core_platform"})
    registry = module_settings_registry()
    if allowed is None:
        return registry
    return tuple(item for item in registry if item["key"] in allowed)


def module_settings_registry_for_user(user: Any | None) -> tuple[dict[str, Any], ...]:
    return module_settings_registry_for_role(module_settings_role_name(user))


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
    role_name = module_settings_role_name(user)
    registry = module_settings_registry_for_role(role_name)
    full_registry_count = len(module_settings_registry())
    visible_keys = [item["key"] for item in registry]
    return {
        "context_type": "module_settings_registry",
        "contract_version": "phase3-module-settings-registry-v2",
        "generated_at": datetime.now(UTC).isoformat(),
        "read_only": True,
        "scope": {
            "company_id": getattr(company, "id", None),
            "company_name": getattr(company, "name", None),
            "organisation_uid": getattr(company, "organisation_uid", None),
            "user_id": getattr(user, "id", None),
            "role": role_name,
            "server_side_visibility": True,
        },
        "summary": {
            "module_count": len(registry),
            "full_module_count": full_registry_count,
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
        "visibility_policy": {
            "server_side_filtered": True,
            "role": role_name,
            "visible_module_keys": visible_keys,
            "full_registry_admin_only": True,
            "management_company_users_excluded_from_contractor_logix": (
                role_name in MANAGEMENT_SETTINGS_ROLES
                and role_name not in ADMIN_SETTINGS_ROLES
                and "contractor_logix" not in visible_keys
            ),
            "contractor_users_excluded_from_management_settings": (
                role_name == "Contractor"
                and "property_management_logix" not in visible_keys
                and "finance_logix" not in visible_keys
            ),
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
