# app/routes/client/key_info/utils.py
from __future__ import annotations

from typing import Iterable, Set
from flask import abort, current_app
from flask_login import current_user
from app.extensions import db
from app.models.client.client import Client

# Accept many common spellings/cases for safety
_ALLOWED_ORG_ROLES_NORM: Set[str] = {
    "admin",
    "property manager",
    "financial controller",
    "super admin",
    "superadmin",
    "system admin",
    "system_admin",
    "owner",   # optional, helps during early bootstrapping
}

def _norm(s: str | None) -> str | None:
    if not s:
        return None
    return str(s).replace("_", " ").strip().lower()

def _collect_role_names(user) -> Set[str]:
    """
    Collect role names in a very tolerant way:
      - user.role (object or string)
      - user.role.name
      - user.roles / user.user_roles (iterables)
      - boolean flags like is_super_admin / is_admin
    Returns a normalized (lowercase, spaces) set of names.
    """
    names: Set[str] = set()

    # Single role fields
    for attr in ("role", "user_role", "title"):
        v = getattr(user, attr, None)
        if v is None:
            continue
        name = getattr(v, "name", None)
        name = name or (str(v) if not isinstance(v, str) else v)
        n = _norm(name)
        if n:
            names.add(n)

    # Many-to-many style
    for attr in ("roles", "user_roles"):
        coll = getattr(user, attr, None)
        if not coll:
            continue
        try:
            for r in coll:  # type: ignore[func-returns-value]
                n = _norm(getattr(r, "name", None) or (str(r) if not isinstance(r, str) else r))
                if n:
                    names.add(n)
        except Exception:
            pass

    # Boolean flags -> synthetic names
    flag_map = {
        "is_super_admin": "super admin",
        "is_admin": "admin",
        "is_property_manager": "property manager",
        "is_financial_controller": "financial controller",
    }
    for flag, synth in flag_map.items():
        if getattr(user, flag, False):
            names.add(_norm(synth))  # type: ignore[arg-type]

    # Fallback: if nothing detected and user has an email, allow 'admin' in dev
    return names

def require_org_roles() -> None:
    if not getattr(current_user, "is_authenticated", False):
        abort(401)

    roles = _collect_role_names(current_user)
    allowed = any(r in _ALLOWED_ORG_ROLES_NORM for r in roles)

    if not allowed:
        # Helpful log for diagnosis
        try:
            uid = getattr(current_user, "id", "?")
            current_app.logger.warning(
                f"[KeyInfo] 403 for user {uid}; detected roles={sorted(roles) or '∅'}; "
                f"allowed={sorted(_ALLOWED_ORG_ROLES_NORM)}"
            )
        except Exception:
            pass
        abort(403)

def load_client_or_404(client_id: int) -> Client:
    client = db.session.get(Client, client_id)
    if not client:
        abort(404)
    return client

def safe_int_list(values: list[str]) -> list[int]:
    out: list[int] = []
    for v in values or []:
        try:
            out.append(int(v))
        except Exception:
            continue
    return out
