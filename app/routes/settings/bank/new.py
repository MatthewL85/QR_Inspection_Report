# app/routes/settings/bank/new.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.extensions import db
from app.models.onboarding import BankAccount
from app.forms.company.bank_account import BankAccountForm
from .. import settings_bp
from ._common import current_company_id, clear_other_defaults

@settings_bp.route("/bank/new", methods=["GET", "POST"])
@login_required
def bank_new():
    form = BankAccountForm()
    if form.validate_on_submit():
        acc = BankAccount(
            owner_type="company",
            owner_id=current_company_id(),
            company_id=current_company_id(),  # legacy backref (ok to keep until dropped)
            nickname=form.nickname.data,
            account_name=form.account_name.data,
            bank_name=form.bank_name.data,
            iban=(form.iban.data or "").replace(" ", "") or None,
            bic_swift=form.bic_swift.data,
            remittance_email=form.remittance_email.data,
            currency=form.currency.data,
            account_type=form.account_type.data,
            active=bool(form.active.data),
            is_default=bool(form.is_default.data),
        )
        db.session.add(acc)
        db.session.flush()
        if acc.is_default:
            clear_other_defaults(account_id=acc.id)
        db.session.commit()
        flash("Bank account created.", "success")
        return redirect(url_for("settings.bank_index"))
    return render_template("settings/bank_accounts/form.html", form=form, title="New Bank Account")
