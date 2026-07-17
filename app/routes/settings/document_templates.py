from __future__ import annotations

from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.core.document_template import CoreDocumentTemplate
from app.models.onboarding.company import Company
from app.routes.settings import settings_bp
from app.services.core.document_template_service import (
    DOCUMENT_TEMPLATE_DEFAULTS,
    document_template_catalog,
    document_template_preview_payload,
    get_document_template_payload,
)


CONTRACTOR_ROLE_NAMES = {"contractor", "admin contractor"}
COMPANY_SWITCH_ROLE_NAMES = {"super admin", "admin"}


def _role_key() -> str:
    return (getattr(current_user, "role_name", None) or "").strip().lower()


def _is_contractor_document_context() -> bool:
    return _role_key() in CONTRACTOR_ROLE_NAMES


def _can_switch_company_context() -> bool:
    return _role_key() in COMPANY_SWITCH_ROLE_NAMES


def _contractor_template_redirect(module_key: str | None = None, document_type: str | None = None, *, preview: bool = False):
    module = _normalise_key(module_key or "")
    doc_type = _normalise_key(document_type or "")
    if module == "contractor_logix" and doc_type:
        endpoint = "contractor.contractor_document_template_preview" if preview else "contractor.contractor_document_template_edit"
        return redirect(url_for(endpoint, document_type=doc_type))

    flash("Contractor Logix document templates are managed inside Contractor Logix settings.", "warning")
    return redirect(url_for("contractor.contractor_document_templates"))


def _resolve_company() -> Company | None:
    requested_company_id = request.args.get("company_id", type=int)
    current_company_id = getattr(current_user, "company_id", None)

    if _can_switch_company_context() and requested_company_id:
        company = Company.query.get(requested_company_id)
        if company:
            return company

    if current_company_id:
        company = Company.query.get(current_company_id)
        if company:
            return company

    if _can_switch_company_context():
        return Company.query.order_by(Company.id.desc()).first()

    return None


def _normalise_key(value: str) -> str:
    return (value or "").strip().lower()


def _editable_template(
    company: Company,
    module_key: str,
    document_type: str,
    persist_new: bool = False,
) -> CoreDocumentTemplate:
    template = CoreDocumentTemplate.query.filter_by(
        company_id=company.id,
        module_key=module_key,
        document_type=document_type,
        status="Active",
    ).order_by(CoreDocumentTemplate.id.desc()).first()
    if template:
        return template

    default_payload = get_document_template_payload(company.id, module_key, document_type)
    template = CoreDocumentTemplate(
        company_id=company.id,
        module_key=module_key,
        document_type=document_type,
        name=default_payload.get("name") or f"{module_key} {document_type}",
        description=default_payload.get("description"),
        status="Active",
        version_label=default_payload.get("version_label") or "v1",
        template_format=default_payload.get("template_format") or "html",
        html_body=default_payload.get("html_body"),
        terms_body=default_payload.get("terms_body"),
        footer_body=default_payload.get("footer_body"),
        logo_mode=default_payload.get("logo_mode") or "company",
        primary_brand_source=default_payload.get("primary_brand_source") or "company",
        include_signature_block=bool(default_payload.get("include_signature_block")),
        include_terms=bool(default_payload.get("include_terms", True)),
        number_prefix=default_payload.get("number_prefix"),
        sequence_padding=default_payload.get("sequence_padding") or 5,
        supported_output_formats=default_payload.get("supported_output_formats") or ["html", "pdf"],
        required_context_keys=default_payload.get("required_context_keys") or [],
        default_context=default_payload.get("default_context") or {},
        visibility_scope=default_payload.get("visibility_scope") or "company",
        created_by_id=getattr(current_user, "id", None),
        updated_by_id=getattr(current_user, "id", None),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    if persist_new:
        db.session.add(template)
    return template


@settings_bp.route("/document-templates", methods=["GET"], endpoint="document_templates_index")
@login_required
def document_templates_index():
    if _is_contractor_document_context():
        return redirect(url_for("contractor.contractor_document_templates"))

    company = _resolve_company()
    templates = document_template_catalog(company.id if company else None)
    owner_groups: dict[str, list[dict]] = {}
    for item in templates:
        owner_groups.setdefault(item["owner_module"], []).append(item)
    return render_template(
        "settings/document_templates/index.html",
        company=company,
        owner_groups=owner_groups,
        templates=templates,
    )


@settings_bp.route(
    "/document-templates/<module_key>/<document_type>/edit",
    methods=["GET", "POST"],
    endpoint="document_templates_edit",
)
@login_required
def document_templates_edit(module_key: str, document_type: str):
    module_key = _normalise_key(module_key)
    document_type = _normalise_key(document_type)
    if _is_contractor_document_context():
        return _contractor_template_redirect(module_key, document_type)

    if (module_key, document_type) not in DOCUMENT_TEMPLATE_DEFAULTS:
        flash("That document template type is not registered.", "danger")
        return redirect(url_for("settings.document_templates_index"))

    company = _resolve_company()
    if not company:
        flash("Company context is required before document templates can be edited.", "danger")
        return redirect(url_for("settings.profile_index"))

    template = _editable_template(company, module_key, document_type, persist_new=request.method == "POST")
    if request.method == "POST":
        try:
            template.name = (request.form.get("name") or "").strip() or template.name
            template.description = (request.form.get("description") or "").strip() or None
            template.logo_mode = (request.form.get("logo_mode") or "company").strip()
            template.primary_brand_source = (request.form.get("primary_brand_source") or "company").strip()
            template.number_prefix = (request.form.get("number_prefix") or "").strip().upper() or None
            template.terms_body = (request.form.get("terms_body") or "").strip() or None
            template.footer_body = (request.form.get("footer_body") or "").strip() or None
            template.html_body = (request.form.get("html_body") or "").strip() or None
            template.include_terms = request.form.get("include_terms") == "on"
            template.include_signature_block = request.form.get("include_signature_block") == "on"
            template.updated_by_id = getattr(current_user, "id", None)
            template.updated_at = datetime.utcnow()
            db.session.commit()
            flash("Document template updated.", "success")
            return redirect(url_for("settings.document_templates_index", company_id=company.id))
        except SQLAlchemyError:
            db.session.rollback()
            flash("We could not save that document template. Please try again.", "danger")

    payload = get_document_template_payload(company.id, module_key, document_type)
    return render_template(
        "settings/document_templates/form.html",
        company=company,
        template=template,
        payload=payload,
    )


@settings_bp.route(
    "/document-templates/<module_key>/<document_type>/preview",
    methods=["GET"],
    endpoint="document_templates_preview",
)
@login_required
def document_templates_preview(module_key: str, document_type: str):
    module_key = _normalise_key(module_key)
    document_type = _normalise_key(document_type)
    if _is_contractor_document_context():
        return _contractor_template_redirect(module_key, document_type, preview=True)

    if (module_key, document_type) not in DOCUMENT_TEMPLATE_DEFAULTS:
        flash("That document template type is not registered.", "danger")
        return redirect(url_for("settings.document_templates_index"))

    company = _resolve_company()
    if not company:
        flash("Company context is required before document templates can be previewed.", "danger")
        return redirect(url_for("settings.profile_index"))

    payload = document_template_preview_payload(company, module_key, document_type)
    return render_template(
        "settings/document_templates/preview.html",
        company=company,
        payload=payload,
    )
