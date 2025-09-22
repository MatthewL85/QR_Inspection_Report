from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.forms.company.insurance_policy import InsurancePolicyForm
from .. import settings_bp
from ._common import get_policy_or_404, clear_other_defaults

@settings_bp.route("/insurance/<int:policy_id>/edit", methods=["GET","POST"])
@login_required
def insurance_edit(policy_id):
    p = get_policy_or_404(policy_id)
    form = InsurancePolicyForm(obj=p)
    if form.validate_on_submit():
        form.populate_obj(p)
        if form.is_default.data:
            clear_other_defaults(policy_type=p.policy_type, exclude_id=p.id)
            p.is_default = True
        db.session.commit()
        flash("Insurance policy updated.", "success")
        return redirect(url_for("settings.insurance_index"))
    return render_template("settings/insurance_policies/form.html", form=form, title="Edit Insurance Policy")
