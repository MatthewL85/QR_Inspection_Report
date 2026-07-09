from __future__ import annotations

from flask import current_app, render_template, request
from flask_login import current_user, login_required

from app.models.onboarding.company import Company
from app.routes.settings import settings_bp
from app.services.core.module_settings_registry import module_settings_registry


def _resolve_company() -> Company | None:
    company_id = request.args.get("company_id", type=int) or getattr(current_user, "company_id", None)
    if company_id:
        company = Company.query.get(company_id)
        if company:
            return company
    return Company.query.order_by(Company.id.desc()).first()


@settings_bp.route("/modules", methods=["GET"], endpoint="module_settings_index")
@login_required
def module_settings_index():
    company = _resolve_company()
    modules = module_settings_registry()
    active_modules = sum(1 for item in modules if item["status"] in {"active", "foundation", "partial", "shell"})
    template_count = sum(len(item["document_template_types"]) for item in modules)
    return render_template(
        "settings/modules/index.html",
        company=company,
        modules=modules,
        active_modules=active_modules,
        template_count=template_count,
        view_functions=current_app.view_functions,
    )
