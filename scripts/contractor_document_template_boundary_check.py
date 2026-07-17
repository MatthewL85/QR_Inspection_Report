"""Verify Contractor Logix document templates stay inside Contractor Logix."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.services.core.document_template_service import (
    DOCUMENT_TEMPLATE_DEFAULTS,
    DOCUMENT_TEMPLATE_OWNERSHIP,
    document_template_catalog,
)
from scripts.seed_dashboard_review_users import REVIEW_PASSWORD


CONTRACTOR_DOCUMENT_TYPES = {"job_docket", "payment_request", "quote_response"}
MANAGEMENT_DOCUMENT_TYPES = {"work_order", "quote_request"}
REQUIRED_OWNERSHIP = {
    ("works_logix", "work_order"): "Property Management Logix",
    ("works_logix", "quote_request"): "Property Management Logix",
    ("contractor_logix", "job_docket"): "Contractor Logix",
    ("contractor_logix", "quote_response"): "Contractor Logix",
    ("contractor_logix", "payment_request"): "Contractor Logix",
    ("finance_logix", "invoice"): "Finance Logix",
    ("contracts_logix", "contract"): "Contracts Logix",
    ("gar", "gar_report"): "GAR AI",
}


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _check_catalog_ownership(failures: list[str]) -> None:
    missing_ownership = sorted(set(DOCUMENT_TEMPLATE_DEFAULTS).difference(DOCUMENT_TEMPLATE_OWNERSHIP))
    if missing_ownership:
        failures.append(f"document defaults missing ownership records: {missing_ownership}")

    unexpected_ownership = sorted(set(DOCUMENT_TEMPLATE_OWNERSHIP).difference(DOCUMENT_TEMPLATE_DEFAULTS))
    if unexpected_ownership:
        failures.append(f"document ownership records without defaults: {unexpected_ownership}")

    for key, expected_owner in REQUIRED_OWNERSHIP.items():
        ownership = DOCUMENT_TEMPLATE_OWNERSHIP.get(key)
        if not ownership:
            failures.append(f"{key}: missing ownership definition")
            continue
        actual_owner = ownership.get("owner_module")
        if actual_owner != expected_owner:
            failures.append(f"{key}: expected owner {expected_owner!r}, got {actual_owner!r}")
        for required_field in ("created_by", "reviewed_by", "availability"):
            if not ownership.get(required_field):
                failures.append(f"{key}: missing ownership field {required_field}")

    contractor_types = {
        document_type
        for module_key, document_type in DOCUMENT_TEMPLATE_DEFAULTS
        if module_key == "contractor_logix"
    }
    if contractor_types != CONTRACTOR_DOCUMENT_TYPES:
        failures.append(
            "Contractor Logix document types drifted: "
            f"expected {sorted(CONTRACTOR_DOCUMENT_TYPES)}, got {sorted(contractor_types)}"
        )

    catalog = document_template_catalog(None)
    contractor_catalog = [item for item in catalog if item.get("module_key") == "contractor_logix"]
    if {item.get("document_type") for item in contractor_catalog} != CONTRACTOR_DOCUMENT_TYPES:
        failures.append("Contractor catalogue does not expose exactly the contractor-owned document types")
    for item in contractor_catalog:
        if item.get("owner_module") != "Contractor Logix":
            failures.append(f"{item.get('document_type')}: contractor catalogue owner drifted")
        if item.get("availability") != "Contractor company settings":
            failures.append(f"{item.get('document_type')}: contractor availability drifted")


def _check_route_boundaries(failures: list[str]) -> None:
    contractor_route = _read("app/routes/contractor.py")
    settings_route = _read("app/routes/settings/document_templates.py")
    contractor_template = _read("app/templates/contractor/document_templates.html")
    shared_template = _read("app/templates/settings/document_templates/index.html")

    for endpoint in (
        "contractor_document_templates",
        "contractor_document_template_edit",
        "contractor_document_template_preview",
    ):
        if endpoint not in contractor_route:
            failures.append(f"Contractor route missing endpoint {endpoint}")

    if "CONTRACTOR_DOCUMENT_TYPES = {\"job_docket\", \"quote_response\", \"payment_request\"}" not in contractor_route:
        failures.append("Contractor route must explicitly whitelist contractor-owned document types")
    if "module_key=CONTRACTOR_DOCUMENT_MODULE_KEY" not in contractor_route:
        failures.append("Contractor route must always write templates under contractor_logix")
    if "url_for(\"contractor.contractor_document_templates\")" not in settings_route:
        failures.append("Shared settings route must redirect contractor users to Contractor Logix templates")

    for forbidden in MANAGEMENT_DOCUMENT_TYPES:
        if forbidden in contractor_template:
            failures.append(f"Contractor template surface mentions management-owned document type {forbidden}")
    for required in ("Job Dockets", "Payment Requests", "Contractor Logix"):
        if required not in shared_template:
            failures.append(f"Shared document template surface missing ownership copy: {required}")


def main() -> int:
    app = create_app()
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True

    failures: list[str] = []

    with app.app_context():
        _check_catalog_ownership(failures)
        _check_route_boundaries(failures)

        with app.test_client() as client:
            login = client.post(
                "/auth/login",
                data={
                    "identifier": "review.contractor@logixpm.test",
                    "password": REVIEW_PASSWORD,
                },
                follow_redirects=False,
            )
            if login.status_code not in {302, 303}:
                failures.append(f"contractor login failed: {login.status_code}")

            for path, marker in (
                ("/contractor/settings/document-templates", "Contractor-Owned Templates"),
                ("/contractor/settings/document-templates/job_docket/edit", "Edit Template"),
                ("/contractor/settings/document-templates/job_docket/preview", "Document Preview"),
            ):
                response = client.get(path, follow_redirects=False)
                text = response.get_data(as_text=True)
                if response.status_code != 200:
                    failures.append(f"{path}: expected 200, got {response.status_code}")
                if marker not in text:
                    failures.append(f"{path}: missing marker {marker!r}")
                if "Super Admin" in text:
                    failures.append(f"{path}: rendered Super Admin copy in Contractor Logix")

            bypass = client.get("/settings/document-templates?company_id=1", follow_redirects=False)
            location = bypass.headers.get("Location") or ""
            if bypass.status_code not in {302, 303}:
                failures.append(f"shared settings bypass expected redirect, got {bypass.status_code}")
            if "/contractor/settings/document-templates" not in location:
                failures.append(f"shared settings bypass redirected to unexpected location: {location}")

    if failures:
        print("FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASSED contractor document template boundary check")
    print(f"- Document templates checked: {len(DOCUMENT_TEMPLATE_DEFAULTS)}")
    print(f"- Contractor document types: {', '.join(sorted(CONTRACTOR_DOCUMENT_TYPES))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
