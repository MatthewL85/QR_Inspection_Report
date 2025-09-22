from flask import render_template
from flask_login import login_required
from app.models.onboarding import CompanyLicense
from .. import settings_bp
from ._common import current_company_id

@settings_bp.get("/licenses")
@login_required
def licenses_index():
    items = (CompanyLicense.query
             .filter_by(company_id=current_company_id())
             .order_by(CompanyLicense.country.asc(),
                       CompanyLicense.region.asc().nullsfirst(),
                       CompanyLicense.is_default.desc())
             .all())
    return render_template("settings/licenses/index.html", items=items)
