# app/services/contract/contract_audits.py
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional, Mapping

from flask import g
from sqlalchemy.orm import Session

from app import db  # keep for compatibility with existing imports/usages
from app.models import ContractAudit  # re-exported in app/models/__init__.py


def _current_actor_id() -> Optional[int]:
    """
    Returns the current logged-in user id if available.
    It's safe if no request/app context: returns None.
    """
    user = getattr(g, "user", None)
    return getattr(user, "id", None)


def _to_text_json(value: Any) -> Optional[str]:
    """
    Persist JSON-ish blobs as TEXT safely.
    - None -> None
    - dict/list -> JSON string (pretty if possible)
    - str -> passthrough
    - other -> str(value)
    """
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, indent=2, ensure_ascii=False, default=str)
        except Exception:
            return json.dumps(value, default=str)
    if isinstance(value, str):
        return value
    return str(value)


def create_contract_audit(
    session: Session,
    *,
    contract_id: int,
    action: str,  # "create"|"update"|"renew"|"delete"|"bootstrap"|custom
    before: Optional[Mapping[str, Any]] = None,
    after: Optional[Mapping[str, Any]] = None,
    notes: Optional[str] = None,
    actor_id: Optional[int] = None,
    happened_at: Optional[datetime] = None,
    # ---- GAR/AI optional fields (match DB columns if present) ----
    detail_json: Any = None,
    change_set: Any = None,
    parsed_summary: Optional[str] = None,
    parsed_text: Optional[str] = None,
    extracted_data: Any = None,
    ai_scorecard: Any = None,
    ai_rank: Optional[int] = None,
    is_ai_preferred: Optional[bool] = None,
    reason_for_recommendation: Optional[str] = None,
) -> ContractAudit:
    """
    Insert a ContractAudit row. **Doesn't commit**; caller controls the transaction.

    Notes:
    - Coalesces `is_ai_preferred` -> False to avoid NOT NULL violations.
    - Safely stringifies JSON-like blobs for TEXT columns.
    """
    # Avoid NOT NULL violation on BOOLEAN fields
    is_ai_preferred = bool(is_ai_preferred) if is_ai_preferred is not None else False

    audit = ContractAudit(
        contract_id=contract_id,
        action=action,
        # keep your actor resolution behavior
        actor_id=actor_id if actor_id is not None else _current_actor_id(),
        happened_at=happened_at or datetime.utcnow(),

        # base fields (stringify to fit TEXT columns if needed)
        before_data=_to_text_json(before if before is not None else "null"),
        after_data=_to_text_json(after if after is not None else "null"),
        notes=notes,

        # GAR/AI fields (all optional)
        detail_json=_to_text_json(detail_json),
        change_set=_to_text_json(change_set),
        parsed_summary=parsed_summary,
        parsed_text=parsed_text,
        extracted_data=_to_text_json(extracted_data),
        ai_scorecard=_to_text_json(ai_scorecard),
        ai_rank=ai_rank,
        is_ai_preferred=is_ai_preferred,
        reason_for_recommendation=reason_for_recommendation,
    )
    session.add(audit)
    return audit
