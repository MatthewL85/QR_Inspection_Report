from flask import redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from .. import settings_bp
from ._common import get_contact_or_404

@settings_bp.post("/emergency/<int:contact_id>/delete")
@login_required
def emergency_delete(contact_id):
    ec = get_contact_or_404(contact_id)
    db.session.delete(ec)
    db.session.commit()
    flash("Emergency contact deleted.", "success")
    return redirect(url_for("settings.emergency_index"))
