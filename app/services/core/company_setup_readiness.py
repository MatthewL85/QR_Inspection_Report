from __future__ import annotations

from dataclasses import dataclass

from app.models.core.organisation_connection import ModuleSubscription
from app.models.onboarding.company import Company
from app.services.core.module_registry import ModuleContract, module_contracts
from app.services.core.organisation_identity import active_connections_for_company, ensure_company_organisation_uid


@dataclass(frozen=True)
class ModuleSetupReadiness:
    key: str
    name: str
    contract_status: str
    is_enabled: bool
    subscription_status: str
    requires_connection: bool
    dashboard_endpoint: str | None


@dataclass(frozen=True)
class CompanySetupReadiness:
    company_id: int
    organisation_uid: str
    enabled_module_count: int
    active_connection_count: int
    enabled_module_names: tuple[str, ...]
    modules: tuple[ModuleSetupReadiness, ...]

    @property
    def identity_ready(self) -> bool:
        return bool(self.organisation_uid)

    @property
    def has_connections(self) -> bool:
        return self.active_connection_count > 0


def _module_readiness(
    contract: ModuleContract,
    subscription_by_key: dict[str, ModuleSubscription],
) -> ModuleSetupReadiness:
    subscription = subscription_by_key.get(contract.key)
    return ModuleSetupReadiness(
        key=contract.key,
        name=contract.name,
        contract_status=contract.status,
        is_enabled=bool(subscription and subscription.is_active),
        subscription_status=subscription.status if subscription else "not_enabled",
        requires_connection="organisation_connection_id" in contract.shared_links,
        dashboard_endpoint=contract.dashboard_endpoint,
    )


def build_company_setup_readiness(company: Company) -> CompanySetupReadiness:
    """Build the reusable setup state for company profile, onboarding and GAR context."""

    organisation_uid = ensure_company_organisation_uid(company)
    subscriptions = (
        ModuleSubscription.query
        .filter_by(company_id=company.id)
        .order_by(ModuleSubscription.module_key.asc())
        .all()
    )
    subscription_by_key = {subscription.module_key: subscription for subscription in subscriptions}
    connections = active_connections_for_company(company.id)

    modules = tuple(
        _module_readiness(contract, subscription_by_key)
        for contract in module_contracts()
    )
    enabled_module_names = tuple(
        module.name
        for module in modules
        if module.is_enabled
    )

    return CompanySetupReadiness(
        company_id=company.id,
        organisation_uid=organisation_uid,
        enabled_module_count=len(enabled_module_names),
        active_connection_count=len(connections),
        enabled_module_names=enabled_module_names,
        modules=modules,
    )
