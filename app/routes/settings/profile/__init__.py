# app/routes/settings/profile/__init__.py
from __future__ import annotations
from datetime import datetime
from types import SimpleNamespace

from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.onboarding.company import Company
from app.routes.settings import settings_bp  # use existing blueprint
from app.services.core.company_setup_readiness import build_company_setup_readiness
from app.services.core.document_template_service import document_template_catalog

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


def _save_work_order_prefix(company: Company) -> bool:
    raw_prefix = (request.form.get("work_order_prefix") or "").strip()
    prefix = Company._normalise_work_order_prefix(raw_prefix)

    if raw_prefix and len(prefix) < 2:
        flash("Work order prefix must contain at least 2 letters or numbers.", "danger")
        return False

    if prefix:
        duplicate = Company.query.filter(
            Company.work_order_prefix == prefix,
            Company.id != company.id,
        ).first()
        if duplicate:
            flash("That work order prefix is already in use by another organisation.", "danger")
            return False

    company.work_order_prefix = prefix or None
    return True

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
    try:
        readiness = build_company_setup_readiness(company)
    except Exception:
        current_app.logger.exception(
            "Company setup readiness failed for company_id=%s",
            getattr(company, "id", None),
        )
        readiness = SimpleNamespace(
            organisation_uid=getattr(company, "organisation_uid", None) or "-",
            enabled_module_count=0,
            active_connection_count=0,
            enabled_module_names=[],
            has_connections=False,
            modules=[],
        )

    try:
        document_templates = document_template_catalog(company.id)
    except Exception:
        current_app.logger.exception(
            "Document template catalog failed for company_id=%s",
            getattr(company, "id", None),
        )
        document_templates = []
    db.session.commit()

    return render_template(
        "settings/company_profile/index.html",
        company=company,
        readiness=readiness,
        document_templates=document_templates,
    )


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
            if not _save_work_order_prefix(company):
                return render_template("settings/company_profile/edit.html", form=form, company=company)
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
            if not _save_work_order_prefix(company):
                return render_template("settings/company_profile/edit.html", company=company)
            _attach_company_to_user(company)
            db.session.commit()
            flash("Company profile updated.", "success")
            return redirect(url_for("settings.profile_index", id=company.id))
        except SQLAlchemyError:
            db.session.rollback()
            flash("We couldn’t save your company profile. Please try again.", "danger")

    return render_template("settings/company_profile/edit.html", company=company)
