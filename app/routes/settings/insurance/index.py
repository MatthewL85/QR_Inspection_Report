from datetime import date, timedelta
from flask import render_template
from flask_login import login_required
from app.models.onboarding import InsurancePolicy
from .. import settings_bp
from ._common import current_company_id

@settings_bp.get("/insurance")
@login_required
def insurance_index():
    items = (InsurancePolicy.query
             .filter_by(company_id=current_company_id())
             .order_by(InsurancePolicy.policy_type.asc(),
                       InsurancePolicy.is_default.desc(),
                       InsurancePolicy.expiry_date.asc().nullsfirst())
             .all())
    today = date.today()
    soon = today + timedelta(days=30)
    return render_template("settings/insurance_policies/index.html", items=items, today=today, soon=soon)
