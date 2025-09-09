from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.company import Company

onboarding_bp = Blueprint("onboarding_bp", __name__, url_prefix="/onboarding")

TENANT_ROLE_NAMES = {"Super Admin", "Admin", "Property Manager", "Financial Controller"}

def _ensure_tenant_user():
    role_name = (getattr(current_user.role, "name", None) or "").strip()
    return role_name in TENANT_ROLE_NAMES

@onboarding_bp.route("/", methods=["GET"])
@login_required
def company_onboarding():
    """Landing page for onboarding (Step wizard, etc.)."""
    if not _ensure_tenant_user():
        flash("Onboarding is only available for management agencies.", "warning")
        return redirect(url_for("super_admin.dashboard"))

    company = current_user.company
    if not company:
        # If you created a placeholder company during signup, this shouldn't happen.
        flash("Please create your company to begin onboarding.", "warning")
        return redirect(url_for("super_admin.dashboard"))

    return render_template("onboarding/company_onboarding.html", company=company)

@onboarding_bp.post("/save-step")
@login_required
def save_step():
    """Persist fields for the current step; does NOT complete onboarding."""
    if not _ensure_tenant_user():
        flash("Onboarding is only available for management agencies.", "warning")
        return redirect(url_for("super_admin.dashboard"))

    company: Company = current_user.company
    if not company:
        flash("Company not found.", "danger")
        return redirect(url_for("onboarding_bp.company_onboarding"))

    # Example fields you might save from the step:
    company.name = request.form.get("company_name", company.name)
    company.address_line1 = request.form.get("address_line1", company.address_line1)
    company.city = request.form.get("city", company.city)
    company.country = request.form.get("country", company.country)
    company.subdomain = request.form.get("subdomain", company.subdomain)  # if you added this column
    company.plan = request.form.get("plan", company.plan)                  # if you added this column

    # Track progress (optional)
    company.onboarding_step = request.form.get("next_step") or company.onboarding_step

    db.session.commit()
    flash("Onboarding step saved.", "success")
    return redirect(url_for("onboarding_bp.company_onboarding"))

@onboarding_bp.post("/finish")
@login_required
def finish_onboarding():
    """Mark onboarding as complete and send the user to their dashboard."""
    if not _ensure_tenant_user():
        flash("Onboarding is only available for management agencies.", "warning")
        return redirect(url_for("super_admin.dashboard"))

    company: Company = current_user.company
    if not company:
        flash("Company not found.", "danger")
        return redirect(url_for("onboarding_bp.company_onboarding"))

    company.onboarding_completed = True
    company.onboarding_step = None  # or "done"
    company.is_active = True        # optional: activate tenant on finish
    db.session.commit()

    flash("🎉 Onboarding complete! Welcome to LogixPM.", "success")
    return redirect(url_for("super_admin.dashboard"))
