# app/services/unit_access_service.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import html as html_utils
import secrets
import string

from flask import current_app, has_request_context, url_for
from app.extensions import db
from sqlalchemy.orm import joinedload
from app.models.members.member import Member
from app.models.members.unit import Unit
from app.models.members.unit_access_invite import UnitAccessInvite
from app.models.members.unit_membership import UnitMembership
from app.utils.email import send_email


CLAIM_CODE_ALPHABET = string.ascii_uppercase + string.digits
CLAIM_CODE_GROUPS = (4, 4, 4)
CLAIMABLE_ROLES = {"owner", "co_owner", "resident", "tenant"}


@dataclass
class ClaimResult:
    ok: bool
    message: str
    invite: UnitAccessInvite | None = None
    membership: UnitMembership | None = None


@dataclass
class BulkInviteSummary:
    created: int = 0
    skipped_no_email: int = 0
    skipped_existing_pending: int = 0
    skipped_already_claimed: int = 0
    skipped_already_linked: int = 0
    skipped_no_member: int = 0
    errors: list[str] = field(default_factory=list)
    invites: list[UnitAccessInvite] = field(default_factory=list)


@dataclass
class InviteDeliverySummary:
    sent: int = 0
    skipped_no_email: int = 0
    skipped_not_pending: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


def _normalise_code(code: str) -> str:
    return "".join(char for char in (code or "").upper() if char.isalnum())


def _display_code(raw_code: str) -> str:
    offset = 0
    parts: list[str] = []
    for size in CLAIM_CODE_GROUPS:
        parts.append(raw_code[offset:offset + size])
        offset += size
    return "-".join(part for part in parts if part)


def _new_claim_code() -> str:
    size = sum(CLAIM_CODE_GROUPS)
    for _ in range(20):
        raw_code = "".join(secrets.choice(CLAIM_CODE_ALPHABET) for _ in range(size))
        display_code = _display_code(raw_code)
        if not UnitAccessInvite.query.filter_by(claim_code=display_code).first():
            return display_code
    raise RuntimeError("Could not generate a unique unit access code.")


def create_unit_access_invite(
    unit: Unit,
    *,
    role: str = "owner",
    email: str | None = None,
    created_by_user_id: int | None = None,
    expires_in_days: int = 30,
    notes: str | None = None,
) -> UnitAccessInvite:
    role = (role or "owner").strip().lower()
    if role not in CLAIMABLE_ROLES:
        raise ValueError("Unsupported unit access role.")

    invite = UnitAccessInvite(
        unit_id=unit.id,
        client_id=unit.client_id,
        company_id=unit.company_id,
        claim_code=_new_claim_code(),
        role="owner" if role == "co_owner" else role,
        email=(email or "").strip().lower() or None,
        status="pending",
        expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
        created_by_user_id=created_by_user_id,
        notes=notes,
    )
    db.session.add(invite)
    db.session.commit()
    return invite


def _find_existing_invite(unit_id: int, email: str, role: str) -> UnitAccessInvite | None:
    if not email:
        return None
    return (
        UnitAccessInvite.query
        .filter(
            UnitAccessInvite.unit_id == unit_id,
            UnitAccessInvite.email == email,
            UnitAccessInvite.role == role,
            UnitAccessInvite.status.in_(["pending", "claimed"]),
        )
        .order_by(UnitAccessInvite.created_at.desc())
        .first()
    )


def bulk_create_unit_access_invites_for_client(
    client,
    *,
    created_by_user_id: int | None = None,
    expires_in_days: int = 30,
    dry_run: bool = False,
) -> BulkInviteSummary:
    """
    Create member portal invite codes for current owners on every unit in a client.

    Phase A deliberately creates auditable portal codes only. Email delivery can
    safely build on top of the same UnitAccessInvite records later.
    """
    summary = BulkInviteSummary()
    now = datetime.utcnow()

    units = (
        Unit.query
        .filter(Unit.client_id == client.id)
        .order_by(Unit.block_name.asc(), Unit.core_name.asc(), Unit.unit_number.asc(), Unit.unit_label.asc())
        .all()
    )
    unit_ids = [unit.id for unit in units]
    if not unit_ids:
        return summary

    owner_links = (
        UnitMembership.query
        .options(joinedload(UnitMembership.unit), joinedload(UnitMembership.member))
        .filter(
            UnitMembership.unit_id.in_(unit_ids),
            UnitMembership.role == "owner",
            UnitMembership.is_current.is_(True),
        )
        .order_by(UnitMembership.unit_id.asc(), UnitMembership.is_primary.desc(), UnitMembership.id.asc())
        .all()
    )

    for link in owner_links:
        member = link.member
        unit = link.unit
        if not member:
            summary.skipped_no_member += 1
            continue
        if link.user_id or member.user_id:
            summary.skipped_already_linked += 1
            continue

        email = (member.email or "").strip().lower()
        if not email:
            summary.skipped_no_email += 1
            continue

        existing = _find_existing_invite(link.unit_id, email, "owner")
        if existing and existing.status == "claimed":
            summary.skipped_already_claimed += 1
            continue
        if existing and existing.status == "pending" and existing.expires_at >= now:
            summary.skipped_existing_pending += 1
            continue
        if existing and existing.status == "pending" and existing.expires_at < now and not dry_run:
            existing.status = "expired"

        try:
            if dry_run:
                summary.created += 1
                continue
            invite = create_unit_access_invite(
                unit,
                role="owner",
                email=email,
                created_by_user_id=created_by_user_id,
                expires_in_days=expires_in_days,
                notes=f"Bulk invite generated for {client.name or 'client'} owners.",
            )
            summary.created += 1
            summary.invites.append(invite)
        except Exception as exc:  # pragma: no cover - defensive safety for admin workflow
            db.session.rollback()
            unit_label = unit.unit_label or unit.unit_number or f"Unit #{unit.id}"
            summary.errors.append(f"{unit_label}: {exc}")

    if not dry_run:
        db.session.commit()
    return summary


def _invite_login_url() -> str:
    if has_request_context():
        return url_for("auth.login", _external=True)

    base_url = (current_app.config.get("PUBLIC_BASE_URL") or current_app.config.get("SERVER_NAME") or "").strip()
    if base_url and not base_url.startswith(("http://", "https://")):
        base_url = f"https://{base_url}"
    if base_url:
        return f"{base_url.rstrip('/')}/auth/login"
    return "/auth/login"


def _invite_email_body(invite: UnitAccessInvite) -> str:
    unit = invite.unit
    client = invite.client
    if unit:
        unit_label = unit.unit_label or unit.unit_number or f"Unit #{unit.id}"
    else:
        unit_label = "your unit"
    client_name = client.name if client else "your development"
    expiry = invite.expires_at.strftime("%d %b %Y") if invite.expires_at else "the expiry date"
    return f"""Hello,

You have been invited to link {unit_label} at {client_name} to your Members Logix portal.

Portal code: {invite.claim_code}

Go to: {_invite_login_url()}
Sign in, open Members Logix, then use Add another property and enter the portal code above.

This code expires on {expiry}.

If you were not expecting this invite, please contact your managing agent.

LogixPM
"""


def _invite_email_html(invite: UnitAccessInvite) -> str:
    unit = invite.unit
    client = invite.client
    if unit:
        unit_label = unit.unit_label or unit.unit_number or f"Unit #{unit.id}"
    else:
        unit_label = "your unit"
    client_name = client.name if client else "your development"
    expiry = invite.expires_at.strftime("%d %b %Y") if invite.expires_at else "the expiry date"
    login_url = _invite_login_url()
    return f"""
<div style="font-family: Arial, sans-serif; color: #17233c; line-height: 1.5;">
  <h2 style="margin: 0 0 12px;">Members Logix portal access</h2>
  <p>You have been invited to link <strong>{html_utils.escape(unit_label)}</strong> at <strong>{html_utils.escape(client_name)}</strong> to your Members Logix portal.</p>
  <p style="margin: 20px 0 8px; font-size: 13px; color: #526174; text-transform: uppercase; font-weight: 700;">Portal code</p>
  <p style="display: inline-block; border: 1px solid #cfd6e1; border-radius: 8px; background: #f8fafc; padding: 10px 14px; font-size: 18px; font-weight: 800; letter-spacing: 1px;">{html_utils.escape(invite.claim_code)}</p>
  <p><a href="{html_utils.escape(login_url)}" style="display: inline-block; background: #2152ff; color: #ffffff; text-decoration: none; border-radius: 8px; padding: 10px 16px; font-weight: 700;">Open Members Logix</a></p>
  <p>Sign in, open Members Logix, then use <strong>Add another property</strong> and enter the portal code above.</p>
  <p style="color: #526174;">This code expires on {html_utils.escape(expiry)}.</p>
  <p style="color: #526174; font-size: 13px;">If you were not expecting this invite, please contact your managing agent.</p>
</div>
"""


def send_unit_access_invite(invite: UnitAccessInvite) -> bool:
    if invite.status != "pending" or not invite.is_pending:
        invite.delivery_status = "not_sendable"
        invite.last_delivery_error = "Invite is not pending or has expired."
        db.session.commit()
        return False
    if not invite.email:
        invite.delivery_status = "no_email"
        invite.last_delivery_error = "No email address is recorded for this invite."
        db.session.commit()
        return False

    try:
        send_email(
            subject="Your Members Logix portal access code",
            recipients=[invite.email],
            body=_invite_email_body(invite),
            html=_invite_email_html(invite),
        )
    except Exception as exc:  # pragma: no cover - depends on local SMTP setup
        invite.delivery_status = "failed"
        invite.last_delivery_error = str(exc)
        invite.send_count = (invite.send_count or 0) + 1
        db.session.commit()
        return False

    invite.delivery_status = "sent"
    invite.sent_at = datetime.utcnow()
    invite.send_count = (invite.send_count or 0) + 1
    invite.last_delivery_error = None
    db.session.commit()
    return True


def send_pending_unit_access_invites_for_client(client_id: int) -> InviteDeliverySummary:
    summary = InviteDeliverySummary()
    invites = (
        UnitAccessInvite.query
        .options(joinedload(UnitAccessInvite.unit), joinedload(UnitAccessInvite.client))
        .filter(
            UnitAccessInvite.client_id == client_id,
            UnitAccessInvite.status == "pending",
        )
        .order_by(UnitAccessInvite.created_at.asc())
        .all()
    )

    for invite in invites:
        if not invite.email:
            summary.skipped_no_email += 1
            continue
        if not invite.is_pending:
            summary.skipped_not_pending += 1
            continue
        if send_unit_access_invite(invite):
            summary.sent += 1
        else:
            summary.failed += 1
            if invite.last_delivery_error:
                summary.errors.append(f"{invite.email}: {invite.last_delivery_error}")

    return summary


def cancel_unit_access_invite(invite: UnitAccessInvite, *, reason: str | None = None) -> bool:
    if invite.status != "pending":
        return False
    invite.status = "cancelled"
    invite.delivery_status = "cancelled"
    invite.last_delivery_error = None
    note = (reason or "Invite cancelled by Super Admin.").strip()
    invite.notes = f"{invite.notes}\n{note}".strip() if invite.notes else note
    db.session.commit()
    return True


def _member_for_user(user) -> Member:
    member = Member.query.filter_by(user_id=user.id).first()
    if member:
        return member

    first_name = None
    last_name = None
    if getattr(user, "full_name", None):
        parts = user.full_name.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else None

    member = Member(
        user_id=user.id,
        company_id=getattr(user, "company_id", None),
        first_name=first_name,
        last_name=last_name,
        email=getattr(user, "email", None),
        phone=getattr(user, "mobile_phone", None) or getattr(user, "direct_phone", None),
        is_owner=True,
        is_active=True,
        source_system="Members Logix Claim",
    )
    db.session.add(member)
    db.session.flush()
    return member


def claim_unit_access(code: str, user) -> ClaimResult:
    normalised = _normalise_code(code)
    if not normalised:
        return ClaimResult(False, "Enter the access code supplied by your managing agent.")

    display_code = _display_code(normalised)
    invite = UnitAccessInvite.query.filter_by(claim_code=display_code).first()
    if not invite:
        return ClaimResult(False, "That access code was not recognised.")
    if invite.status != "pending":
        return ClaimResult(False, "That access code has already been used or cancelled.", invite=invite)
    if invite.expires_at < datetime.utcnow():
        invite.status = "expired"
        db.session.commit()
        return ClaimResult(False, "That access code has expired. Please request a new one.", invite=invite)

    user_email = (getattr(user, "email", "") or "").strip().lower()
    if invite.email and invite.email != user_email:
        return ClaimResult(False, "That access code was issued for a different email address.", invite=invite)

    unit = Unit.query.get(invite.unit_id)
    if not unit:
        return ClaimResult(False, "The linked unit could not be found.", invite=invite)

    member = _member_for_user(user)
    member.client_id = member.client_id or invite.client_id
    member.company_id = member.company_id or invite.company_id
    member.email = member.email or user_email
    member.is_owner = member.is_owner or invite.role == "owner"

    membership = UnitMembership.query.filter_by(
        unit_id=invite.unit_id,
        member_id=member.id,
        role=invite.role,
    ).first()
    if membership is None:
        membership = UnitMembership(
            unit_id=invite.unit_id,
            member_id=member.id,
            role=invite.role,
        )
        db.session.add(membership)

    membership.client_id = invite.client_id
    membership.user_id = user.id
    membership.status = "active"
    membership.is_current = True
    membership.access_start = membership.access_start or date.today()
    membership.access_end = None
    membership.verified_at = datetime.utcnow()
    if invite.role == "owner":
        membership.ownership_start_date = membership.ownership_start_date or date.today()

    invite.status = "claimed"
    invite.claimed_by_user_id = user.id
    invite.claimed_by_member_id = member.id
    invite.claimed_at = datetime.utcnow()

    db.session.commit()
    return ClaimResult(True, "Property access added to your Members Logix portal.", invite=invite, membership=membership)
