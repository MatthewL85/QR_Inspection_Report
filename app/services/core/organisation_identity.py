from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from secrets import token_urlsafe
from uuid import uuid4

from sqlalchemy import or_

from app.extensions import db
from app.models.core.organisation_connection import (
    ModuleSubscription,
    OrganisationConnection,
    OrganisationConnectionInvite,
)
from app.models.onboarding.company import Company
from app.services.core.module_registry import module_contract_by_key


DEFAULT_CONNECTION_PERMISSIONS = {
    "works": ["work_order_offer", "job_docket", "schedule", "progress_update", "completion_evidence"],
    "contractor": ["work_queue", "calendar", "job_docket", "field_updates"],
    "gar_ai": ["connected_records_only"],
}


@dataclass(frozen=True)
class OrganisationVisibilityBoundary:
    company_id: int
    connected_company_ids: tuple[int, ...]
    active_module_keys: tuple[str, ...]
    gar_visibility_scope: str


def generate_connection_code() -> str:
    """Create a short one-time connection code that remains globally unique."""

    return token_urlsafe(18).replace("-", "").replace("_", "")[:24].upper()


def ensure_company_organisation_uid(company: Company) -> str:
    if not company.organisation_uid:
        company.organisation_uid = str(uuid4())
    return company.organisation_uid


def enable_module_subscription(
    *,
    company_id: int,
    module_key: str,
    plan: str | None = None,
    config: dict | None = None,
    created_by_user_id: int | None = None,
) -> ModuleSubscription:
    """Idempotently enable a module for one organisation."""

    if not module_contract_by_key(module_key):
        raise ValueError(f"Unknown module key: {module_key}")

    subscription = ModuleSubscription.query.filter_by(
        company_id=company_id,
        module_key=module_key,
    ).first()
    if not subscription:
        subscription = ModuleSubscription(
            company_id=company_id,
            module_key=module_key,
            created_by_user_id=created_by_user_id,
        )
        db.session.add(subscription)

    subscription.status = "active"
    subscription.plan = plan or subscription.plan
    subscription.config_json = config if config is not None else subscription.config_json
    subscription.disabled_at = None
    subscription.enabled_at = subscription.enabled_at or datetime.utcnow()
    return subscription


def create_organisation_connection_invite(
    *,
    source_company_id: int,
    target_company_id: int | None = None,
    target_email: str | None = None,
    connection_type: str = "management_contractor",
    allowed_modules: list[str] | None = None,
    expires_in_days: int = 30,
    created_by_user_id: int | None = None,
    notes: str | None = None,
) -> OrganisationConnectionInvite:
    """Create a one-time connection invitation between organisations."""

    source_company = Company.query.get(source_company_id)
    if not source_company:
        raise ValueError("Source company does not exist.")

    if target_company_id and not Company.query.get(target_company_id):
        raise ValueError("Target company does not exist.")

    for module_key in allowed_modules or []:
        if not module_contract_by_key(module_key):
            raise ValueError(f"Unknown module key: {module_key}")

    invite = OrganisationConnectionInvite(
        source_company_id=source_company_id,
        target_company_id=target_company_id,
        target_email=(target_email or "").strip() or None,
        connection_type=connection_type,
        allowed_modules_json=allowed_modules or list(DEFAULT_CONNECTION_PERMISSIONS),
        expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
        created_by_user_id=created_by_user_id,
        notes=notes,
    )

    while True:
        invite.invite_code = generate_connection_code()
        if not OrganisationConnectionInvite.query.filter_by(invite_code=invite.invite_code).first():
            break

    db.session.add(invite)
    return invite


def accept_organisation_connection_invite(
    *,
    invite_code: str,
    accepting_company_id: int,
    accepted_by_user_id: int | None = None,
) -> OrganisationConnection:
    """Accept a pending invite and create or reactivate the governed connection."""

    invite = OrganisationConnectionInvite.query.filter_by(invite_code=invite_code).first()
    if not invite or not invite.is_pending:
        raise ValueError("Connection invite is not available.")

    if invite.source_company_id == accepting_company_id:
        raise ValueError("A company cannot accept its own connection invite.")

    if invite.target_company_id and invite.target_company_id != accepting_company_id:
        raise ValueError("This connection invite is assigned to a different company.")

    connection = OrganisationConnection.query.filter_by(
        source_company_id=invite.source_company_id,
        target_company_id=accepting_company_id,
        connection_type=invite.connection_type,
    ).first()
    if not connection:
        connection = OrganisationConnection(
            source_company_id=invite.source_company_id,
            target_company_id=accepting_company_id,
            connection_type=invite.connection_type,
            source_invite_id=invite.id,
            created_by_user_id=invite.created_by_user_id,
        )
        db.session.add(connection)

    connection.status = "active"
    connection.permissions_json = {
        "modules": invite.allowed_modules_json or list(DEFAULT_CONNECTION_PERMISSIONS),
        "permissions": DEFAULT_CONNECTION_PERMISSIONS,
    }
    connection.accepted_by_user_id = accepted_by_user_id
    connection.accepted_at = datetime.utcnow()

    invite.status = "accepted"
    invite.target_company_id = accepting_company_id
    invite.accepted_by_user_id = accepted_by_user_id
    invite.accepted_at = connection.accepted_at
    return connection


def active_connections_for_company(company_id: int) -> list[OrganisationConnection]:
    return (
        OrganisationConnection.query
        .filter(
            OrganisationConnection.status == "active",
            or_(
                OrganisationConnection.source_company_id == company_id,
                OrganisationConnection.target_company_id == company_id,
            ),
        )
        .order_by(OrganisationConnection.created_at.desc())
        .all()
    )


def has_active_organisation_connection(
    *,
    company_id: int,
    connected_company_id: int,
    connection_type: str | None = None,
) -> bool:
    query = OrganisationConnection.query.filter(
        OrganisationConnection.status == "active",
        or_(
            (OrganisationConnection.source_company_id == company_id)
            & (OrganisationConnection.target_company_id == connected_company_id),
            (OrganisationConnection.source_company_id == connected_company_id)
            & (OrganisationConnection.target_company_id == company_id),
        ),
    )
    if connection_type:
        query = query.filter(OrganisationConnection.connection_type == connection_type)
    return db.session.query(query.exists()).scalar()


def organisation_visibility_boundary(company_id: int) -> OrganisationVisibilityBoundary:
    connections = active_connections_for_company(company_id)
    connected_company_ids = tuple(
        sorted(
            company_id_value
            for connection in connections
            if (company_id_value := connection.other_company_id(company_id)) is not None
        )
    )
    active_module_keys = tuple(
        row.module_key
        for row in ModuleSubscription.query.filter_by(company_id=company_id, status="active").order_by(ModuleSubscription.module_key.asc())
    )
    return OrganisationVisibilityBoundary(
        company_id=company_id,
        connected_company_ids=connected_company_ids,
        active_module_keys=active_module_keys,
        gar_visibility_scope="connected_records_only",
    )
