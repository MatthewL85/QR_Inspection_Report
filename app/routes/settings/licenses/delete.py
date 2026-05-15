from flask import redirect, url_for, flash
from flask_login import login_required

from app.extensions import db
from .. import settings_bp
from ._common import get_license_or_404


@settings_bp.post("/licenses/<int:license_id>/delete")
@login_required
def licenses_delete(license_id):
    license_record = get_license_or_404(license_id)
    db.session.delete(license_record)
    db.session.commit()
    flash("Licence deleted.", "success")
    return redirect(url_for("settings.licenses_index"))
