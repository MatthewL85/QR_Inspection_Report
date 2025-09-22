from typing import Optional
from app.extensions import db
from app.models.onboarding import BankAccount

def get_default_bank_account(owner_type: str, owner_id: int) -> Optional[BankAccount]:
    return (BankAccount.query
            .filter_by(owner_type=owner_type, owner_id=owner_id, is_default=True, active=True)
            .first())

def set_default_bank_account(ba: BankAccount) -> None:
    (BankAccount.query
        .filter_by(owner_type=ba.owner_type, owner_id=ba.owner_id, is_default=True)
        .update({BankAccount.is_default: False}))
    ba.is_default = True
    db.session.commit()

def build_bank_block(owner_type: str, owner_id: int):
    bank = get_default_bank_account(owner_type, owner_id)
    if not bank:
        return None
    return {
        "account_name": bank.account_name,
        "bank_name": bank.bank_name,
        "iban": bank.iban,
        "bic_swift": bank.bic_swift,
        "remittance_email": bank.remittance_email,
        "currency": bank.currency,
    }
