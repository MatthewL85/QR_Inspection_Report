# app/routes/settings/profile/__init__.py
from __future__ import annotations
from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.onboarding.company import Company
from app.routes.settings import settings_bp  # use existing blueprint

# Optional WTForms support (use if you have it, otherwise fallback to manual)
try:
    from app.forms.company.company_settings_form import SettingsCompanyProfileForm
except Exception:  # pragma: no cover
    SettingsCompanyProfileForm = None


# ---------- helpers ----------
PROFILE_FIELDS = (
    "name", "registration_number", "vat_number", "tax_identifier",
    "company_type", "industry",
    "email", "phone", "website",
    "address_line1", "address_line2", "city", "state", "postal_code", "country",
    "currency", "timezone", "preferred_language",
)

def _attach_company_to_user(company: Company) -> None:
    # Link company -> user (best effort, only if fields exist)
    for fld in ("created_by_id", "owner_user_id", "user_id"):
        if hasattr(company, fld) and getattr(company, fld) in (None, 0):
            setattr(company, fld, getattr(current_user, "id", None))
    # Link user -> company (if your user model has company_id)
    if hasattr(current_user, "company_id") and getattr(current_user, "company_id", None) in (None, 0):
        current_user.company_id = company.id

def _resolve_company() -> Company:
    """Order: ?id → current_user.company_id → last created by me → create minimal."""
    qid = request.args.get("id", type=int)
    if qid:
        obj = Company.query.get(qid)
        if obj:
            return obj

    if hasattr(current_user, "company_id") and current_user.company_id:
        obj = Company.query.get(current_user.company_id)
        if obj:
            return obj

    if hasattr(Company, "created_by_id"):
        obj = Company.query.filter_by(created_by_id=getattr(current_user, "id", None))\
                           .order_by(Company.id.desc()).first()
        if obj:
            return obj

    # create minimal so page is never empty
    obj = Company()
    if hasattr(obj, "name") and not obj.name:
        obj.name = "New Company"
    if hasattr(obj, "created_at"):
        obj.created_at = datetime.utcnow()
    db.session.add(obj)
    db.session.flush()
    _attach_company_to_user(obj)
    db.session.commit()
    return obj


# ---------- routes ----------
@settings_bp.route("/company-profile", methods=["GET"], endpoint="profile_index")
@login_required
def profile_index():
    company = _resolve_company()
    return render_template("settings/company_profile/index.html", company=company)


@settings_bp.route("/company-profile/edit", methods=["GET", "POST"], endpoint="profile_edit")
@login_required
def profile_edit():
    company = _resolve_company()

    # WTForms path
    if SettingsCompanyProfileForm is not None:
        form = SettingsCompanyProfileForm(obj=company)
        if form.validate_on_submit():
            for f in PROFILE_FIELDS:
                if hasattr(company, f):
                    setattr(company, f, (getattr(form, f).data or "").strip() or None)
            _attach_company_to_user(company)
            db.session.commit()
            flash("Company profile updated.", "success")
            return redirect(url_for("settings.profile_index", id=company.id))

        if request.method == "POST":
            current_app.logger.warning("Company profile form errors: %s", dict(form.errors))
            flash("Please fix the highlighted errors.", "danger")

        return render_template("settings/company_profile/edit.html", form=form, company=company)

    # Manual path (no WTForms)
    if request.method == "POST":
        try:
            def g(name): return (request.form.get(name) or "").strip() or None
            for f in PROFILE_FIELDS:
                if hasattr(company, f):
                    setattr(company, f, g(f))
            _attach_company_to_user(company)
            db.session.commit()
            flash("Company profile updated.", "success")
            return redirect(url_for("settings.profile_index", id=company.id))
        except SQLAlchemyError:
            db.session.rollback()
            flash("We couldn’t save your company profile. Please try again.", "danger")

    return render_template("settings/company_profile/edit.html", company=company)
