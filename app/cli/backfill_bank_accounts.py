# app/cli/backfill_bank_accounts.py
from flask import current_app
from app.extensions import db
from app.models.onboarding import BankAccount

def backfill_bank_accounts():
    fixed = 0
    for ba in BankAccount.query.filter(BankAccount.owner_id == 0).all():
        if ba.company_id:
            ba.owner_type = 'company'
            ba.owner_id = ba.company_id
            fixed += 1
    db.session.commit()
    current_app.logger.info("Backfilled %s bank accounts", fixed)
