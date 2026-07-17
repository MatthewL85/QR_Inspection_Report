from __future__ import annotations

from app.models.works.work_order import WorkOrder
from app.models.works.work_order_reopen_request import WorkOrderReopenRequest


ADMIN_ROLES = {
    "admin",
    "platform admin",
    "super admin",
    "superadmin",
    "system admin",
}

ASSISTANT_COVER_ROLES = {
    "assistant manager",
    "master assistant",
    "assistant lead",
    "senior assistant",
}

ASSISTANT_ROLES = ASSISTANT_COVER_ROLES | {
    "assistant",
    "assistant property manager",
}

PM_ROLES = {
    "property manager",
}


def works_role_key(user) -> str:
    role_name = (
        getattr(user, "role_name", None)
        or getattr(getattr(user, "role", None), "name", "")
        or ""
    )
    return role_name.strip().lower().replace("_", " ")


def _same_company(user, work_order: WorkOrder, company_id: int | None) -> bool:
    user_company_id = getattr(user, "company_id", None) or getattr(user, "active_company_id", None)
    if not user_company_id or not company_id or user_company_id != company_id:
        return False

    if work_order.company_id and work_order.company_id != company_id:
        return False
    if work_order.client and work_order.client.company_id != company_id:
        return False
    if work_order.unit and work_order.unit.company_id != company_id:
        return False
    return True


def can_manage_work_order(user, work_order: WorkOrder | None, company_id: int | None) -> bool:
    """Return whether a platform user can review/route/close this Works item."""

    if not user or not work_order or not _same_company(user, work_order, company_id):
        return False

    role = works_role_key(user)
    if role in ADMIN_ROLES:
        return True

    client = work_order.client or (work_order.unit.client if work_order.unit else None)
    if not client:
        return False

    user_id = getattr(user, "id", None)
    if role in PM_ROLES:
        return client.assigned_pm_id == user_id

    if role in ASSISTANT_COVER_ROLES:
        return True

    if role in ASSISTANT_ROLES:
        return client.assigned_assistant_id == user_id or client.assigned_pm_id == user_id

    return False


def can_manage_reopen_request(user, reopen_request: WorkOrderReopenRequest | None, company_id: int | None) -> bool:
    if not reopen_request or not reopen_request.work_order:
        return False
    return can_manage_work_order(user, reopen_request.work_order, company_id)
