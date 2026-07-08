from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.models.core.document_template import CoreDocumentTemplate
from app.models.onboarding.company import Company


DEFAULT_SUPPORTED_OUTPUT_FORMATS = ["html", "pdf"]

DOCUMENT_TEMPLATE_DEFAULTS: dict[tuple[str, str], dict[str, Any]] = {
    ("works_logix", "work_order"): {
        "name": "Works Logix Work Order",
        "logo_mode": "company",
        "number_prefix": "WO",
        "description": "Management-side work order instruction and review record.",
        "required_context_keys": ["work_order_ref", "client_name", "location", "issue_summary"],
    },
    ("contractor_logix", "job_docket"): {
        "name": "Contractor Logix Job Docket",
        "logo_mode": "contractor",
        "number_prefix": "JD",
        "description": "Contractor operational job docket for scheduling, attendance and completion.",
        "required_context_keys": ["job_docket_ref", "work_order_ref", "site_contact", "scope_of_works"],
    },
    ("works_logix", "quote_request"): {
        "name": "Works Logix Quotation Request",
        "logo_mode": "company",
        "number_prefix": "QR",
        "description": "Quotation request sent to one or more contractors.",
        "required_context_keys": ["quote_request_ref", "client_name", "scope_of_works"],
    },
    ("contractor_logix", "quote_response"): {
        "name": "Contractor Logix Quotation Response",
        "logo_mode": "contractor",
        "number_prefix": "QT",
        "description": "Contractor quotation response returned to Works Logix.",
        "required_context_keys": ["quote_response_ref", "quoted_total", "valid_until"],
    },
    ("contractor_logix", "payment_request"): {
        "name": "Contractor Logix Payment Request",
        "logo_mode": "dual",
        "number_prefix": "PR",
        "description": "Payment request sent from Contractor Logix to Works/Finance review.",
        "required_context_keys": ["payment_request_ref", "job_docket_ref", "work_order_ref", "requested_total"],
    },
    ("finance_logix", "invoice"): {
        "name": "Finance Logix Invoice",
        "logo_mode": "company",
        "number_prefix": "INV",
        "description": "Finance-ready invoice template for future debtor and contractor workflows.",
        "required_context_keys": ["invoice_ref", "account_name", "invoice_total", "due_date"],
    },
    ("contracts_logix", "contract"): {
        "name": "Contracts Logix Agreement",
        "logo_mode": "company",
        "number_prefix": "CON",
        "description": "Managed contract document wrapper with branding and terms.",
        "required_context_keys": ["contract_ref", "client_name", "contract_period"],
    },
    ("gar", "gar_report"): {
        "name": "GAR AI Report",
        "logo_mode": "company",
        "number_prefix": "GAR",
        "description": "GAR source-backed report template for governed intelligence outputs.",
        "required_context_keys": ["report_title", "source_summary", "generated_for"],
    },
}

DOCUMENT_TEMPLATE_OWNERSHIP: dict[tuple[str, str], dict[str, Any]] = {
    ("works_logix", "work_order"): {
        "owner_module": "Property Management Logix",
        "created_by": "PM / Admin / Assistant",
        "reviewed_by": "Property Management Logix",
        "availability": "Management company settings",
        "handoff": False,
    },
    ("contractor_logix", "job_docket"): {
        "owner_module": "Contractor Logix",
        "created_by": "Contractor",
        "reviewed_by": "Contractor Logix",
        "availability": "Contractor company settings",
        "handoff": False,
    },
    ("works_logix", "quote_request"): {
        "owner_module": "Property Management Logix",
        "created_by": "PM / Admin / Assistant",
        "reviewed_by": "Works Logix",
        "availability": "Management company settings",
        "handoff": True,
    },
    ("contractor_logix", "quote_response"): {
        "owner_module": "Contractor Logix",
        "created_by": "Contractor",
        "reviewed_by": "Works Logix / Directors Logix",
        "availability": "Contractor company settings",
        "handoff": True,
    },
    ("contractor_logix", "payment_request"): {
        "owner_module": "Contractor Logix",
        "created_by": "Contractor",
        "reviewed_by": "Works Logix / Finance Logix",
        "availability": "Contractor company settings",
        "handoff": True,
    },
    ("finance_logix", "invoice"): {
        "owner_module": "Finance Logix",
        "created_by": "Finance",
        "reviewed_by": "Finance Logix",
        "availability": "Finance settings",
        "handoff": False,
    },
    ("contracts_logix", "contract"): {
        "owner_module": "Contracts Logix",
        "created_by": "Super Admin / Admin",
        "reviewed_by": "Contracts Logix",
        "availability": "Contract settings",
        "handoff": False,
    },
    ("gar", "gar_report"): {
        "owner_module": "GAR AI",
        "created_by": "GAR / Authorised user",
        "reviewed_by": "Role-aware module view",
        "availability": "GAR settings",
        "handoff": False,
    },
}


def _normalise_key(value: str | None) -> str:
    return (value or "").strip().lower()


def _company_branding(company: Company | None) -> dict[str, Any]:
    if not company:
        return {
            "name": "LogixPM",
            "logo_path": None,
            "primary_color": "#2554ff",
            "secondary_color": "#111c34",
            "address": "",
            "email": None,
            "phone": None,
        }

    address = getattr(company, "address_block", None)
    if callable(address):
        address_value = address()
    else:
        address_value = address or ""

    return {
        "id": company.id,
        "name": company.name,
        "logo_path": company.logo_path,
        "primary_color": getattr(company, "theme_primary", None) or company.brand_primary_color or company.brand_color or "#2554ff",
        "secondary_color": getattr(company, "theme_secondary", None) or company.brand_secondary_color or "#111c34",
        "address": address_value,
        "email": company.email,
        "phone": company.phone,
        "currency": company.currency,
        "work_order_prefix": getattr(company, "resolved_work_order_prefix", None),
    }


def _default_template(module_key: str, document_type: str) -> dict[str, Any]:
    key = (_normalise_key(module_key), _normalise_key(document_type))
    default = deepcopy(DOCUMENT_TEMPLATE_DEFAULTS.get(key, {}))
    default.setdefault("module_key", key[0])
    default.setdefault("document_type", key[1])
    default.setdefault("name", f"{key[0].replace('_', ' ').title()} {key[1].replace('_', ' ').title()}")
    default.setdefault("status", "Active")
    default.setdefault("version_label", "v1")
    default.setdefault("template_format", "html")
    default.setdefault("html_body", None)
    default.setdefault("terms_body", None)
    default.setdefault("footer_body", None)
    default.setdefault("include_signature_block", False)
    default.setdefault("include_terms", True)
    default.setdefault("primary_brand_source", "company")
    default.setdefault("visibility_scope", "company")
    default.setdefault("sequence_padding", 5)
    default.setdefault("supported_output_formats", DEFAULT_SUPPORTED_OUTPUT_FORMATS)
    default.setdefault("required_context_keys", [])
    default.setdefault("default_context", {})
    default["id"] = None
    default["source"] = "system_default"
    return default


def resolve_document_template(
    company_id: int | None,
    module_key: str,
    document_type: str,
) -> CoreDocumentTemplate | dict[str, Any]:
    module = _normalise_key(module_key)
    doc_type = _normalise_key(document_type)
    if company_id:
        template = (
            CoreDocumentTemplate.query.filter_by(
                company_id=company_id,
                module_key=module,
                document_type=doc_type,
                status="Active",
            )
            .order_by(CoreDocumentTemplate.updated_at.desc(), CoreDocumentTemplate.id.desc())
            .first()
        )
        if template:
            return template

    template = (
        CoreDocumentTemplate.query.filter_by(
            company_id=None,
            module_key=module,
            document_type=doc_type,
            status="Active",
        )
        .order_by(CoreDocumentTemplate.updated_at.desc(), CoreDocumentTemplate.id.desc())
        .first()
    )
    return template or _default_template(module, doc_type)


def build_document_template_context(
    company: Company | None = None,
    source_record: Any | None = None,
    contractor_company: Company | None = None,
    extra_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context: dict[str, Any] = {
        "company": _company_branding(company),
        "contractor_company": _company_branding(contractor_company) if contractor_company else None,
        "source_record": {
            "model": source_record.__class__.__name__ if source_record else None,
            "id": getattr(source_record, "id", None),
            "reference": (
                getattr(source_record, "display_reference", None)
                or getattr(source_record, "reference", None)
                or getattr(source_record, "job_docket_number", None)
                or getattr(source_record, "work_order_number", None)
            ),
        },
    }
    if extra_context:
        context.update(extra_context)
    return context


def document_template_payload(
    template: CoreDocumentTemplate | dict[str, Any],
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if isinstance(template, CoreDocumentTemplate):
        return {
            "id": template.id,
            "source": "database",
            "company_id": template.company_id,
            "module_key": template.module_key,
            "document_type": template.document_type,
            "name": template.name,
            "description": template.description,
            "status": template.status,
            "version_label": template.version_label,
            "template_format": template.template_format,
            "html_body": template.html_body,
            "terms_body": template.terms_body,
            "footer_body": template.footer_body,
            "logo_mode": template.logo_mode,
            "primary_brand_source": template.primary_brand_source,
            "include_signature_block": template.include_signature_block,
            "include_terms": template.include_terms,
            "number_prefix": template.number_prefix,
            "sequence_padding": template.sequence_padding,
            "supported_output_formats": template.supported_output_formats or DEFAULT_SUPPORTED_OUTPUT_FORMATS,
            "required_context_keys": template.required_context_keys or [],
            "default_context": template.default_context or {},
            "visibility_scope": template.visibility_scope,
            "is_locked": template.is_locked,
            "context": context or {},
        }

    payload = deepcopy(template)
    payload["context"] = context or {}
    return payload


def get_document_template_payload(
    company_id: int | None,
    module_key: str,
    document_type: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    template = resolve_document_template(company_id, module_key, document_type)
    return document_template_payload(template, context=context)


def document_template_catalog(company_id: int | None = None) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    for key, defaults in sorted(
        DOCUMENT_TEMPLATE_DEFAULTS.items(),
        key=lambda item: (
            DOCUMENT_TEMPLATE_OWNERSHIP.get(item[0], {}).get("owner_module", ""),
            item[1].get("name", ""),
        ),
    ):
        module_key, document_type = key
        template = resolve_document_template(company_id, module_key, document_type)
        payload = document_template_payload(template)
        ownership = DOCUMENT_TEMPLATE_OWNERSHIP.get(key, {})
        catalog.append(
            {
                **payload,
                "default_name": defaults.get("name"),
                "owner_module": ownership.get("owner_module", module_key.replace("_", " ").title()),
                "created_by": ownership.get("created_by", "-"),
                "reviewed_by": ownership.get("reviewed_by", "-"),
                "availability": ownership.get("availability", "Settings"),
                "handoff": bool(ownership.get("handoff")),
                "has_company_template": payload.get("source") == "database",
            }
        )
    return catalog
