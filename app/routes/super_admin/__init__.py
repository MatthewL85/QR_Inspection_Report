# app/routes/super_admin/__init__.py

from flask import Blueprint, request, redirect, url_for
from flask_login import current_user

# 🔧 Blueprint setup for Super Admin
super_admin_bp = Blueprint(
    "super_admin",
    __name__,
    url_prefix="/super-admin",
)

# ──────────────────────────────────────────────────────────────────────────────
# Onboarding gate: ensure Super Admin completes company onboarding before
# accessing the rest of the Super Admin area.
# ──────────────────────────────────────────────────────────────────────────────
@super_admin_bp.before_app_request
def sa_onboarding_gate():
    """If a Super Admin is logged in but has no company yet, force onboarding."""
    if not current_user.is_authenticated:
        return

    # Only gate Super Admins
    role_name = getattr(current_user, "role_name", "") or ""
    if role_name.lower() != "super admin":
        return

    # Already onboarded?
    if getattr(current_user, "company_id", None):
        return

    # Safe allowlist (login, logout, auth, static, and the onboarding route itself)
    path = request.path or ""
    safe_prefixes = (
        "/auth",
        "/login",
        "/logout",
        "/static",
        "/super-admin/onboarding/company",
    )
    if any(path.startswith(p) for p in safe_prefixes):
        return

    # Redirect to onboarding wizard
    return redirect(url_for("super_admin.company_onboarding"))

# ──────────────────────────────────────────────────────────────────────────────
# Import route modules AFTER blueprint declaration to avoid circular imports.
# Each imported module must use `from app.routes.super_admin import super_admin_bp`
# and register routes via `@super_admin_bp.route(...)`.
# ──────────────────────────────────────────────────────────────────────────────

# Core dashboard and areas
from app.routes.super_admin import dashboard                 # noqa: E402,F401
from app.routes.super_admin.user import *                    # noqa: E402,F401,F403
from app.routes.super_admin.client import *                  # noqa: E402,F401,F403
# from app.routes.super_admin import reports                 # noqa: E402,F401
# from app.routes.super_admin import alerts                  # noqa: E402,F401
# from app.routes.super_admin import settings                # noqa: E402,F401
from app.routes.super_admin.compliance import *              # noqa: E402,F401,F403
from app.routes.super_admin.agms.upcoming_agms import *      # noqa: E402,F401,F403
from app.routes.super_admin.gar.gar_insights import *        # noqa: E402,F401,F403
from app.routes.super_admin.client.capex import *            # noqa: E402,F401,F403

# NEW: Contract Audits (uses the SAME super_admin_bp)
# Ensure your audits module routes look like: @super_admin_bp.route("/contracts/audits", ...)
from app.routes.super_admin.contracts.audit import *        # noqa: E402,F401,F403
