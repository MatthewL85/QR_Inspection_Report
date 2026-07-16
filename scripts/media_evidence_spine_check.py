"""Guard the shared media/evidence spine across Phase 3 modules.

The platform is still using evidence references in several places while the
future MediaFile-backed upload service is being shaped. This check makes that
intent explicit so Members Logix, Works Logix, Contractor Logix and GAR do not
drift into disconnected attachment handling.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


MEDIAFILE_REQUIRED_COLUMNS = {
    "filename",
    "file_path",
    "file_type",
    "uploaded_by",
    "related_table",
    "related_id",
    "visibility",
    "role_visibility",
    "parsed_summary",
    "extracted_data",
    "ai_classification",
    "ai_confidence_score",
}

REQUIRED_MEDIA_CONTEXTS = {
    "member_maintenance_request": {
        "owning_module": "members_logix",
        "related_table": "maintenance_request",
    },
    "contractor_completion_evidence": {
        "owning_module": "contractor_logix",
        "related_table": "work_order_completion",
    },
    "member_work_order_feedback": {
        "owning_module": "members_logix",
        "related_table": "contractor_feedback",
    },
    "member_reopen_request": {
        "owning_module": "members_logix",
        "related_table": "work_order_reopen_request",
    },
}

REFERENCE_FIELD_FILES = {
    "app/routes/members/__init__.py": (
        "media_reference",
        "uploaded_references",
        "attachment_url",
        "attachments_count",
        "doc_links",
        "photo_links",
    ),
    "app/routes/contractor.py": (
        "uploaded_references",
        "evidence_links",
        "attachments_count",
        "evidence_reference",
    ),
    "app/services/works/audit_pack_service.py": (
        "build_completion_evidence_pack",
        "evidence_items",
        "source_references",
        "WorkOrderCompletion",
        "WorkOrderReopenRequest",
    ),
    "app/services/works/work_order_docket_service.py": (
        "build_contractor_work_order_docket",
        "evidence_items",
        "reference_url",
        "Open evidence",
    ),
    "app/services/members/works_context.py": (
        "completion_evidence",
        "evidence_reference",
        "evidence_links",
    ),
    "app/services/gar/source_queries.py": (
        "MediaFile",
        "related_table",
        "related_id",
        "ai_classification",
    ),
}

TEMPLATE_EVIDENCE_TOKENS = {
    "app/templates/members/works.html": (
        'data-app-media-reference="true"',
        'data-app-media-source-model="MediaFile"',
        'data-app-direct-upload="false"',
        "member_maintenance_request",
        "member_work_order_feedback",
        "member_reopen_request",
    ),
    "app/templates/contractor/work_orders.html": (
        'data-app-media-reference="true"',
        'data-app-media-source-model="MediaFile"',
        'data-app-direct-upload="false"',
        "contractor_completion_evidence",
        "contractor_progress_update",
    ),
    "app/templates/contractor/work_order_detail.html": (
        "docket.evidence_items",
        "works-evidence-link",
        "Open Evidence",
    ),
    "app/templates/contractor/job_docket_detail.html": (
        "work_pack.evidence_items",
        "works-evidence-link",
        "Open Evidence",
    ),
    "app/templates/units/work_order_review.html": (
        "work_order_audit_pack.evidence_items",
        "works-evidence-link",
        "Open Evidence",
    ),
    "app/templates/works/member_request_detail.html": (
        "works-evidence-link",
        "Open attached evidence",
    ),
}

REQUIRED_RELATED_CHECKS = {
    "Works Evidence Audit Contract": "works_evidence_audit_contract_check.py",
    "Contractor Evidence Propagation Contract": "contractor_evidence_propagation_check.py",
    "App Mobile Surface": "app_mobile_surface_check.py",
    "App Home Feed Contract": "app_home_feed_contract_check.py",
    "App Capabilities Feed Contract": "app_capabilities_feed_contract_check.py",
}


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8", errors="replace")


def main() -> int:
    from app.models.core.media_file import MediaFile
    from app.services.core.app_home import APP_MEDIA_CONTRACT, APP_POLICY
    import scripts.phase3_readiness_check as readiness

    failures: list[str] = []

    media_columns = set(MediaFile.__table__.columns.keys())
    missing_columns = MEDIAFILE_REQUIRED_COLUMNS.difference(media_columns)
    if missing_columns:
        failures.append("MediaFile missing required columns: " + ", ".join(sorted(missing_columns)))

    if APP_MEDIA_CONTRACT.get("contract_version") != "phase3e-app-media-v1":
        failures.append("APP_MEDIA_CONTRACT version changed.")
    if APP_MEDIA_CONTRACT.get("source_model") != "MediaFile":
        failures.append("APP_MEDIA_CONTRACT must keep MediaFile as the source model.")
    if APP_MEDIA_CONTRACT.get("direct_binary_uploads_enabled"):
        failures.append("Direct binary uploads must remain disabled until the governed MediaFile service is complete.")
    if not APP_MEDIA_CONTRACT.get("evidence_references_supported"):
        failures.append("Evidence references must remain supported during the transition to MediaFile.")

    media_policy = (APP_POLICY.get("media") or {})
    if media_policy.get("direct_binary_uploads_enabled"):
        failures.append("App policy must not expose direct binary uploads yet.")
    if not media_policy.get("evidence_references_supported"):
        failures.append("App policy must support evidence references.")

    guardrails = APP_MEDIA_CONTRACT.get("guardrails") or {}
    for key in (
        "requires_authenticated_session",
        "requires_csrf_for_mutation",
        "requires_record_context",
        "server_generated_media_ids",
        "virus_scan_required_before_visibility",
        "role_visibility_required",
    ):
        if guardrails.get(key) is not True:
            failures.append(f"Media guardrail must be true: {key}")
    for key in ("client_generated_business_ids_allowed", "offline_upload_queue_allowed"):
        if guardrails.get(key):
            failures.append(f"Media guardrail must remain false: {key}")

    contexts = {
        item.get("key"): item
        for item in APP_MEDIA_CONTRACT.get("contexts", [])
        if isinstance(item, dict)
    }
    for key, expected in REQUIRED_MEDIA_CONTEXTS.items():
        context = contexts.get(key)
        if not context:
            failures.append(f"APP_MEDIA_CONTRACT missing context: {key}")
            continue
        for field, expected_value in expected.items():
            if context.get(field) != expected_value:
                failures.append(f"Media context {key} changed {field}: {context.get(field)}")
        if not context.get("required_context_fields"):
            failures.append(f"Media context {key} must declare required context fields.")
        if not context.get("visibility"):
            failures.append(f"Media context {key} must declare role-aware visibility.")

    for relative_path, tokens in REFERENCE_FIELD_FILES.items():
        content = _read(relative_path)
        for token in tokens:
            if token not in content:
                failures.append(f"{relative_path} is missing evidence spine token: {token}")

    for relative_path, tokens in TEMPLATE_EVIDENCE_TOKENS.items():
        content = _read(relative_path)
        for token in tokens:
            if token not in content:
                failures.append(f"{relative_path} is missing evidence UI token: {token}")

    readiness_checks = dict(readiness.CHECKS)
    for label, script_name in REQUIRED_RELATED_CHECKS.items():
        if readiness_checks.get(label) != script_name:
            failures.append(f"Phase 3 runner must include {label}: {script_name}")

    if failures:
        print("FAILED: media/evidence spine guardrail failed")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Media/evidence spine check")
    print(f"- MediaFile columns checked: {len(MEDIAFILE_REQUIRED_COLUMNS)}")
    print(f"- Media contexts checked: {len(REQUIRED_MEDIA_CONTEXTS)}")
    print(f"- Evidence source files checked: {len(REFERENCE_FIELD_FILES)}")
    print(f"- Evidence templates checked: {len(TEMPLATE_EVIDENCE_TOKENS)}")
    print("- Related runner checks present: yes")
    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
