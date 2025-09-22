from flask import redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from .. import settings_bp
from ._common import get_contact_or_404, clear_other_defaults

@settings_bp.post("/emergency/<int:contact_id>/make-default")
@login_required
def emergency_make_default(contact_id):
    ec = get_contact_or_404(contact_id)
    if not ec.service_type:
        flash("Cannot set default without a service type.", "warning")
        return redirect(url_for("settings.emergency_index"))
    clear_other_defaults(service_type=ec.service_type, exclude_id=ec.id)
    ec.is_default = True
    db.session.commit()
    flash(f"Default emergency contact set for service: {ec.service_type}.", "success")
    return redirect(url_for("settings.emergency_index"))
