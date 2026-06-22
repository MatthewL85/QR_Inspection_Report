from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleContract:
    key: str
    name: str
    status: str
    dashboard_endpoint: str | None
    owned_data: tuple[str, ...]
    shared_links: tuple[str, ...]


MODULE_CONTRACTS: tuple[ModuleContract, ...] = (
    ModuleContract(
        key="core",
        name="Core Platform",
        status="active",
        dashboard_endpoint=None,
        owned_data=("users", "roles", "companies", "documents", "audit_logs"),
        shared_links=("user_id", "company_id"),
    ),
    ModuleContract(
        key="client_management",
        name="Client / Property Management Logix",
        status="active",
        dashboard_endpoint="super_admin.manage_clients",
        owned_data=("clients", "development_structure", "team_assignments"),
        shared_links=("company_id", "client_id", "unit_id", "user_id"),
    ),
    ModuleContract(
        key="unit_spine",
        name="Unit / Property Asset Spine",
        status="active",
        dashboard_endpoint="unit_bp.list",
        owned_data=("units", "block_core_area", "occupancy_metadata"),
        shared_links=("client_id", "unit_id", "member_id"),
    ),
    ModuleContract(
        key="contract_manager",
        name="Contract Manager",
        status="active",
        dashboard_endpoint="super_admin_contracts.contracts_overview",
        owned_data=("psra_contracts", "renewal_alerts", "contract_documents"),
        shared_links=("client_id", "template_version_id", "user_id"),
    ),
    ModuleContract(
        key="finance",
        name="Finance Logix",
        status="shell",
        dashboard_endpoint="finance.dashboard",
        owned_data=("budgets", "service_charges", "invoices", "payments", "arrears"),
        shared_links=("client_id", "unit_id", "member_id", "work_order_id"),
    ),
    ModuleContract(
        key="works",
        name="Works Logix",
        status="partial",
        dashboard_endpoint="super_admin.work_orders",
        owned_data=(
            "work_orders",
            "work_order_lifecycle_events",
            "completion_evidence",
            "completion_reviews",
            "reopen_requests",
        ),
        shared_links=(
            "work_order_id",
            "client_id",
            "unit_id",
            "contractor_id",
            "member_request_id",
            "completion_id",
            "reopen_request_id",
            "user_id",
        ),
    ),
    ModuleContract(
        key="members",
        name="Members Logix",
        status="shell",
        dashboard_endpoint="members.dashboard",
        owned_data=(
            "members",
            "residents",
            "unit_memberships",
            "member_requests",
            "member_notifications",
            "mobile_member_app_shell",
        ),
        shared_links=("client_id", "unit_id", "member_id", "resident_id", "user_id"),
    ),
    ModuleContract(
        key="contractor",
        name="Contractor Logix",
        status="shell",
        dashboard_endpoint="contractor.contractor_dashboard",
        owned_data=(
            "contractor_profiles",
            "contractor_teams",
            "compliance",
            "performance",
            "contractor_notifications",
            "mobile_contractor_app_shell",
        ),
        shared_links=("contractor_id", "company_id", "work_order_id", "user_id"),
    ),
    ModuleContract(
        key="hr",
        name="HR Logix",
        status="foundation",
        dashboard_endpoint=None,
        owned_data=(
            "employee_profiles",
            "leave_records",
            "employment_documents",
            "performance_reviews",
            "staff_notifications",
            "mobile_staff_app_shell",
        ),
        shared_links=("user_id", "company_id"),
    ),
    ModuleContract(
        key="director",
        name="Director Logix",
        status="shell",
        dashboard_endpoint="director.dashboard",
        owned_data=("director_visibility", "director_approvals", "governance_views"),
        shared_links=("client_id", "unit_id", "member_id", "user_id"),
    ),
    ModuleContract(
        key="assistant",
        name="Assistant Workspace",
        status="partial",
        dashboard_endpoint="assistant.dashboard",
        owned_data=(
            "assigned_follow_up",
            "support_queue",
            "assigned_works_routing",
            "assistant_manager_cover_queue",
        ),
        shared_links=(
            "client_id",
            "unit_id",
            "user_id",
            "work_order_id",
            "member_request_id",
            "contractor_id",
        ),
    ),
    ModuleContract(
        key="admin_portal",
        name="Admin Portal",
        status="shell",
        dashboard_endpoint="admin_portal.dashboard",
        owned_data=("admin_operations", "client_support_view"),
        shared_links=("client_id", "unit_id", "user_id", "company_id"),
    ),
    ModuleContract(
        key="gar_ai",
        name="GAR AI Layer",
        status="foundation",
        dashboard_endpoint="super_admin.gar_insights",
        owned_data=("context_summaries", "risk_recommendations", "explainability"),
        shared_links=(
            "source_references",
            "visibility_rules",
            "audit_ids",
            "work_order_lifecycle_event_ids",
        ),
    ),
)


def module_contracts() -> tuple[ModuleContract, ...]:
    return MODULE_CONTRACTS


def module_contract_by_key(key: str) -> ModuleContract | None:
    return next((contract for contract in MODULE_CONTRACTS if contract.key == key), None)
