# app/routes/settings/profile/edit.py
from __future__ import annotations

from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.routes.settings import settings_bp
from ._common import resolve_company_for_settings, attach_company_to_user, PROFILE_FIELDS

# Optional WTForms support. If you have a settings form, this will be used automatically.
try:
    from app.forms.company.company_settings_form import SettingsCompanyProfileForm
except Exception:  # pragma: no cover
    SettingsCompanyProfileForm = None


@settings_bp.route("/company-profile/edit", methods=["GET", "POST"], endpoint="profile_edit")
@login_required
def profile_edit():
    company = resolve_company_for_settings()

    # WTForms path -------------------------------------------------------------
    if SettingsCompanyProfileForm is not None:
        form = SettingsCompanyProfileForm(obj=company)

        if form.validate_on_submit():
            for f in PROFILE_FIELDS:
                if hasattr(company, f):
                    setattr(company, f, (getattr(form, f).data or "").strip() or None)

            attach_company_to_user(company)
            db.session.commit()
            flash("Company profile updated.", "success")
            return redirect(url_for("settings.profile_index", id=company.id))

        if request.method == "POST":
            current_app.logger.warning("Company profile form errors: %s", dict(form.errors))
            flash("Please fix the highlighted errors.", "danger")

        return render_template("settings/company_profile/edit.html", form=form, company=company)

    # No WTForms → manual path ------------------------------------------------
    if request.method == "POST":
        try:
            def g(name): return (request.form.get(name) or "").strip() or None

            for f in PROFILE_FIELDS:
                if hasattr(company, f):
                    setattr(company, f, g(f))

            attach_company_to_user(company)
            db.session.commit()
            flash("Company profile updated.", "success")
            return redirect(url_for("settings.profile_index", id=company.id))
        except SQLAlchemyError:
            db.session.rollback()
            flash("We couldn’t save your company profile. Please try again.", "danger")

    return render_template("settings/company_profile/edit.html", company=company)
