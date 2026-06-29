from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.extensions import db
from app.models.contractor.contractor import Contractor
from app.models.core.organisation_connection import (
    ModuleSubscription,
    OrganisationConnection,
    OrganisationConnectionInvite,
)
from app.models.onboarding.company import Company
from app.models.works.work_order import WorkOrder
from app.services.core.module_registry import module_contract_by_key
from app.services.core.organisation_identity import (
    DEFAULT_CONNECTION_PERMISSIONS,
    OrganisationVisibilityBoundary,
    generate_connection_code,
)


def main() -> int:
    failures: list[str] = []
    app = create_app()

    with app.app_context():
        expected_tables = {
            "module_subscriptions": ModuleSubscription,
            "organisation_connection_invites": OrganisationConnectionInvite,
            "organisation_connections": OrganisationConnection,
        }
        for table_name in expected_tables:
            if table_name not in db.metadata.tables:
                failures.append(f"Missing SQLAlchemy table metadata: {table_name}")

        if not hasattr(Company, "organisation_uid"):
            failures.append("Company is missing organisation_uid.")
        if not hasattr(Contractor, "company_id"):
            failures.append("Contractor is missing company_id.")
        if not hasattr(WorkOrder, "organisation_connection_id"):
            failures.append("WorkOrder is missing organisation_connection_id.")

        core_contract = module_contract_by_key("core")
        if not core_contract:
            failures.append("Core module contract is missing.")
        else:
            for owned_name in ("organisation_uids", "module_subscriptions", "organisation_connections"):
                if owned_name not in core_contract.owned_data:
                    failures.append(f"Core module contract is missing owned data: {owned_name}")
            for link_name in ("organisation_uid", "module_subscription_id", "organisation_connection_id"):
                if link_name not in core_contract.shared_links:
                    failures.append(f"Core module contract is missing shared link: {link_name}")

        for module_key in ("works", "contractor", "gar_ai"):
            contract = module_contract_by_key(module_key)
            if not contract:
                failures.append(f"Module contract is missing: {module_key}")
            elif "organisation_connection_id" not in contract.shared_links:
                failures.append(f"{module_key} contract must expose organisation_connection_id.")

        code = generate_connection_code()
        if len(code) < 16 or len(code) > 24 or not code.isalnum() or not code.isupper():
            failures.append("Connection invite code format is not stable.")

        if "works" not in DEFAULT_CONNECTION_PERMISSIONS:
            failures.append("Default connection permissions must include Works Logix.")
        if "contractor" not in DEFAULT_CONNECTION_PERMISSIONS:
            failures.append("Default connection permissions must include Contractor Logix.")
        if "gar_ai" not in DEFAULT_CONNECTION_PERMISSIONS:
            failures.append("Default connection permissions must include GAR AI.")

        boundary_fields = set(OrganisationVisibilityBoundary.__dataclass_fields__)
        for field_name in ("company_id", "connected_company_ids", "active_module_keys", "gar_visibility_scope"):
            if field_name not in boundary_fields:
                failures.append(f"Organisation visibility boundary missing field: {field_name}")

        company_profile_template = ROOT / "app" / "templates" / "settings" / "company_profile" / "index.html"
        if not company_profile_template.exists():
            failures.append("Company Profile setup surface is missing.")
        else:
            template_text = company_profile_template.read_text(encoding="utf-8")
            for marker in ("Organisation UID", "Enabled Modules", "Active Connections", "Module & Connection Readiness"):
                if marker not in template_text:
                    failures.append(f"Company Profile setup surface is missing marker: {marker}")

    if failures:
        print("Core platform identity check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Core platform identity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
