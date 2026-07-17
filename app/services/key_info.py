# app/services/key_info.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any, Set

from flask_login import current_user
from sqlalchemy import select

from app.extensions import db
from app.models.client.key_info import (
    ClientKeyInfo,
    ClientKeyInfoChange,
    ClientKeyInfoShare,
)

# ─────────────────────────────────────────────────────────────────────────────
# Role helpers (robust & backwards compatible with your previous constants)
# ─────────────────────────────────────────────────────────────────────────────
# Original constants retained (not used directly by checks anymore, but kept
# for backwards compatibility with any external import that might read them).
APPROVERS = {"Admin", "Property Manager", "Financial Controller", "Super Admin"}
# ⬇️ Contractors can now propose (guarded below)
PROPOSERS = {"Admin", "Property Manager", "Financial Controller", "Super Admin", "Contractor", "Admin Contractor"}

# Normalisation helpers
def _norm(s: str | None) -> str | None:
    if not s:
        return None
    return str(s).replace("_", " ").strip().lower()

def _collect_role_names(user) -> Set[str]:
    """
    Gather role names from:
      - user.role / user.role.name
      - user.roles / user.user_roles (iterables)
      - boolean flags: is_super_admin, is_admin, is_property_manager, is_financial_controller
    Return a set of normalized names (lowercase, spaces instead of underscores).
    """
    names: Set[str] = set()
    if not user:
        return names

    # Single role object/string
    for attr in ("role", "user_role", "title"):
        v = getattr(user, attr, None)
        if v is None:
            continue
        name = getattr(v, "name", None)
        name = name or (v if isinstance(v, str) else str(v))
        n = _norm(name)
        if n:
            names.add(n)

    # Many-to-many roles
    for attr in ("roles", "user_roles"):
        coll = getattr(user, attr, None)
        if not coll:
            continue
        try:
            for r in coll:  # type: ignore[func-returns-value]
                nm = getattr(r, "name", None)
                nm = nm or (r if isinstance(r, str) else str(r))
                n = _norm(nm)
                if n:
                    names.add(n)
        except Exception:
            pass

    # Boolean flags -> synthetic role names
    flag_map = {
        "is_super_admin": "super admin",
        "is_admin": "admin",
        "is_property_manager": "property manager",
        "is_financial_controller": "financial controller",
    }
    for flag, synth in flag_map.items():
        if getattr(user, flag, False):
            n = _norm(synth)
            if n:
                names.add(n)

    return names

# Accepted names (normalized)
_APPROVERS = {
    "admin",
    "financial controller",
    "property manager",
    "super admin",
    "superadmin",
    "system admin",
    "system admin",  # duplicate safe
}
_PROPOSERS = {
    "admin",
    "property manager",
    "financial controller",
    "super admin",
    "superadmin",
    "system admin",
    "contractor",
    "admin contractor",
    "owner",  # optional helper during bootstrapping
}

def can_approve(user) -> bool:
    if not user:
        return False
    # explicit super-admin flag wins
    if getattr(user, "is_super_admin", False):
        return True
    roles = _collect_role_names(user)
    return any(r in _APPROVERS for r in roles)

def can_propose(user) -> bool:
    if not user:
        return False
    if getattr(user, "is_super_admin", False):
        return True
    roles = _collect_role_names(user)
    return any(r in _PROPOSERS for r in roles)


# ─────────────────────────────────────────────────────────────────────────────
# Contractor guardrails
# ─────────────────────────────────────────────────────────────────────────────
def _current_contractor_id(user) -> Optional[int]:
    """
    Resolve the contractor/company id for a contractor user.
    Adapt attribute names if your User model differs.
    """
    for attr in ("contractor_id", "company_id", "contractorId"):
        cid = getattr(user, attr, None)
        if cid is not None:
            try:
                return int(cid)
            except Exception:
                return None
    return None


def _is_contractor_shared_on_section(contractor_id: int, key_info: ClientKeyInfo) -> bool:
    return any(s.contractor_id == contractor_id for s in (key_info.shares or []))


def is_contractor_linked_to_client(user, client_id: int) -> bool:
    """
    Hook for your business rule: should this contractor be allowed to propose for this client?
    Default = True (permissive) so you don't block while wiring associations.
    Replace with a real check (e.g., active framework/contract, assigned vendor, etc.).
    """
    # Example (pseudo):
    # return db.session.scalar(
    #   select(ClientContractorLink).where(
    #       ClientContractorLink.client_id == client_id,
    #       ClientContractorLink.contractor_id == _current_contractor_id(user),
    #       ClientContractorLink.is_active.is_(True)
    #   ).exists()
    # )
    return True


def contractor_can_propose_for(user, client_id: int, key_info: ClientKeyInfo | None) -> bool:
    """
    Contractors can propose if:
      - role in {"Contractor", "Admin Contractor"} (normalized in can_propose)
      - they are linked to the client (hook above), and
      - when editing an existing section, the section is already shared with them.
      - when proposing a new section (key_info is None), linking to the client is sufficient.
    """
    # quick gate—only run this for contractor roles
    roles = _collect_role_names(user)
    if not any(r in {"contractor", "admin contractor"} for r in roles):
        return False

    cid = _current_contractor_id(user)
    if not cid:
        return False

    if not is_contractor_linked_to_client(user, client_id):
        return False

    if key_info is None:
        return True

    return _is_contractor_shared_on_section(cid, key_info)


# ─────────────────────────────────────────────────────────────────────────────
# AI/GAR helper stubs (safe defaults)
# Hook your parsers/LLM pipeline here to enrich rows on approval.
# ─────────────────────────────────────────────────────────────────────────────
def _ai_enrich_from_content(content: str) -> Dict[str, Any]:
    """
    Return a dict with AI/GAR-ready values. Keep deterministic fallbacks
    so dashboards never break if the AI pipeline is disabled.
    """
    text = (content or "").strip()
    summary = (text[:180] + "…") if len(text) > 180 else text
    # NOTE: Extend with your real extractors later
    return {
        "ai_parsed_text": text,
        "ai_parsed_summary": summary,
        "ai_extracted_data": {},
        "ai_tags": ["key-info"],
        "ai_redaction_hints": {},
        "ai_visibility_flags": {"share_in_dash_tiles": True},
        "ai_scorecard": {"completeness": 0.75, "risk": 0.15},
        "ai_rank": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Core operations
# ─────────────────────────────────────────────────────────────────────────────
def apply_change(change: ClientKeyInfoChange, approver, reason: Optional[str] = None) -> ClientKeyInfo:
    """
    Approve a pending change and publish it to ClientKeyInfo, synchronising
    per-contractor shares. Admin, FC, PM and Super Admin can approve.
    """
    if not can_approve(approver):
        raise PermissionError("Only Admin, Financial Controller, Property Manager or Super Admin can approve.")

    contractor_ids = change.proposed_contractor_ids or []
    enrich = _ai_enrich_from_content(change.proposed_content)

    if change.key_info:
        # Update existing section
        ki = change.key_info
        ki.title = change.proposed_title.strip()
        ki.content = change.proposed_content
        ki.approved_by_id = approver.id
        ki.approved_at = datetime.utcnow()
        ki.last_submitted_by_id = change.submitted_by_id

        # AI/GAR fields
        ki.ai_parsed_text = enrich["ai_parsed_text"]
        ki.ai_parsed_summary = enrich["ai_parsed_summary"]
        ki.ai_extracted_data = enrich["ai_extracted_data"]
        ki.ai_tags = enrich["ai_tags"]
        ki.ai_redaction_hints = enrich["ai_redaction_hints"]
        ki.ai_visibility_flags = enrich["ai_visibility_flags"]
        ki.ai_scorecard = enrich["ai_scorecard"]
        ki.ai_rank = enrich["ai_rank"]

        # Resync shares
        for s in list(ki.shares):
            db.session.delete(s)
        for cid in contractor_ids:
            db.session.add(ClientKeyInfoShare(key_info=ki, contractor_id=int(cid)))

    else:
        # Create new section
        ki = ClientKeyInfo(
            client_id=change.client_id,
            title=change.proposed_title.strip(),
            content=change.proposed_content,
            approved_by_id=approver.id,
            approved_at=datetime.utcnow(),
            last_submitted_by_id=change.submitted_by_id,
            # AI/GAR
            ai_parsed_text=enrich["ai_parsed_text"],
            ai_parsed_summary=enrich["ai_parsed_summary"],
            ai_extracted_data=enrich["ai_extracted_data"],
            ai_tags=enrich["ai_tags"],
            ai_redaction_hints=enrich["ai_redaction_hints"],
            ai_visibility_flags=enrich["ai_visibility_flags"],
            ai_scorecard=enrich["ai_scorecard"],
            ai_rank=enrich["ai_rank"],
        )
        db.session.add(ki)
        db.session.flush()  # ensure ki.id for share rows
        for cid in contractor_ids:
            db.session.add(ClientKeyInfoShare(key_info_id=ki.id, contractor_id=int(cid)))

    # Finalise change
    change.status = "approved"
    change.decided_by_id = approver.id
    change.decided_at = datetime.utcnow()
    change.decision_reason = (reason or "Approved").strip()

    db.session.commit()
    return ki


def reject_change(change: ClientKeyInfoChange, approver, reason: Optional[str] = None) -> None:
    """
    Reject a pending change. Admin, FC, PM and Super Admin can reject.
    """
    if not can_approve(approver):
        raise PermissionError("Only Admin, Financial Controller, Property Manager or Super Admin can reject.")

    change.status = "rejected"
    change.decided_by_id = approver.id
    change.decided_at = datetime.utcnow()
    change.decision_reason = (reason or "Rejected").strip()
    db.session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Proposal creation helper (used by contractor & org routes)
# ─────────────────────────────────────────────────────────────────────────────
def create_proposal(
    *,
    client_id: int,
    submitted_by,
    title: str,
    content: str,
    key_info: ClientKeyInfo | None = None,
    proposed_contractor_ids: Optional[list[int]] = None,
    pro_attested_by_contractor: bool = False,
    pro_attestation_note: Optional[str] = None,
) -> ClientKeyInfoChange:
    """
    Safe way to create a proposal record with guardrails:
      - checks role via can_propose()
      - if contractor, enforces contractor_can_propose_for() and
        auto-forces sharing to the contractor's own company if none provided
    """
    if not can_propose(submitted_by):
        raise PermissionError("You are not allowed to propose changes.")

    # Contractor guardrails (based on normalized role names)
    roles = _collect_role_names(submitted_by)
    if any(r in {"contractor", "admin contractor"} for r in roles):
        if not contractor_can_propose_for(submitted_by, client_id, key_info):
            raise PermissionError("Contractor is not allowed to propose for this client/section.")
        # Always share back to the contractor's own company at minimum
        own_cid = _current_contractor_id(submitted_by)
        base_ids = [own_cid] if own_cid else []
    else:
        base_ids = []

    # Final proposed share set
    contractor_ids = list({*(proposed_contractor_ids or []), *base_ids})

    change = ClientKeyInfoChange(
        client_id=client_id,
        key_info_id=key_info.id if key_info else None,
        proposed_title=(title or (key_info.title if key_info else "")).strip(),
        proposed_content=content,
        proposed_contractor_ids=contractor_ids,
        submitted_by_id=submitted_by.id,
        pro_attested_by_contractor=bool(pro_attested_by_contractor),
        pro_attestation_note=(pro_attestation_note or "").strip() or None,
    )
    db.session.add(change)
    db.session.commit()
    return change


# ─────────────────────────────────────────────────────────────────────────────
# Convenience queries (for dashboards / widgets)
# ─────────────────────────────────────────────────────────────────────────────
def list_published_for_client(client_id: int) -> list[ClientKeyInfo]:
    return (
        db.session.query(ClientKeyInfo)
        .filter_by(client_id=client_id, status="active")
        .order_by(ClientKeyInfo.title.asc())
        .all()
    )


def list_pending_changes(client_id: int) -> list[ClientKeyInfoChange]:
    return (
        db.session.query(ClientKeyInfoChange)
        .filter_by(client_id=client_id, status="pending")
        .order_by(ClientKeyInfoChange.submitted_at.desc())
        .all()
    )
