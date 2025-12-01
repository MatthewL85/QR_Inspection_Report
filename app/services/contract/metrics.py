# app/service/contract/metrics.py
from __future__ import annotations
from typing import Dict, Iterable
from decimal import Decimal

from app import db
from sqlalchemy import func
from app.models.contracts import ClientContract
from app.models.client.client import Client


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

# Normalise labels so templates are stable even if DB has None/empty
def _norm(status: str | None) -> str:
    s = (status or "").strip()
    return s if s else "Draft"

def _currency_symbol(code: str | None) -> str:
    code = (code or "").upper()
    return {
        "EUR": "€",
        "GBP": "£",
        "USD": "$",
    }.get(code, "€")  # default to Euro for your app


# ─────────────────────────────────────────────────────────────────────────────
# Existing: signature status metrics (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def signature_status_metrics(*, company_id: int | None = None) -> Dict[str, int]:
    """
    Returns counts by signature status for contracts visible to a company.
    Keys include: Draft, Sent, Signed, Declined, Expired, and total.
    """
    q = (
        db.session.query(ClientContract.sign_status, func.count())
        .select_from(ClientContract)
        .join(Client, Client.id == ClientContract.client_id)
    )
    if company_id:
        q = q.filter(Client.company_id == company_id)

    rows = q.group_by(ClientContract.sign_status).all()

    counts: Dict[str, int] = {
        "Draft": 0,
        "Sent": 0,
        "Signed": 0,
        "Declined": 0,
        "Expired": 0,
    }
    total = 0
    for status, cnt in rows:
        k = _norm(status)
        counts[k] = counts.get(k, 0) + int(cnt)
        total += int(cnt)

    counts["Total"] = total
    counts["Pending"] = counts.get("Sent", 0)  # synonym if you want a "Pending" tile
    return counts


# ─────────────────────────────────────────────────────────────────────────────
# NEW: Managed Portfolio (booked revenue only)
# ─────────────────────────────────────────────────────────────────────────────
def managed_portfolio_total(
    *,
    company_id: int | None = None,
    base_currency: str = "EUR",
    include_statuses: Iterable[str] = ("Signed",),  # set to ("Signed","Active") if needed
) -> float:
    """
    Sum of contract_value for SIGNED contracts (booked revenue), scoped by company.

    Rules:
    - Case-insensitive status matching (e.g., 'signed', 'SIGNED', 'Signed')
    - Excludes ARCHIVED (any case) and soft-deleted rows
    - Filters to the given base_currency (or rows with NULL currency)
    """
    # Choose a status column that exists in your model
    status_col = getattr(ClientContract, "sign_status", None) or getattr(ClientContract, "status", None)

    q = (
        db.session.query(func.coalesce(func.sum(ClientContract.contract_value), 0))
        .select_from(ClientContract)
        .join(Client, Client.id == ClientContract.client_id)
    )

    if status_col is not None:
        wanted = [s.lower() for s in include_statuses]
        q = q.filter(func.lower(status_col).in_(wanted))
        # explicitly exclude archived regardless of letter case
        q = q.filter(func.lower(status_col) != "archived")

    if company_id:
        q = q.filter(Client.company_id == company_id)

    # exclude soft-deleted if column exists
    if hasattr(ClientContract, "is_deleted"):
        q = q.filter((ClientContract.is_deleted.is_(False)) | (ClientContract.is_deleted.is_(None)))

    # currency filter (include NULL as a safety)
    if hasattr(ClientContract, "currency"):
        q = q.filter((ClientContract.currency == base_currency) | (ClientContract.currency.is_(None)))

    total = q.scalar() or 0
    # ensure primitive float
    if isinstance(total, Decimal):
        total = float(total)
    return float(total)


def managed_portfolio_display(
    *,
    company_id: int | None = None,
    base_currency: str = "EUR",
    include_statuses: Iterable[str] = ("Signed",),
    show_cents: bool = False,
) -> str:
    """
    Convenience: returns a human string like '€160,006' (or with cents if desired).
    """
    amt = managed_portfolio_total(
        company_id=company_id,
        base_currency=base_currency,
        include_statuses=include_statuses,
    )
    sym = _currency_symbol(base_currency)
    if show_cents:
        return f"{sym}{amt:,.2f}"
    return f"{sym}{amt:,.0f}"
