from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.forms.company.insurance_policy import InsurancePolicyForm
from app.models.onboarding import InsurancePolicy
from .. import settings_bp
from ._common import current_company_id, clear_other_defaults

@settings_bp.route("/insurance/new", methods=["GET","POST"])
@login_required
def insurance_new():
    form = InsurancePolicyForm()
    if form.validate_on_submit():
        p = InsurancePolicy(
            company_id=current_company_id(),
            policy_type=form.policy_type.data,
            provider=form.provider.data,
            policy_number=form.policy_number.data,
            coverage_amount=form.coverage_amount.data,
            currency=form.currency.data,
            start_date=form.start_date.data,
            expiry_date=form.expiry_date.data,
            is_default=bool(form.is_default.data),
            active=bool(form.active.data),
            document_path=form.document_path.data or None,
        )
        db.session.add(p)
        db.session.flush()
        if p.is_default:
            clear_other_defaults(policy_type=p.policy_type, exclude_id=p.id)
        db.session.commit()
        flash("Insurance policy created.", "success")
        return redirect(url_for("settings.insurance_index"))
    return render_template("settings/insurance_policies/form.html", form=form, title="New Insurance Policy")
