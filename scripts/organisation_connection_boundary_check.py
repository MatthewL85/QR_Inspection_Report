"""Validate organisation identity and cross-module connection boundaries.

Standalone modules must connect through platform-owned organisation records,
module subscriptions and governed connection invites. They must not rely on
email addresses or direct cross-module shortcuts for operational data sharing.
"""

from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.extensions import db
from app.models.core.organisation_connection import (
    ModuleSubscription,
    OrganisationConnection,
    OrganisationConnectionInvite,
)
from app.models.onboarding.company import Company
from app.models.works.work_order import WorkOrder
from app.services.core.organisation_identity import (
    DEFAULT_CONNECTION_PERMISSIONS,
    accept_organisation_connection_invite,
    active_connections_for_company,
    create_organisation_connection_invite,
    ensure_company_organisation_uid,
    generate_connection_code,
    organisation_visibility_boundary,
)


STATIC_EXPECTATIONS = {
    "app/models/onboarding/company.py": (
        "organisation_uid = db.Column",
        "unique=True",
        "nullable=False",
        "default=lambda: str(uuid4())",
        "index=True",
    ),
    "app/models/core/organisation_connection.py": (
        "class ModuleSubscription",
        "class OrganisationConnectionInvite",
        "class OrganisationConnection",
        "invite_code = db.Column",
        "unique=True",
        "source_company_id",
        "target_company_id",
        "permissions_json",
        "uq_organisation_connection_pair_type",
    ),
    "app/services/core/organisation_identity.py": (
        "def generate_connection_code",
        "def ensure_company_organisation_uid",
        "def create_organisation_connection_invite",
        "def accept_organisation_connection_invite",
        "A company cannot accept its own connection invite.",
        "connected_records_only",
    ),
    "app/services/works/workflow_service.py": (
        "_organisation_connection_payload",
        "organisation_connection_id",
        "organisation_connection_status",
        "connected",
    ),
}

CONNECTION_ROUTE_EXPECTATIONS = {
    "app/routes/settings/connections.py": (
        "@settings_bp.route(\"/connections\"",
        "create_organisation_connection_invite",
        "accept_organisation_connection_invite",
        "enable_module_subscription",
    ),
    "app/routes/super_admin/organisation_connections.py": (
        "@super_admin_bp.route(\"/organisation-connections\"",
        "create_organisation_connection_invite",
        "accept_organisation_connection_invite",
        "enable_module_subscription",
    ),
    "app/routes/contractor.py": (
        "@contractor_bp.route('/settings/connections'",
        "@login_required(role='Contractor')",
        "create_organisation_connection_invite",
        "accept_organisation_connection_invite",
    ),
}


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _check_static_contracts(failures: list[str]) -> None:
    for relative_path, markers in STATIC_EXPECTATIONS.items():
        text = _read(relative_path)
        for marker in markers:
            if marker not in text:
                failures.append(f"{relative_path} missing marker: {marker}")

    for relative_path, markers in CONNECTION_ROUTE_EXPECTATIONS.items():
        text = _read(relative_path)
        for marker in markers:
            if marker not in text:
                failures.append(f"{relative_path} missing connection route marker: {marker}")

    work_order_columns = WorkOrder.__table__.columns
    if "organisation_connection_id" not in work_order_columns:
        failures.append("WorkOrder table is missing organisation_connection_id")

    company_columns = Company.__table__.columns
    organisation_uid = company_columns.get("organisation_uid")
    if organisation_uid is None:
        failures.append("Company table is missing organisation_uid")
    else:
        if not organisation_uid.unique:
            failures.append("Company.organisation_uid must be unique")
        if organisation_uid.nullable:
            failures.append("Company.organisation_uid must be non-nullable")

    for model, required_columns in (
        (ModuleSubscription, ("company_id", "module_key", "status")),
        (OrganisationConnectionInvite, ("invite_code", "source_company_id", "target_company_id", "allowed_modules_json")),
        (OrganisationConnection, ("source_company_id", "target_company_id", "connection_type", "permissions_json")),
    ):
        columns = model.__table__.columns
        for column_name in required_columns:
            if column_name not in columns:
                failures.append(f"{model.__name__} missing column: {column_name}")


def _check_connection_codes(failures: list[str]) -> None:
    codes = {generate_connection_code() for _ in range(6)}
    if len(codes) != 6:
        failures.append("Connection code generation produced a duplicate in a six-code sample")
    for code in codes:
        if len(code) < 16 or len(code) > 24 or not code.isalnum() or not code.isupper():
            failures.append(f"Connection code format is unstable: {code!r}")

    for module_key in ("works", "contractor", "gar_ai"):
        if module_key not in DEFAULT_CONNECTION_PERMISSIONS:
            failures.append(f"Default connection permissions missing module: {module_key}")


def _delete_test_records(marker: str) -> None:
    companies = Company.query.filter(Company.name.like(f"{marker}%")).all()
    company_ids = [company.id for company in companies]
    if not company_ids:
        return

    OrganisationConnection.query.filter(
        (OrganisationConnection.source_company_id.in_(company_ids))
        | (OrganisationConnection.target_company_id.in_(company_ids))
    ).delete(synchronize_session=False)
    OrganisationConnectionInvite.query.filter(
        (OrganisationConnectionInvite.source_company_id.in_(company_ids))
        | (OrganisationConnectionInvite.target_company_id.in_(company_ids))
    ).delete(synchronize_session=False)
    ModuleSubscription.query.filter(ModuleSubscription.company_id.in_(company_ids)).delete(synchronize_session=False)
    Company.query.filter(Company.id.in_(company_ids)).delete(synchronize_session=False)
    db.session.commit()


def _check_runtime_connection_flow(failures: list[str]) -> None:
    marker = f"Boundary Check {uuid4()}"
    _delete_test_records(marker)

    source = Company(name=f"{marker} Source", company_type="Property Management", is_active=True)
    target = Company(name=f"{marker} Target", company_type="Contractor", is_active=True)
    db.session.add_all([source, target])
    db.session.commit()

    try:
        source_uid = ensure_company_organisation_uid(source)
        target_uid = ensure_company_organisation_uid(target)
        if not source_uid or not target_uid or source_uid == target_uid:
            failures.append("Organisation UIDs must be present and unique between companies")

        invite = create_organisation_connection_invite(
            source_company_id=source.id,
            target_company_id=target.id,
            connection_type="management_contractor",
            allowed_modules=["works", "contractor", "gar_ai"],
            notes="Created by organisation boundary check.",
        )
        db.session.commit()

        if not invite.invite_code or invite.target_email:
            failures.append("Targeted organisation invite should use code/target company, not target email")
        if invite.status != "pending":
            failures.append("New organisation connection invite should start pending")

        try:
            accept_organisation_connection_invite(invite_code=invite.invite_code, accepting_company_id=source.id)
            failures.append("Source company was able to accept its own invite")
        except ValueError as exc:
            if "cannot accept its own" not in str(exc):
                failures.append(f"Self-accept failed for the wrong reason: {exc}")
            db.session.rollback()

        connection = accept_organisation_connection_invite(
            invite_code=invite.invite_code,
            accepting_company_id=target.id,
        )
        db.session.commit()

        if connection.status != "active":
            failures.append("Accepted organisation connection should be active")
        if connection.source_company_id != source.id or connection.target_company_id != target.id:
            failures.append("Accepted organisation connection linked the wrong companies")

        permissions = connection.permissions_json or {}
        modules = set(permissions.get("modules") or [])
        if modules != {"works", "contractor", "gar_ai"}:
            failures.append(f"Accepted connection modules drifted: {sorted(modules)}")
        for module_key in ("works", "contractor", "gar_ai"):
            if module_key not in (permissions.get("permissions") or {}):
                failures.append(f"Accepted connection permissions missing {module_key}")

        active_for_source = active_connections_for_company(source.id)
        if connection.id not in {item.id for item in active_for_source}:
            failures.append("Active connection lookup did not include the accepted connection")

        boundary = organisation_visibility_boundary(source.id)
        if target.id not in boundary.connected_company_ids:
            failures.append("Organisation visibility boundary did not include connected company")
        if boundary.gar_visibility_scope != "connected_records_only":
            failures.append("GAR visibility boundary must stay connected_records_only")
    finally:
        db.session.rollback()
        _delete_test_records(marker)


def main() -> int:
    failures: list[str] = []
    app = create_app()

    with app.app_context():
        _check_static_contracts(failures)
        _check_connection_codes(failures)
        _check_runtime_connection_flow(failures)

    if failures:
        print("FAILED organisation connection boundary check")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASSED organisation connection boundary check")
    print("- Organisation UIDs are unique tenant identifiers")
    print("- Connection invites use one-time codes and governed acceptance")
    print("- Works/Contractor/GAR sharing is tied to organisation_connection_id")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
