from flask import redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from .. import settings_bp
from ._common import get_policy_or_404

@settings_bp.post("/insurance/<int:policy_id>/delete")
@login_required
def insurance_delete(policy_id):
    p = get_policy_or_404(policy_id)
    db.session.delete(p)
    db.session.commit()
    flash("Insurance policy deleted.", "success")
    return redirect(url_for("settings.insurance_index"))
