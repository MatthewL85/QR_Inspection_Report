from flask.cli import with_appcontext
import click

from app import db
from app.models.contracts import ClientContract
# ⬇️ import directly from the module that actually defines it
from app.services.contract.contract_audits import create_contract_audit


@click.command("backfill-contract-audits")
@with_appcontext
def backfill_contract_audits():
    """Backfill ContractAudit entries for all existing contracts that have no audits yet."""
    click.echo("🔎 Checking for contracts missing audits...")

    from app.models import ContractAudit  # local import to avoid startup circulars

    count = 0
    for contract in ClientContract.query.all():
        if ContractAudit.query.filter_by(contract_id=contract.id).first():
            continue

        after = {
            "id": contract.id,
            "name": getattr(contract, "name", None),
            "contract_value": getattr(contract, "contract_value", None),
            "sign_status": getattr(contract, "sign_status", None),
        }

        create_contract_audit(
            db.session,
            contract_id=contract.id,
            action="bootstrap",
            before=None,
            after=after,
            notes="Baseline snapshot backfilled",
            actor_id=None,
        )
        count += 1

    db.session.commit()
    click.echo(f"✅ Backfilled {count} contracts with bootstrap audits.")
