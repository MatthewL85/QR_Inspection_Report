from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import or_

from app.models.core.organisation_connection import (
    OrganisationConnection,
    OrganisationConnectionInvite,
)
from app.models.onboarding.company import Company
from app.services.core.organisation_identity import ensure_company_organisation_uid


@dataclass(frozen=True)
class ModuleConnectionContext:
    company: Company | None
    organisation_uid: str | None
    active_connections: tuple[OrganisationConnection, ...]
    pending_sent_invites: tuple[OrganisationConnectionInvite, ...]
    pending_received_invites: tuple[OrganisationConnectionInvite, ...]
    integration_readiness: tuple[dict[str, Any], ...]

    @property
    def active_connection_count(self) -> int:
        return len(self.active_connections)

    @property
    def pending_invite_count(self) -> int:
        return len(self.pending_sent_invites) + len(self.pending_received_invites)


def _integration_readiness_for_module(module_key: str) -> tuple[dict[str, Any], ...]:
    """Describe future connection types without pretending they are live yet."""

    common = (
        {
            "name": "LogixPM",
            "kind": "Native module",
            "status": "Available",
            "notes": "Uses organisation UID, module subscription and governed connection permissions.",
        },
        {
            "name": "GAR AI",
            "kind": "Native intelligence layer",
            "status": "Governed",
            "notes": "Reads connected source records only when visibility rules allow it.",
        },
    )

    if module_key == "contractor_logix":
        return common + (
            {
                "name": "Sage / Accounting package",
                "kind": "External finance integration",
                "status": "Future connector",
                "notes": "Would use a dedicated API connector, OAuth/API credentials and invoice/payment mapping.",
            },
            {
                "name": "HR Manager / Cloud HR",
                "kind": "External HR integration",
                "status": "Future connector",
                "notes": "Would sync contractor staff/engineer records through a controlled integration adapter.",
            },
        )

    return common + (
        {
            "name": "Finance Logix / Sage",
            "kind": "Finance connection",
            "status": "Future connector",
            "notes": "Payment requests and invoice data should flow through a governed finance adapter.",
        },
        {
            "name": "HR Logix / HR Manager",
            "kind": "HR connection",
            "status": "Future connector",
            "notes": "Staff records should connect through Core users and an HR-owned profile adapter.",
        },
    )


def module_connection_context(company: Company | None, *, module_key: str) -> ModuleConnectionContext:
    if not company:
        return ModuleConnectionContext(
            company=None,
            organisation_uid=None,
            active_connections=(),
            pending_sent_invites=(),
            pending_received_invites=(),
            integration_readiness=_integration_readiness_for_module(module_key),
        )

    organisation_uid = ensure_company_organisation_uid(company)
    now = datetime.utcnow()

    active_connections = (
        OrganisationConnection.query
        .filter(
            OrganisationConnection.status == "active",
            or_(
                OrganisationConnection.source_company_id == company.id,
                OrganisationConnection.target_company_id == company.id,
            ),
        )
        .order_by(OrganisationConnection.created_at.desc())
        .all()
    )
    pending_sent_invites = (
        OrganisationConnectionInvite.query
        .filter(
            OrganisationConnectionInvite.source_company_id == company.id,
            OrganisationConnectionInvite.status == "pending",
            OrganisationConnectionInvite.expires_at >= now,
        )
        .order_by(OrganisationConnectionInvite.created_at.desc())
        .all()
    )
    pending_received_invites = (
        OrganisationConnectionInvite.query
        .filter(
            OrganisationConnectionInvite.target_company_id == company.id,
            OrganisationConnectionInvite.status == "pending",
            OrganisationConnectionInvite.expires_at >= now,
        )
        .order_by(OrganisationConnectionInvite.created_at.desc())
        .all()
    )

    return ModuleConnectionContext(
        company=company,
        organisation_uid=organisation_uid,
        active_connections=tuple(active_connections),
        pending_sent_invites=tuple(pending_sent_invites),
        pending_received_invites=tuple(pending_received_invites),
        integration_readiness=_integration_readiness_for_module(module_key),
    )
