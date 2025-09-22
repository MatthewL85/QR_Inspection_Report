# app/routes/settings/bank/index.py
from flask import render_template
from flask_login import login_required
from app.models.onboarding import BankAccount
from .. import settings_bp
from ._common import current_company_id

@settings_bp.get("/bank")
@login_required
def bank_index():
    items = (BankAccount.query
             .filter(BankAccount.owner_type == "company",
                     BankAccount.owner_id == current_company_id())
             .order_by(BankAccount.is_default.desc(),
                       BankAccount.nickname.asc().nullsfirst())
             .all())
    return render_template("settings/bank_accounts/index.html", items=items)
