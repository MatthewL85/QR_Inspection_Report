from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from app.extensions import db
from app.models.client.client import Client
from app.models.contracts import ClientContract
from app.models.core.notification import Notification
from app.models.core.user import User


ALERT_BUCKETS = {
    "expired": {"label": "Expired", "priority": "High", "max_days": -1},
    "30": {"label": "Due in 30 days", "priority": "High", "min_days": 0, "max_days": 30},
    "60": {"label": "Due in 60 days", "priority": "Medium", "min_days": 31, "max_days": 60},
    "90": {"label": "Due in 90 days", "priority": "Medium", "min_days": 61, "max_days": 90},
}


@dataclass(frozen=True)
class ContractRenewalAlert:
    contract: ClientContract
    bucket: str
    label: str
    priority: str
    days_to_expiry: int


def renewal_bucket(end_date: date | None, today: date | None = None) -> tuple[str | None, int | None]:
    if not end_date:
        return None, None
    today = today or date.today()
    days = (end_date - today).days
    if days < 0:
        return "expired", days
    if days <= 30:
        return "30", days
    if days <= 60:
        return "60", days
    if days <= 90:
        return "90", days
    return None, days


def contract_renewal_alerts(company_id: int | None = None, today: date | None = None) -> list[ContractRenewalAlert]:
    today = today or date.today()
    query = (
        ClientContract.query
        .join(Client, Client.id == ClientContract.client_id)
        .filter(ClientContract.end_date.isnot(None))
    )
    if company_id:
        query = query.filter(Client.company_id == company_id)

    # Keep this intentionally broad and do the exact bucket math in Python so
    # expired contracts remain visible regardless of how long ago they expired.
    rows = query.order_by(ClientContract.end_date.asc()).all()
    alerts: list[ContractRenewalAlert] = []
    for contract in rows:
        bucket, days = renewal_bucket(contract.end_date, today)
        if not bucket or days is None:
            continue
        meta = ALERT_BUCKETS[bucket]
        alerts.append(
            ContractRenewalAlert(
                contract=contract,
                bucket=bucket,
                label=meta["label"],
                priority=meta["priority"],
                days_to_expiry=days,
            )
        )
    return alerts


def alert_summary(company_id: int | None = None, today: date | None = None) -> dict[str, int]:
    summary = {"expired": 0, "30": 0, "60": 0, "90": 0, "total": 0}
    for alert in contract_renewal_alerts(company_id=company_id, today=today):
        summary[alert.bucket] += 1
        summary["total"] += 1
    return summary


def _contract_title(contract: ClientContract) -> str:
    try:
        return contract.get_json("meta.contract_title", f"Contract #{contract.id}")
    except Exception:
        return f"Contract #{contract.id}"


def _recipient_ids(contract: ClientContract, fallback_user_id: int | None = None) -> list[int]:
    if contract.alert_owner_id:
        return [contract.alert_owner_id]

    client = contract.client
    company_id = getattr(client, "company_id", None)
    query = User.query
    if company_id:
        query = query.filter(User.company_id == company_id)

    recipients = (
        query.join(User.role)
        .filter(User.role.has(name="Super Admin"))
        .order_by(User.id.asc())
        .all()
    )
    ids = [user.id for user in recipients]
    if not ids and fallback_user_id:
        ids = [fallback_user_id]
    return ids


def _contract_link(contract: ClientContract) -> str:
    return f"/super-admin/contracts/renew/{contract.client_id}?step=3&contract_id={contract.id}"


def _notification_exists(recipient_id: int, link_url: str, bucket: str) -> bool:
    return (
        Notification.query
        .filter(
            Notification.recipient_id == recipient_id,
            Notification.type == "contract_renewal",
            Notification.link_url == link_url,
            Notification.gar_category == f"Contract Renewal:{bucket}",
        )
        .first()
        is not None
    )


def sync_contract_renewal_notifications(
    *,
    company_id: int | None = None,
    fallback_user_id: int | None = None,
    today: date | None = None,
    commit: bool = True,
) -> dict[str, int]:
    created = 0
    skipped_existing = 0
    considered = 0

    for alert in contract_renewal_alerts(company_id=company_id, today=today):
        considered += 1
        contract = alert.contract
        client = contract.client
        title = _contract_title(contract)
        link_url = _contract_link(contract)
        if alert.days_to_expiry < 0:
            timing = f"expired {abs(alert.days_to_expiry)} days ago"
        else:
            timing = f"expires in {alert.days_to_expiry} days"

        for recipient_id in _recipient_ids(contract, fallback_user_id=fallback_user_id):
            if _notification_exists(recipient_id, link_url, alert.bucket):
                skipped_existing += 1
                continue

            message = f"{client.name if client else 'Client'} contract alert: {title} {timing}."
            notification = Notification(
                recipient_id=recipient_id,
                message=message,
                type="contract_renewal",
                link_url=link_url,
                priority_level=alert.priority,
                gar_category=f"Contract Renewal:{alert.bucket}",
                is_governance_related=True,
                suggested_action="Review renewal status and update Contract Manager.",
                extracted_data={
                    "source": "contract_manager",
                    "contract_id": contract.id,
                    "client_id": contract.client_id,
                    "bucket": alert.bucket,
                    "days_to_expiry": alert.days_to_expiry,
                },
            )
            db.session.add(notification)
            created += 1

    if commit:
        db.session.commit()

    return {
        "considered": considered,
        "created": created,
        "skipped_existing": skipped_existing,
    }
