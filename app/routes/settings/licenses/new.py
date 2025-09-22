from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.forms.company.company_license import CompanyLicenseForm
from app.models.onboarding import CompanyLicense
from .. import settings_bp
from ._common import current_company_id, clear_other_defaults

@settings_bp.route("/licenses/new", methods=["GET","POST"])
@login_required
def licenses_new():
    form = CompanyLicenseForm()
    if form.validate_on_submit():
        lic = CompanyLicense(
            company_id=current_company_id(),
            regulator_name=form.regulator_name.data,
            license_type=form.license_type.data,
            license_number=form.license_number.data,
            country=form.country.data,
            region=form.region.data or None,
            city=form.city.data or None,
            status=form.status.data,
            valid_from=form.valid_from.data,
            expiry_date=form.expiry_date.data,
            is_default=bool(form.is_default.data),
            active=bool(form.active.data),
            scope_json=form.scope_json.data or None,
            document_path=form.document_path.data or None,
        )
        db.session.add(lic)
        db.session.flush()
        if lic.is_default:
            clear_other_defaults(country=lic.country, region=lic.region, exclude_id=lic.id)
        db.session.commit()
        flash("Licence created.", "success")
        return redirect(url_for("settings.licenses_index"))
    return render_template("settings/licenses/form.html", form=form, title="New Licence")
