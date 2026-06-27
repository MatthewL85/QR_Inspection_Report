from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.decorators.role import super_admin_required
from app.extensions import db
from app.models.core.organisation_connection import (
    ModuleSubscription,
    OrganisationConnection,
    OrganisationConnectionInvite,
)
from app.models.onboarding.company import Company
from app.routes.super_admin import super_admin_bp
from app.services.core.module_registry import module_contracts
from app.services.core.organisation_identity import (
    accept_organisation_connection_invite,
    create_organisation_connection_invite,
    enable_module_subscription,
)


def _current_company() -> Company | None:
    company_id = getattr(current_user, "company_id", None)
    return Company.query.get(company_id) if company_id else None


def _parse_company_id(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@super_admin_bp.route("/organisation-connections", endpoint="organisation_connections")
@login_required
@super_admin_required
def organisation_connections():
    company = _current_company()
    companies = Company.query.order_by(Company.name.asc()).all()

    subscriptions = []
    pending_invites = []
    active_connections = []
    received_invites = []

    if company:
        subscriptions = (
            ModuleSubscription.query
            .filter(ModuleSubscription.company_id == company.id)
            .order_by(ModuleSubscription.module_key.asc())
            .all()
        )
        pending_invites = (
            OrganisationConnectionInvite.query
            .filter(
                OrganisationConnectionInvite.source_company_id == company.id,
                OrganisationConnectionInvite.status == "pending",
            )
            .order_by(OrganisationConnectionInvite.created_at.desc())
            .all()
        )
        received_invites = (
            OrganisationConnectionInvite.query
            .filter(
                OrganisationConnectionInvite.target_company_id == company.id,
                OrganisationConnectionInvite.status == "pending",
            )
            .order_by(OrganisationConnectionInvite.created_at.desc())
            .all()
        )
        active_connections = (
            OrganisationConnection.query
            .filter(
                OrganisationConnection.status == "active",
                or_(
                    OrganisationConnection.source_company_id == company.id,
                    OrganisationConnection.target_company_id == company.id,
                ),
            )
            .order_by(OrganisationConnection.created_at.desc())
            .all()
        )

    available_modules = [
        contract for contract in module_contracts()
        if contract.key != "core"
    ]

    return render_template(
        "super_admin/organisation_connections.html",
        company=company,
        companies=companies,
        available_modules=available_modules,
        subscriptions=subscriptions,
        pending_invites=pending_invites,
        received_invites=received_invites,
        active_connections=active_connections,
    )


@super_admin_bp.post("/organisation-connections/modules", endpoint="enable_organisation_module")
@login_required
@super_admin_required
def enable_organisation_module():
    company = _current_company()
    target_company_id = _parse_company_id(request.form.get("company_id")) or (company.id if company else None)
    module_key = (request.form.get("module_key") or "").strip()
    plan = (request.form.get("plan") or "").strip() or None

    if not target_company_id or not module_key:
        flash("Select an organisation and module before enabling access.", "warning")
        return redirect(url_for("super_admin.organisation_connections"))

    try:
        enable_module_subscription(
            company_id=target_company_id,
            module_key=module_key,
            plan=plan,
            created_by_user_id=getattr(current_user, "id", None),
        )
        db.session.commit()
        flash("Module access enabled for this organisation.", "success")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "danger")

    return redirect(url_for("super_admin.organisation_connections"))


@super_admin_bp.post("/organisation-connections/invites", endpoint="create_organisation_connection_invite")
@login_required
@super_admin_required
def create_connection_invite():
    company = _current_company()
    source_company_id = _parse_company_id(request.form.get("source_company_id")) or (company.id if company else None)
    target_company_id = _parse_company_id(request.form.get("target_company_id"))
    target_email = (request.form.get("target_email") or "").strip() or None
    connection_type = (request.form.get("connection_type") or "management_contractor").strip()
    allowed_modules = request.form.getlist("allowed_modules") or ["works", "contractor", "gar_ai"]

    if not source_company_id:
        flash("A source organisation is required before creating a connection invite.", "warning")
        return redirect(url_for("super_admin.organisation_connections"))

    if target_company_id == source_company_id:
        flash("An organisation cannot invite itself.", "warning")
        return redirect(url_for("super_admin.organisation_connections"))

    try:
        invite = create_organisation_connection_invite(
            source_company_id=source_company_id,
            target_company_id=target_company_id,
            target_email=target_email,
            connection_type=connection_type,
            allowed_modules=allowed_modules,
            created_by_user_id=getattr(current_user, "id", None),
        )
        db.session.commit()
        flash(f"Connection invite created. Code: {invite.invite_code}", "success")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "danger")

    return redirect(url_for("super_admin.organisation_connections"))


@super_admin_bp.post("/organisation-connections/accept", endpoint="accept_organisation_connection_invite")
@login_required
@super_admin_required
def accept_connection_invite():
    company = _current_company()
    invite_code = (request.form.get("invite_code") or "").strip().upper()
    accepting_company_id = _parse_company_id(request.form.get("accepting_company_id")) or (company.id if company else None)

    if not invite_code or not accepting_company_id:
        flash("Enter the invite code and accepting organisation.", "warning")
        return redirect(url_for("super_admin.organisation_connections"))

    try:
        accept_organisation_connection_invite(
            invite_code=invite_code,
            accepting_company_id=accepting_company_id,
            accepted_by_user_id=getattr(current_user, "id", None),
        )
        db.session.commit()
        flash("Organisation connection accepted.", "success")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "danger")

    return redirect(url_for("super_admin.organisation_connections"))
