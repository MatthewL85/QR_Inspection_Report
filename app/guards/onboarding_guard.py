# app/guards/onboarding_guard.py
from flask import request, redirect, url_for
from flask_login import current_user
from werkzeug.routing import BuildError

TENANT_ROLE_NAMES = {
    "Super Admin",
    "Admin",
    "Property Manager",
    "Financial Controller",
}

# Endpoints that must remain accessible even if the tenant hasn't onboarded yet
ALLOWED_ENDPOINTS = {
    # auth
    "auth.login",
    "auth.logout",
    "auth.signup",
    "auth.forgot_password",
    "auth.reset_password",

    # onboarding flow itself
    "tenant.company_onboarding",
    "tenant.company_onboarding_upload_logo",
    "tenant.company_onboarding_finish",
}

# Blueprints to always allow (e.g., static assets)
ALLOWED_BLUEPRINTS = {
    "static",
}

def _is_allowed_endpoint(endpoint: str | None) -> bool:
    if not endpoint:
        return False
    if endpoint in ALLOWED_ENDPOINTS:
        return True
    # allow everything under allowed blueprints
    bp = endpoint.split(".", 1)[0]
    return bp in ALLOWED_BLUEPRINTS

def _needs_tenant_onboarding(user) -> bool:
    """
    Returns True if the user must be redirected to tenant onboarding.
    Conditions:
      - user is in a tenant role (management agency roles)
      - (no company yet) OR (company exists but onboarding not complete)
    """
    role_name = (getattr(user.role, "name", None) or "").strip()
    if role_name not in TENANT_ROLE_NAMES:
        return False  # e.g., Contractor, Resident, etc.

    company = getattr(user, "company", None)
    if not company:
        return True

    # If your model has these flags, use them. Otherwise, default to False.
    onboarding_completed = bool(getattr(company, "onboarding_completed", False))
    return not onboarding_completed


def register_onboarding_guard(app):
    @app.before_request
    def _tenant_onboarding_gate():
        # only run for authenticated users
        if not current_user.is_authenticated:
            return None

        # let allowed routes/assets pass
        if _is_allowed_endpoint(request.endpoint):
            return None

        # require onboarding for tenant roles
        if _needs_tenant_onboarding(current_user):
            try:
                return redirect(url_for("tenant.company_onboarding"))
            except BuildError:
                # If the onboarding route isn't registered yet, just allow.
                # (prevents hard crashes during local dev)
                return None

        return None
