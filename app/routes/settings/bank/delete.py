# app/routes/settings/bank/delete.py
from flask import redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from .. import settings_bp
from ._common import get_account_or_404

@settings_bp.post("/bank/<int:account_id>/delete")
@login_required
def bank_delete(account_id):
    acc = get_account_or_404(account_id)
    db.session.delete(acc)
    db.session.commit()
    flash("Bank account deleted.", "success")
    return redirect(url_for("settings.bank_index"))
