from flask import render_template
from flask_login import login_required
from app.models.onboarding import EmergencyContact
from .. import settings_bp
from ._common import current_company_id

@settings_bp.get("/emergency")
@login_required
def emergency_index():
    items = (EmergencyContact.query
             .filter_by(company_id=current_company_id())
             .order_by(EmergencyContact.service_type.asc(),
                       EmergencyContact.priority.asc(),
                       EmergencyContact.is_default.desc())
             .all())
    return render_template("settings/emergency_contacts/index.html", items=items)
