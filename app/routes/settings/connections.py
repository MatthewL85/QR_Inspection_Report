from __future__ import annotations

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models.core.organisation_connection import ModuleSubscription
from app.models.onboarding.company import Company
from app.routes.settings import settings_bp
from app.services.core.module_connections import module_connection_context
from app.services.core.module_registry import module_contracts
from app.services.core.module_settings_registry import can_view_module_settings_centre
from app.services.core.organisation_identity import (
    accept_organisation_connection_invite,
    create_organisation_connection_invite,
    enable_module_subscription,
)


def _resolve_company() -> Company | None:
    company_id = request.args.get("company_id", type=int) or getattr(current_user, "company_id", None)
    if company_id:
        company = Company.query.get(company_id)
        if company:
            return company
    return Company.query.order_by(Company.id.desc()).first()


def _redirect(company: Company | None):
    if company:
        return redirect(url_for("settings.connections_index", company_id=company.id))
    return redirect(url_for("settings.connections_index"))


@settings_bp.route("/connections", methods=["GET", "POST"], endpoint="connections_index")
@login_required
def connections_index():
    if not can_view_module_settings_centre(current_user):
        abort(403)

    company = _resolve_company()
    if not company:
        flash("Create or select an organisation before managing connections.", "warning")
        return redirect(url_for("settings.profile_index"))

    if request.method == "POST":
        settings_action = (request.form.get("settings_action") or "").strip()

        if settings_action == "enable_module_subscription":
            module_key = (request.form.get("module_key") or "").strip()
            plan = (request.form.get("plan") or "").strip() or None
            if not module_key:
                flash("Select a module before enabling access.", "warning")
                return _redirect(company)
            try:
                enable_module_subscription(
                    company_id=company.id,
                    module_key=module_key,
                    plan=plan,
                    created_by_user_id=getattr(current_user, "id", None),
                )
                db.session.commit()
                flash("Module access enabled for this organisation.", "success")
            except ValueError as exc:
                db.session.rollback()
                flash(str(exc), "danger")
            return _redirect(company)

        if settings_action == "create_connection_invite":
            target_email = (request.form.get("target_email") or "").strip() or None
            try:
                invite = create_organisation_connection_invite(
                    source_company_id=company.id,
                    target_email=target_email,
                    connection_type="management_contractor",
                    allowed_modules=["works", "contractor", "gar_ai"],
                    created_by_user_id=getattr(current_user, "id", None),
                    notes="Created from the Settings Centre connections page.",
                )
                db.session.commit()
                flash(f"Connection code created: {invite.invite_code}", "success")
            except ValueError as exc:
                db.session.rollback()
                flash(str(exc), "danger")
            return _redirect(company)

        if settings_action == "accept_connection_invite":
            invite_code = (request.form.get("invite_code") or "").strip().upper()
            if not invite_code:
                flash("Enter the connection code before connecting organisations.", "warning")
                return _redirect(company)
            try:
                accept_organisation_connection_invite(
                    invite_code=invite_code,
                    accepting_company_id=company.id,
                    accepted_by_user_id=getattr(current_user, "id", None),
                )
                db.session.commit()
                flash("Organisation connection accepted.", "success")
            except ValueError as exc:
                db.session.rollback()
                flash(str(exc), "danger")
            return _redirect(company)

        flash("Choose a connection action before saving.", "warning")
        return _redirect(company)

    subscriptions = {
        subscription.module_key: subscription
        for subscription in ModuleSubscription.query.filter_by(company_id=company.id).all()
    }
    available_modules = [contract for contract in module_contracts() if contract.key != "core"]
    return render_template(
        "settings/connections/index.html",
        company=company,
        available_modules=available_modules,
        subscriptions=subscriptions,
        connection_context=module_connection_context(company, module_key="settings_centre"),
    )
