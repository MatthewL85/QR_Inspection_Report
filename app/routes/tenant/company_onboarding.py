# app/routes/tenant/company_onboarding.py
import os
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.routes.tenant import tenant_bp  # create a 'tenant_bp' blueprint with url_prefix='/tenant'
from app.forms.company.company_onboarding_form import CompanyOnboardingForm
from app.models import db
from app.models.company import Company
from app.config import Config  # ensure UPLOAD_FOLDER exists

@tenant_bp.route("/company-onboarding", methods=["GET", "POST"], endpoint="company_onboarding")
@login_required
def company_onboarding():
    # If already has a company, send to dashboard
    if current_user.company_id:
        return redirect(url_for("super_admin.dashboard"))

    form = CompanyOnboardingForm()

    if request.method == "POST" and form.validate_on_submit():
        # Subdomain + plan are optional here (but best practice to capture)
        subdomain = (getattr(form, "subdomain", None) and form.subdomain.data.strip().lower()) or None
        plan = (getattr(form, "plan", None) and form.plan.data) or "trial"

        # Optional logo upload
        logo_path = None
        if form.logo_path.data:
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(form.logo_path.data.filename)
            save_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            form.logo_path.data.save(save_path)
            logo_path = filename

        company = Company(
            name=form.name.data.strip(),
            registration_number=form.registration_number.data or None,
            vat_number=form.vat_number.data or None,
            tax_identifier=form.tax_identifier.data or None,
            company_type=form.company_type.data,  # "Property Management" for tenant
            industry=form.industry.data or None,

            country=form.country.data,
            region=form.region.data or None,
            currency=form.currency.data or "EUR",
            timezone=form.timezone.data or "Europe/Dublin",
            preferred_language=form.preferred_language.data or "en",

            email=form.email.data or None,
            phone=form.phone.data or None,
            website=form.website.data or None,

            address_line1=form.address_line1.data or None,
            address_line2=form.address_line2.data or None,
            city=form.city.data or None,
            state=form.state.data or None,
            postal_code=form.postal_code.data or None,

            data_protection_compliant=bool(form.data_protection_compliant.data),
            terms_agreed=bool(form.terms_agreed.data),
            consent_to_communicate=bool(form.consent_to_communicate.data),

            logo_path=logo_path,
            brand_color=form.brand_color.data or None,

            # onboarding flags (if your model has them)
            subdomain=subdomain,
            plan=plan,
            onboarding_step="completed",
            onboarding_completed=True,
            is_active=True,
        )

        db.session.add(company)
        db.session.flush()

        # link the current user to the new company
        current_user.company_id = company.id
        db.session.commit()

        flash("✅ Company onboarding complete.", "success")
        return redirect(url_for("super_admin.dashboard"))

    return render_template("tenant/company_onboarding.html", form=form)
