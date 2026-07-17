from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise AssertionError(f"Missing {label}: {token}")


def main() -> None:
    model = read("app/models/core/document_template.py")
    service = read("app/services/core/document_template_service.py")
    settings_route = read("app/routes/settings/document_templates.py")
    settings_init = read("app/routes/settings/__init__.py")
    index_template = read("app/templates/settings/document_templates/index.html")
    form_template = read("app/templates/settings/document_templates/form.html")
    preview_template = read("app/templates/settings/document_templates/preview.html")
    company_profile_template = read("app/templates/settings/company_profile/index.html")
    super_admin_sidebar = read("app/templates/_partials/super_admin_sidebar.html")
    docs = "\n".join(
        [
            read("docs/manual/documents_logix.md"),
            read("docs/manual/contractor_logix.md"),
            read("docs/manual/works_logix.md"),
        ]
    )
    migration = read("migrations/versions/a0b1c2d3e4f5_add_core_document_templates.py")

    for token in [
        "class CoreDocumentTemplate",
        "__tablename__ = \"core_document_templates\"",
        "module_key",
        "document_type",
        "logo_mode",
        "terms_body",
        "footer_body",
        "number_prefix",
        "supported_output_formats",
    ]:
        require(model, token, "model field")

    for token in [
        "DOCUMENT_TEMPLATE_DEFAULTS",
        "resolve_document_template",
        "build_document_template_context",
        "document_template_payload",
        "document_template_catalog",
        "document_template_render_payload",
        "document_template_preview_payload",
        "DOCUMENT_TEMPLATE_OWNERSHIP",
        "DOCUMENT_TEMPLATE_SAMPLE_CONTEXTS",
        "\"payment_request\"",
        "\"job_docket\"",
        "\"quote_request\"",
        "\"quote_response\"",
        "\"invoice\"",
        "\"gar_report\"",
    ]:
        require(service, token, "service contract")

    for token in [
        "document_templates_index",
        "document_templates_edit",
        "document_templates_preview",
        "Document Templates",
        "Document Ownership Map",
        "Document Preview",
        "Created By",
        "Reviewed / Used By",
        "Payment Requests",
        "Job Dockets",
    ]:
        combined_settings = "\n".join(
            [
                settings_route,
                settings_init,
                index_template,
                form_template,
                preview_template,
                company_profile_template,
                super_admin_sidebar,
            ]
        )
        require(combined_settings, token, "settings template manager")

    for token in [
        "Document & Template Setup",
        "Open Document Templates",
        "settings.document_templates_index",
        "settings.document_templates_edit",
        "company-document-setup-grid",
    ]:
        require(company_profile_template, token, "company profile document setup")

    for token in [
        "Document Templates",
        "settings.document_templates_index",
    ]:
        require(super_admin_sidebar, token, "super admin settings sidebar")

    for token in [
        "Core Document Template Foundation",
        "Payment Requests",
        "Job Dockets",
        "Quotations",
        "Invoices",
        "GAR",
    ]:
        require(docs, token, "manual coverage")

    require(migration, "core_document_templates", "migration table")
    require(migration, "down_revision = \"f9a0b1c2d3e4\"", "migration chain")
    print("document template foundation check passed")


if __name__ == "__main__":
    main()
