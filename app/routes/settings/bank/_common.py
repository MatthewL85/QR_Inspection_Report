# app/routes/settings/bank/_common.py
from flask_login import current_user
from app.models.onboarding import BankAccount

def current_company_id() -> int:
    return current_user.company_id

def get_account_or_404(account_id: int) -> BankAccount:
    return (BankAccount.query
            .filter_by(id=account_id, owner_type="company", owner_id=current_company_id())
            .first_or_404())

def clear_other_defaults(account_id: int | None = None):
    """Unset other default accounts for this owner."""
    q = (BankAccount.query
         .filter(BankAccount.owner_type == "company",
                 BankAccount.owner_id == current_company_id(),
                 BankAccount.is_default.is_(True)))
    if account_id:
        q = q.filter(BankAccount.id != account_id)
    q.update({"is_default": False})
