from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.onboarding import Company
from app.forms.company.branding import CompanyBrandingForm
from app.services.files import save_company_logo
from . import settings_bp

def _company() -> Company:
    return Company.query.get_or_404(current_user.company_id)

@settings_bp.get("/branding")
@login_required
def branding_view():
    company = _company()
    form = CompanyBrandingForm(data={
        "brand_primary_color": company.brand_primary_color or company.brand_color,
        "brand_secondary_color": company.brand_secondary_color,
    })
    return render_template("settings/branding.html", form=form, company=company)

@settings_bp.post("/branding")
@login_required
def branding_save():
    company = _company()
    form = CompanyBrandingForm()
    if not form.validate_on_submit():
        flash("Please correct the highlighted errors.", "danger")
        return render_template("settings/branding.html", form=form, company=company), 400

    company.brand_primary_color = form.brand_primary_color.data or company.brand_primary_color
    company.brand_secondary_color = form.brand_secondary_color.data or company.brand_secondary_color

    # handle logo file if provided
    file = request.files.get("logo_file")
    if file and file.filename:
        try:
            rel_path = save_company_logo(company_id=company.id, file_storage=file)
            company.logo_path = rel_path  # e.g., "uploads/company/42/logo.png"
            flash("Logo uploaded.", "success")
        except Exception as e:
            flash(f"Logo upload failed: {e}", "danger")

    db.session.commit()
    flash("Branding saved.", "success")
    return redirect(url_for("settings.branding_view"))
