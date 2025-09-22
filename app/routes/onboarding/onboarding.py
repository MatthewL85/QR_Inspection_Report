# app/routes/onboarding/onboarding.py
from __future__ import annotations

import os
from datetime import datetime
from werkzeug.utils import secure_filename
from sqlalchemy.exc import SQLAlchemyError

from flask import (
    render_template, request, redirect, url_for,
    flash, current_app, session
)
from flask_login import login_required, current_user

from app.routes.onboarding import onboarding_bp
from app.extensions import db
from app.decorators import super_admin_required

# Adjust if your model lives elsewhere
from app.models.onboarding.company import Company

try:
    from app.forms.company.company_onboarding_form import CompanyOnboardingForm
except Exception:
    CompanyOnboardingForm = None

SUPPORTED_TYPES = {"management", "contractor", "omc"}


# ---------- helpers ----------
def _attach_company_to_user(company: Company) -> None:
    """Best-effort link so Settings pages can find it."""
    # Link on the company if the column exists
    for fld in ("created_by_id", "owner_user_id", "user_id"):
        if hasattr(company, fld) and getattr(company, fld) in (None, 0):
            setattr(company, fld, getattr(current_user, "id", None))

    # Link on the user if app expects current_user.company_id
    if hasattr(current_user, "company_id") and getattr(current_user, "company_id", None) in (None, 0):
        current_user.company_id = company.id


def _get_company_from_request_or_session() -> Company | None:
    """
    Load company by priority:
      1) ?id=<int> in query string (Review Details)
      2) session['onboarding_company_id']
      3) last company created by this user (if model supports created_by_id)
    """
    # 1) explicit query param
    qid = request.args.get("id", type=int)
    if qid:
        obj = Company.query.get(qid)
        # Optional: authorize — only allow if belongs to user (when field exists)
        if obj and (not hasattr(obj, "created_by_id") or obj.created_by_id == getattr(current_user, "id", None)):
            # refresh session context for the wizard UX
            session["onboarding_company_id"] = obj.id
            return obj

    # 2) session
    cid = session.get("onboarding_company_id")
    if cid:
        obj = Company.query.get(cid)
        if obj:
            return obj

    # 3) last created by user (nice fallback if fields exist)
    if hasattr(Company, "created_by_id"):
        obj = Company.query.filter_by(created_by_id=getattr(current_user, "id", None))\
                           .order_by(Company.id.desc()).first()
        if obj:
            session["onboarding_company_id"] = obj.id
            return obj

    return None


def _get_or_create_company(existing_id: int | None, name: str | None) -> Company:
    """Fetch by id or create a new Company (minimal), flushing to get an id."""
    if existing_id:
        found = Company.query.get(existing_id)
        if found:
            return found

    obj = Company()
    if name:
        obj.name = name.strip()
    if hasattr(obj, "created_at"):
        obj.created_at = datetime.utcnow()

    # Link to the user if such fields exist
    _attach_company_to_user(obj)

    db.session.add(obj)
    db.session.flush()  # ensure obj.id
    return obj


# ──────────────────────────────────────────────────────────────────────────────
# Step 1: Company Details (GET/POST)
# ──────────────────────────────────────────────────────────────────────────────
@onboarding_bp.route("/company", methods=["GET", "POST"], endpoint="company_get")
@super_admin_required
@login_required
def company_get():
    """
    GET: render company details (prefers ?id=..., then session)
    POST: validate + save, then redirect to branding
    """
    # 🔑 NEW: load by ?id=, then session, then fallback
    company = _get_company_from_request_or_session()
    cid = company.id if company else session.get("onboarding_company_id")

    # WTForms path (preferred)
    if CompanyOnboardingForm is not None:
        form = CompanyOnboardingForm(obj=company)

        if form.validate_on_submit():
            # Create if first time
            if not company:
                company = _get_or_create_company(None, form.name.data)

            # Assign common fields safely
            field_names = (
                "name", "registration_number", "vat_number", "tax_identifier",
                "company_type", "industry",
                "email", "phone", "website",
                "address_line1", "address_line2", "city", "state", "postal_code", "country",
                "currency", "timezone", "preferred_language",
            )
            for fname in field_names:
                if hasattr(company, fname):
                    value = getattr(form, fname).data
                    setattr(company, fname, (value or "").strip() or None)

            # validate company_type against supported list (optional)
            ctype = (getattr(company, "company_type", None) or "").strip().lower()
            if ctype and ctype not in SUPPORTED_TYPES:
                flash("Invalid company type.", "danger")
                return redirect(url_for("onboarding.company_get", id=(company.id if company else None)))

            # ensure linkage so Settings can find it
            _attach_company_to_user(company)

            db.session.commit()
            session["onboarding_company_id"] = company.id
            flash("Company details saved.", "success")
            return redirect(url_for("onboarding.branding_get"))

        # If POST but invalid, surface errors
        if request.method == "POST":
            current_app.logger.warning("Onboarding form errors: %s", dict(form.errors))
            flash("Please fix the highlighted errors.", "danger")

        return render_template("onboarding/company_details.html", form=form, company=company)

    # Fallback path (no WTForms available)
    if request.method == "POST":
        try:
            name = (request.form.get("name") or "").strip()
            if not name:
                flash("Company name is required.", "danger")
                return redirect(url_for("onboarding.company_get", id=cid))

            email = (request.form.get("email") or "").strip() or None
            phone = (request.form.get("phone") or "").strip() or None
            regno = (request.form.get("registration_number") or "").strip() or None
            vat   = (request.form.get("vat_number") or "").strip() or None
            taxid = (request.form.get("tax_identifier") or "").strip() or None
            ctype = (request.form.get("company_type") or "").strip().lower() or None
            industry = (request.form.get("industry") or "").strip() or None

            addr1 = (request.form.get("address_line1") or "").strip() or None
            addr2 = (request.form.get("address_line2") or "").strip() or None
            city  = (request.form.get("city") or "").strip() or None
            state = (request.form.get("state") or "").strip() or None
            pcode = (request.form.get("postal_code") or "").strip() or None
            country = (request.form.get("country") or "").strip() or None

            currency = (request.form.get("currency") or "").strip() or None
            tz = (request.form.get("timezone") or "").strip() or None
            lang = (request.form.get("preferred_language") or "").strip() or None

            if ctype and ctype not in SUPPORTED_TYPES:
                flash("Invalid company type.", "danger")
                return redirect(url_for("onboarding.company_get", id=cid))

            company = company or _get_or_create_company(cid, name)

            def _set(field: str, value):
                if hasattr(company, field):
                    setattr(company, field, value)

            _set("name", name)
            _set("email", email)
            _set("phone", phone)
            _set("registration_number", regno)
            _set("vat_number", vat)
            _set("tax_identifier", taxid)
            _set("company_type", ctype)
            _set("industry", industry)

            _set("address_line1", addr1)
            _set("address_line2", addr2)
            _set("city", city)
            _set("state", state)
            _set("postal_code", pcode)
            _set("country", country)

            _set("currency", currency)
            _set("timezone", tz)
            _set("preferred_language", lang)

            # ensure linkage so Settings can find it
            _attach_company_to_user(company)

            db.session.commit()
            session["onboarding_company_id"] = company.id
            flash("Company details saved.", "success")
            return redirect(url_for("onboarding.branding_get"))

        except SQLAlchemyError:
            current_app.logger.exception("Failed to save onboarding company")
            db.session.rollback()
            flash("We couldn’t save your company details. Please try again.", "danger")

    # GET render
    return render_template("onboarding/company_details.html", company=company)


# ──────────────────────────────────────────────────────────────────────────────
# Step 2: Branding
# ──────────────────────────────────────────────────────────────────────────────
@onboarding_bp.route("/branding", methods=["GET"], endpoint="branding_get")
@super_admin_required
@login_required
def branding_get():
    cid = session.get("onboarding_company_id")
    if not cid:
        # If user jumped back in with a link, try to recover context
        company = _get_company_from_request_or_session()
        if company:
            cid = company.id
            session["onboarding_company_id"] = cid
        else:
            return redirect(url_for("onboarding.company_get"))
    company = Company.query.get_or_404(cid)
    return render_template("onboarding/branding.html", company=company)


@onboarding_bp.route("/branding", methods=["POST"], endpoint="branding_post")
@super_admin_required
@login_required
def branding_post():
    cid = session.get("onboarding_company_id")
    if not cid:
        company = _get_company_from_request_or_session()
        if company:
            cid = company.id
            session["onboarding_company_id"] = cid
        else:
            return redirect(url_for("onboarding.company_get"))
    company = Company.query.get_or_404(cid)

    def _set(field: str, value):
        if hasattr(company, field):
            setattr(company, field, value)

    primary   = (request.form.get("brand_primary_color") or "").strip() or None
    secondary = (request.form.get("brand_secondary_color") or "").strip() or None
    legacy    = (request.form.get("brand_color") or "").strip() or None

    _set("brand_primary_color", primary)
    _set("brand_secondary_color", secondary)
    _set("brand_color", legacy)

    # logo upload
    file = request.files.get("logo_file")
    if file and file.filename:
        filename  = secure_filename(file.filename)
        dest_dir  = os.path.join(current_app.static_folder, "uploads", "branding")
        os.makedirs(dest_dir, exist_ok=True)
        save_path = os.path.join(dest_dir, filename)
        file.save(save_path)
        _set("logo_path", f"/static/uploads/branding/{filename}")

    # keep association intact
    _attach_company_to_user(company)

    db.session.commit()
    flash("Branding saved.", "success")
    return redirect(url_for("onboarding.done"))


# ──────────────────────────────────────────────────────────────────────────────
# Step 3: Done
# ──────────────────────────────────────────────────────────────────────────────
# app/routes/onboarding/onboarding.py

@onboarding_bp.route("/done", methods=["GET"], endpoint="done")
@super_admin_required
@login_required
def done():
    # hide banner for this session
    session["onboarding_completed_at"] = datetime.utcnow().isoformat()

    # clear wizard state
    cid = session.pop("onboarding_company_id", None)

    # optional: success toast
    flash("Onboarding complete. You can manage details anytime in Settings → Company Profile / Branding.", "success")

    # go straight to dashboard
    return redirect(url_for("super_admin.dashboard"))

