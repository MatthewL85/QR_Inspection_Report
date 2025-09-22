from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.forms.company.company_license import CompanyLicenseForm
from .. import settings_bp
from ._common import get_license_or_404, clear_other_defaults

@settings_bp.route("/licenses/<int:license_id>/edit", methods=["GET","POST"])
@login_required
def licenses_edit(license_id):
    lic = get_license_or_404(license_id)
    form = CompanyLicenseForm(obj=lic)
    if form.validate_on_submit():
        form.populate_obj(lic)
        if form.is_default.data:
            clear_other_defaults(country=lic.country, region=lic.region, exclude_id=lic.id)
            lic.is_default = True
        db.session.commit()
        flash("Licence updated.", "success")
        return redirect(url_for("settings.licenses_index"))
    return render_template("settings/licenses/form.html", form=form, title="Edit Licence")
