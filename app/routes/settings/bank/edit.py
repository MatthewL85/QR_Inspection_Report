# app/routes/settings/bank/edit.py
from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.forms.company.bank_account import BankAccountForm
from .. import settings_bp
from ._common import get_account_or_404, clear_other_defaults

@settings_bp.route("/bank/<int:account_id>/edit", methods=["GET", "POST"])
@login_required
def bank_edit(account_id):
    acc = get_account_or_404(account_id)
    form = BankAccountForm(obj=acc)
    if form.validate_on_submit():
        form.populate_obj(acc)
        acc.iban = (acc.iban or "").replace(" ", "") or None
        if form.is_default.data:
            clear_other_defaults(account_id=acc.id)
            acc.is_default = True
        db.session.commit()
        flash("Bank account updated.", "success")
        return redirect(url_for("settings.bank_index"))
    return render_template("settings/bank_accounts/form.html", form=form, title="Edit Bank Account")
