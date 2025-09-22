# app/routes/settings/bank/default.py
from flask import redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from .. import settings_bp
from ._common import get_account_or_404, clear_other_defaults

@settings_bp.post("/bank/<int:account_id>/make-default")
@login_required
def bank_make_default(account_id):
    acc = get_account_or_404(account_id)
    clear_other_defaults(account_id=acc.id)
    acc.is_default = True
    db.session.commit()
    flash("Default bank account set.", "success")
    return redirect(url_for("settings.bank_index"))
