from __future__ import annotations
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.routes.super_admin import super_admin_bp
from app.decorators import super_admin_required
from app.extensions import db
from app.models.org.company_settings import CompanySettings
from app.forms.settings import CompanyProfileForm, BrandingThemeForm

@super_admin_bp.route("/settings/company-profile", endpoint="settings_company_profile")
@super_admin_required
@login_required
def company_profile():
    settings = CompanySettings.get_or_create()
    form = CompanyProfileForm(obj=settings)
    return render_template("super_admin/settings/company_profile.html", form=form)

@super_admin_bp.route("/settings/company-profile", methods=["POST"], endpoint="settings_company_profile_post")
@super_admin_required
@login_required
def company_profile_post():
    settings = CompanySettings.get_or_create()
    form = CompanyProfileForm()
    if form.validate_on_submit():
        form.populate_obj(settings)
        db.session.commit()
        flash("Company profile saved.", "success")
        return redirect(url_for("super_admin.settings_company_profile"))
    return render_template("super_admin/settings/company_profile.html", form=form)