# app/models/listeners/contract_audit_json_safety.py
"""
Safeguard for JSON/JSONB columns on ContractAudit to prevent "DatatypeMismatch"
or formatting errors when strings like 'null' or JSON-encoded strings are passed.

✅ What it fixes
Inserts like:
  detail_json='null', before_data='"null"', after_data='"{...}"'
cause Postgres to treat them as TEXT instead of JSONB.

This listener coerces those fields to proper JSON (None / dict / list / primitives)
right before INSERT/UPDATE — no changes needed at callsites.

📦 Usage
- Drop this file in your project.
- Ensure it's imported once on app startup (e.g., in app/__init__.py after models are imported):

    # app/__init__.py
    # ...
    from app.models.listeners import contract_audit_json_safety  # noqa: F401  (side-effect import)

"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import event

# Adjust this import path if your model lives elsewhere
from app.models.contract.contract_audit import ContractAudit  # type: ignore


_JSON_FIELDS = (
    "detail_json",
    "before_data",
    "after_data",
    "change_set",
    "extracted_data",
    "ai_scorecard",
)


def _to_json_safe(value: Any) -> Any:
    """Best-effort coercion to a JSON-serialisable Python object."""
    if value is None:
        return None

    # Already JSON-compatible primitives
    if isinstance(value, (bool, int, float, list, dict)):
        return value

    # Decimal -> float (or string if you prefer exactness)
    if isinstance(value, Decimal):
        try:
            return float(value)
        except Exception:
            return str(value)

    # Dates -> ISO 8601
    if isinstance(value, (date, datetime)):
        try:
            return value.isoformat()
        except Exception:
            return str(value)

    # If it's a JSON **string**, try to parse
    if isinstance(value, str):
        s = value.strip()
        if s in {"", "null", "NULL", '"null"'}:
            return None
        # If it looks like JSON, attempt to decode
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            try:
                return json.loads(s)
            except Exception:
                # fall through to return the raw string
                pass
        # If it looks like a quoted JSON string (double-encoded), try to unquote once
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            try:
                unq = json.loads(s)
                # If the unquoted also looks like JSON, parse again
                if isinstance(unq, str) and (
                    (unq.startswith("{") and unq.endswith("}")) or (unq.startswith("[") and unq.endswith("]"))
                ):
                    try:
                        return json.loads(unq)
                    except Exception:
                        return unq
                return unq
            except Exception:
                pass
        return s  # return as plain string (still JSON-serialisable)

    # Fallback to string representation
    try:
        json.dumps(value)  # probe
        return value
    except Exception:
        return str(value)


def _coerce_json_fields(target: ContractAudit) -> None:
    """
    Mutate target's JSON fields in-place to ensure proper Python JSON types
    (None/dict/list/primitive) before hitting the DB.
    """
    for name in _JSON_FIELDS:
        if hasattr(target, name):
            try:
                current = getattr(target, name)
                coerced = _to_json_safe(current)
                setattr(target, name, coerced)
            except Exception:
                # Never fail the request because of the coercion step;
                # keep original value if anything goes wrong.
                pass


@event.listens_for(ContractAudit, "before_insert", propagate=True)
def _contract_audit_before_insert(mapper, connection, target: ContractAudit):  # noqa: D401
    _coerce_json_fields(target)


@event.listens_for(ContractAudit, "before_update", propagate=True)
def _contract_audit_before_update(mapper, connection, target: ContractAudit):  # noqa: D401
    _coerce_json_fields(target)
