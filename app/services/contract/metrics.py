# app/service/contract/metrics.py
from __future__ import annotations
from typing import Dict

from app import db
from sqlalchemy import func
from app.models.contracts import ClientContract
from app.models.client.client import Client

# Normalise labels so templates are stable even if DB has None/empty
def _norm(status: str | None) -> str:
    s = (status or "").strip()
    return s if s else "Draft"

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
