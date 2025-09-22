# app/routes/settings/profile/index.py
from flask import render_template, request, redirect, url_for, flash
from .. import settings_bp
from app.extensions import db

# ✅ use your existing form
from app.forms.company.profile import CompanyProfileForm

try:
    from app.models.company import Company
except Exception:
    Company = None  # type: ignore


def _get_or_create_company():
    if not Company:
        return None
    inst = Company.query.first()
    if not inst:
        inst = Company(name="")
        db.session.add(inst)
        db.session.commit()
    return inst


@settings_bp.route("/company-profile", methods=["GET", "POST"], endpoint="profile_view")
def company_profile_view():
    company = _get_or_create_company()
    form = CompanyProfileForm(obj=company)

    if request.method == "POST" and form.validate_on_submit() and company:
        form.populate_obj(company)   # ✅ copies all fields into your Company model
        db.session.commit()
        flash("Company profile updated.", "success")
        return redirect(url_for("settings.profile_view"))

    return render_template("settings/company_profile.html", form=form, company=company)
