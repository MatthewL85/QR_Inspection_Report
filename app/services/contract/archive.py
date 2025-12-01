from datetime import datetime, timezone
from app.extensions import db
from app.services.contract.contract_audits import create_contract_audit  # your existing audit helper

def archive_contract(contract, user, reason: str | None = None):
    # Idempotent
    if contract.is_archived:
        return contract

    # Flip status to ARCHIVED if you use statuses
    try:
        if hasattr(contract, "status"):
            contract.status = "ARCHIVED"
    except Exception:
        pass

    contract.archived_at = datetime.now(timezone.utc)
    contract.archived_by_id = getattr(user, "id", None)
    contract.archived_reason = (reason or "Archived via UI").strip()[:255]

    # Audit
    create_contract_audit(
        contract_id=contract.id,
        action="ARCHIVE",
        payload={
            "reason": contract.archived_reason,
            "by_user_id": contract.archived_by_id,
        }
    )
    db.session.add(contract)
    db.session.commit()
    return contract
