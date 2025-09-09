from flask import current_app
from flask.cli import with_appcontext
import click

from app import db
from app.models.contracts import ClientContract
from app.service.contract import create_contract_audit


@click.command("backfill-contract-audits")
@with_appcontext
def backfill_contract_audits():
    """
    Backfill ContractAudit entries for all existing contracts
    that have no audits yet. Marks them as 'bootstrap'.
    """
    click.echo("🔎 Checking for contracts missing audits...")

    from app.models import ContractAudit

    count = 0
    for contract in ClientContract.query.all():
        has_audits = (
            ContractAudit.query.filter_by(contract_id=contract.id).first() is not None
        )
        if not has_audits:
            # Capture current state as "after"
            after = {
                "id": contract.id,
                "name": contract.name,
                "contract_value": contract.contract_value,
                "sign_status": contract.sign_status,
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
