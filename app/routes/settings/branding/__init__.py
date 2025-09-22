# app/routes/settings/branding/__init__.py
from __future__ import annotations

import os
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.onboarding.company import Company
from app.routes.settings import settings_bp  # ← uses your existing blueprint


# ---------- helpers ----------
def _attach_company_to_user(company: Company) -> None:
    for fld in ("created_by_id", "owner_user_id", "user_id"):
        if hasattr(company, fld) and getattr(company, fld) in (None, 0):
            setattr(company, fld, getattr(current_user, "id", None))
    if hasattr(current_user, "company_id") and (getattr(current_user, "company_id", None) in (None, 0)):
        current_user.company_id = company.id


def _resolve_company() -> Company:
    """?id → current_user.company_id → last created by me → create minimal."""
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
        obj = (Company.query
               .filter_by(created_by_id=getattr(current_user, "id", None))
               .order_by(Company.id.desc())
               .first())
        if obj:
            return obj

    obj = Company()
    if hasattr(obj, "name") and not obj.name:
        obj.name = "New Company"
    db.session.add(obj)
    db.session.flush()
    _attach_company_to_user(obj)
    db.session.commit()
    return obj


def _apply_branding_from_request(company: Company) -> None:
    def _set(field, value):
        if hasattr(company, field):
            setattr(company, field, value)

    # colors
    primary   = (request.form.get("brand_primary_color") or "").strip() or None
    secondary = (request.form.get("brand_secondary_color") or "").strip() or None
    legacy    = (request.form.get("brand_color") or "").strip() or None
    _set("brand_primary_color", primary)
    _set("brand_secondary_color", secondary)
    _set("brand_color", legacy)

    # logo upload
    file = request.files.get("logo_file")
    if file and file.filename:
        filename = secure_filename(file.filename)
        dest_dir = os.path.join(current_app.static_folder, "uploads", "company", str(company.id))
        os.makedirs(dest_dir, exist_ok=True)
        save_path = os.path.join(dest_dir, filename)
        file.save(save_path)
        _set("logo_path", f"/static/uploads/company/{company.id}/{filename}")

    _attach_company_to_user(company)


# ---------- routes ----------
@settings_bp.route("/branding", methods=["GET"], endpoint="branding_view")
@login_required
def branding_view():
    """View-only page (like Company Profile index)."""
    company = _resolve_company()
    return render_template("settings/branding/index.html", company=company)


@settings_bp.route("/branding", methods=["POST"], endpoint="branding_save")
@login_required
def branding_save():
    """
    Back-compat POST handler for any existing single-page forms
    that still submit to /settings/branding.
    """
    company = _resolve_company()
    try:
        _apply_branding_from_request(company)
        db.session.commit()
        flash("Branding updated.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("We couldn’t save your branding. Please try again.", "danger")
    return redirect(url_for("settings.branding_view", id=company.id))


@settings_bp.route("/branding/edit", methods=["GET", "POST"], endpoint="branding_edit")
@login_required
def branding_edit():
    """New edit page for a consistent view/edit pattern."""
    company = _resolve_company()

    if request.method == "POST":
        try:
            _apply_branding_from_request(company)
            db.session.commit()
            flash("Branding updated.", "success")
            return redirect(url_for("settings.branding_view", id=company.id))
        except SQLAlchemyError:
            db.session.rollback()
            flash("We couldn’t save your branding. Please try again.", "danger")

    return render_template("settings/branding/edit.html", company=company)
