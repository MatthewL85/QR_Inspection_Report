from __future__ import annotations
from datetime import datetime
from typing import Any, Optional, Mapping

from flask import g
from sqlalchemy.orm import Session

from app import db
from app.models import ContractAudit  # re-exported in app/models/__init__.py


def _current_actor_id() -> Optional[int]:
    """
    Returns the current logged-in user id if available.
    It's safe if no request/app context: returns None.
    """
    user = getattr(g, "user", None)
    return getattr(user, "id", None)


def create_contract_audit(
    session: Session,
    *,
    contract_id: int,
    action: str,  # "create"|"update"|"renew"|"delete"|"bootstrap"
    before: Optional[Mapping[str, Any]] = None,
    after: Optional[Mapping[str, Any]] = None,
    notes: Optional[str] = None,
    actor_id: Optional[int] = None,
    happened_at: Optional[datetime] = None,
) -> ContractAudit:
    """
    Insert a ContractAudit row. Doesn't commit; caller controls the transaction.
    """
    audit = ContractAudit(
        contract_id=contract_id,
        action=action,
        actor_id=actor_id if actor_id is not None else _current_actor_id(),
        happened_at=happened_at or datetime.utcnow(),
        before_data=(dict(before) if before else None),
        after_data=(dict(after) if after else None),
        notes=notes,
    )
    session.add(audit)
    return audit
