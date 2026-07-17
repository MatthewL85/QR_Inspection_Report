# Platform Stabilisation Register

Status: active architecture control note

Purpose: keep LogixPM growing as separate, connected modules instead of one tangled application.

## Current Stabilisation Objective

Before major new feature expansion, each module should have:

- a clear source-of-truth model area;
- a dashboard or entry point where the module is user-facing;
- service-led integration with other modules;
- shared IDs instead of duplicated business facts;
- GAR-readable records with visibility boundaries.

## Close-Out Status

Completed for this stabilisation/security close-out:

- module route, dependency and service-contract boundaries;
- role access boundaries for module dashboards and operational queues;
- module settings ownership, including module-owned document-template settings;
- organisation identity and connection-code boundaries;
- Contractor Logix document-template ownership;
- source record identity, stable UID and human-readable numbering boundaries;
- external integration credential, sync, scope and revocation boundaries;
- deployment environment, secret, seed data, migration and feature-flag boundaries;
- incident response, backup, restore and recovery ownership boundaries;
- privacy, sensitive data and module data-classification boundaries;
- observability, monitoring, queue accuracy and degraded-state boundaries;
- release, change-control, validation and rollback boundaries;
- production readiness levels, blockers and sign-off boundaries;
- support ownership, escalation and customer-response boundaries;
- onboarding, import, duplicate-check and data-quality boundaries;
- pilot, live activation and module add-on sign-off boundaries;
- media/evidence source attachment and propagation guardrails;
- auditability and human-approval ownership for cross-module actions;
- retention, archive, deletion and restoration boundaries;
- legacy/archive isolation;
- app/module settings feed visibility;
- admin portal access boundaries;
- the stabilisation register gate itself.

Deferred module-owned close-out:

- Finance Logix security/stabilisation is intentionally deferred to the Finance-owned build slice. It must declare Finance-owned roles, settings, document templates, GAR source adapters and module boundaries before Finance workflows are treated as production-active in the committed Phase 3 suite.

## Active Module Shape

| Layer | Owns | Connects through |
| --- | --- | --- |
| Core Platform | Users, roles, companies, documents, media, audit, notifications, organisation links | `user_id`, `company_id`, `organisation_uid`, `organisation_connection_id` |
| Client / Property Management Logix | Client records, site structure, team assignments, key site information | `client_id`, `unit_id`, `user_id`, `company_id` |
| Unit / Property Asset Spine | Units, block/core/area, occupancy hooks, unit portal identity | `unit_id`, `unit_uid`, `client_id` |
| Members Logix | Owners, co-owners, residents, tenants, member requests, portal access | `member_id`, `resident_id`, `unit_id`, `user_id` |
| Works Logix | Work order lifecycle, routing, completion evidence, reopen requests | `work_order_id`, `member_request_id`, `contractor_id`, `unit_id` |
| Contractor Logix | Contractor queues, job dockets, calendar, completion updates, contractor-only logs | `job_docket_id`, `work_order_id`, `contractor_company_id` |
| Finance Logix | Budgets, charges, invoices, payments, balances | `client_id`, `unit_id`, `work_order_id`, `member_id` |
| Director Logix | Director visibility, approvals and governance | `client_id`, `unit_id`, `member_id`, `user_id` |
| HR Logix | Staff profiles, leave, reviews and future staff self-service | `user_id`, `company_id` |
| GAR AI Layer | Source-backed summaries, recommendations, risk and role-aware answers | source references, visibility rules, audit IDs |

## Non-Negotiable Build Rules

1. Models define persistence. They must not import routes or workflow services.
2. Routes are presentation and workflow entry points. They must not be treated as integration APIs.
3. Cross-module behaviour should move through services, source-backed feeds, lifecycle events or governed connection records.
4. GAR may read, summarise and recommend using source references. GAR must not become the only place business facts exist.
5. Documents, photos, videos and evidence must attach to the record they prove: unit, work order, job docket, contract, key site info, invoice, member request or audit event.
6. Contractor Logix must work both connected to Works Logix and independently through standalone job dockets.
7. Members Logix, Contractor Logix and HR Logix must stay mobile/app-ready from the start.

## Verification Gates

Run these checks after structural work:

```powershell
.\venv\Scripts\python.exe scripts\architecture_smoke_check.py
.\venv\Scripts\python.exe scripts\platform_system_map_check.py
.\venv\Scripts\python.exe scripts\archive_inventory_check.py --strict
.\venv\Scripts\python.exe scripts\legacy_archive_isolation_check.py
.\venv\Scripts\python.exe scripts\core_platform_identity_check.py
.\venv\Scripts\python.exe scripts\migration_integrity_check.py
.\venv\Scripts\python.exe scripts\admin_portal_access_contract_check.py
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\pilot_live_activation_contract_check.py
.\venv\Scripts\python.exe scripts\stabilisation_register_gate_check.py
.\venv\Scripts\python.exe scripts\module_completion_register_check.py
.\venv\Scripts\python.exe scripts\manual_coverage_check.py
.\venv\Scripts\python.exe scripts\phase3_manual_contract_check.py
.\venv\Scripts\python.exe scripts\module_contract_check.py
.\venv\Scripts\python.exe scripts\module_route_boundary_check.py
.\venv\Scripts\python.exe scripts\module_dependency_boundary_check.py
.\venv\Scripts\python.exe scripts\module_service_contract_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\module_settings_registry_check.py
.\venv\Scripts\python.exe scripts\contractor_document_template_boundary_check.py
.\venv\Scripts\python.exe scripts\organisation_connection_boundary_check.py
.\venv\Scripts\python.exe scripts\app_feed_contract_check.py
.\venv\Scripts\python.exe scripts\app_shell_readiness_check.py
.\venv\Scripts\python.exe scripts\app_health_feed_contract_check.py
.\venv\Scripts\python.exe scripts\app_home_feed_contract_check.py
.\venv\Scripts\python.exe scripts\app_capabilities_feed_contract_check.py
.\venv\Scripts\python.exe scripts\app_company_setup_feed_contract_check.py
.\venv\Scripts\python.exe scripts\app_module_settings_feed_contract_check.py
.\venv\Scripts\python.exe scripts\app_mobile_surface_check.py
.\venv\Scripts\python.exe scripts\workflow_action_contract_check.py
.\venv\Scripts\python.exe scripts\notification_contract_check.py
.\venv\Scripts\python.exe scripts\notification_role_visibility_contract_check.py
.\venv\Scripts\python.exe scripts\navbar_notification_contract_check.py
.\venv\Scripts\python.exe scripts\role_dashboard_surface_check.py
.\venv\Scripts\python.exe scripts\dashboard_review_login_check.py
.\venv\Scripts\python.exe scripts\operational_surface_render_check.py
.\venv\Scripts\python.exe scripts\key_site_info_contract_check.py
.\venv\Scripts\python.exe scripts\role_dashboard_notification_contract_check.py
.\venv\Scripts\python.exe scripts\works_command_centre_contract_check.py
.\venv\Scripts\python.exe scripts\works_evidence_audit_contract_check.py
.\venv\Scripts\python.exe scripts\role_dashboard_attention_contract_check.py
.\venv\Scripts\python.exe scripts\media_evidence_spine_check.py
.\venv\Scripts\python.exe scripts\contractor_evidence_propagation_check.py
.\venv\Scripts\python.exe scripts\contractor_standalone_docket_check.py
.\venv\Scripts\python.exe scripts\queue_surface_contract_check.py
.\venv\Scripts\python.exe scripts\template_reference_check.py
.\venv\Scripts\python.exe scripts\url_for_reference_check.py
.\venv\Scripts\python.exe scripts\gar_context_check.py
.\venv\Scripts\python.exe scripts\gar_role_visibility_contract_check.py
.\venv\Scripts\python.exe scripts\gar_source_adapter_contract_check.py
.\venv\Scripts\python.exe scripts\gar_inquiry_endpoint_check.py
.\venv\Scripts\python.exe scripts\works_access_control_check.py
.\venv\Scripts\python.exe scripts\works_lifecycle_flow_check.py
.\venv\Scripts\python.exe scripts\phase3_runner_contract_check.py
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py
```

For regular iteration, run the faster contract-focused suite:

```powershell
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py --quick
```

To run only the heavier role dashboard and operational render smoke checks:

```powershell
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py --smoke-only
```

To inspect the selected checks without running them:

```powershell
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py --quick --list
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py --smoke-only --list
```

The full Phase 3 suite streams each child check, records elapsed time and applies a per-check timeout. Use `PHASE3_CHECK_TIMEOUT_SECONDS` to raise the limit when a local machine is slow, but treat repeated timeouts as a signal to split or optimise the underlying check. Failed checks are retried once by default via `PHASE3_FAILED_CHECK_RETRIES=1` so transient local database disconnects do not invalidate a long suite; repeated failures still fail the suite. Full mode should be used before merge/deployment-style review because it includes both the fast contracts and the role dashboard / operational surface render smoke checks.

The formal unfinished-module register is `docs/module_completion_register.md` and is protected by `scripts/module_completion_register_check.py`. The documentation entry points are protected by `scripts/platform_documentation_contract_check.py`. The runner mode split is protected by `scripts/phase3_runner_contract_check.py`. The access and settings ownership boundary is protected by `scripts/module_access_security_boundary_check.py`. The module settings registry ownership rule is protected by `scripts/module_settings_registry_check.py`. Service-led integration and source-backed feeds are protected by `scripts/module_service_contract_check.py`. Legacy/archive isolation is protected by `scripts/legacy_archive_isolation_check.py`. The media/evidence spine is protected by `scripts/media_evidence_spine_check.py`. Contractor-owned document templates are protected by `scripts/contractor_document_template_boundary_check.py`. Organisation connection boundaries are protected by `scripts/organisation_connection_boundary_check.py`.

The close-out sign-off checklist is `docs/stabilisation_security_closeout.md`. Treat it as the short release-readiness control before moving from stabilisation into wider feature expansion. The role-by-module access contract is `docs/module_access_matrix.md`. The module and organisation connection contract is `docs/module_connection_matrix.md`. The document-template ownership contract is `docs/document_template_ownership_matrix.md`. The source record identity and numbering contract is `docs/source_record_identity_matrix.md`. The external integration security contract is `docs/external_integration_security_matrix.md`. The deployment environment security contract is `docs/deployment_environment_security_matrix.md`. The incident response and backup contract is `docs/incident_response_backup_matrix.md`. The privacy and data classification contract is `docs/privacy_data_classification_matrix.md`. The observability and monitoring contract is `docs/observability_monitoring_matrix.md`. The release and change management contract is `docs/release_change_management_matrix.md`. The production readiness gate is `docs/production_readiness_gate.md`. The support and escalation ownership contract is `docs/support_escalation_ownership_matrix.md`. The onboarding and data import contract is `docs/onboarding_data_import_matrix.md`. The pilot and live activation contract is `docs/pilot_live_activation_runbook.md`. The GAR visibility contract is `docs/gar_visibility_matrix.md`. The auditability contract is `docs/auditability_matrix.md`. The data retention and deletion contract is `docs/data_retention_deletion_matrix.md`.

## Next Stabilisation Steps

1. Keep `legacy_archive` and `Old_QR` out of active feature work.
2. Standardise the remaining heavy pages against the current light dashboard pattern.
3. Extend route-level smoke checks as new role dashboards and queue pages are added.
4. Keep extending the user manual whenever a user-facing workflow becomes real.
5. Keep module-level API/service contracts covered before deeper Finance, HR, Director and GAR build-out.
6. Keep media/evidence propagation covered whenever request, work order, docket or completion evidence changes.
7. Keep Key Site Information rich text, media, contractor visibility and safe rendering covered as it becomes an operational source of truth.
8. Keep Works Logix and Contractor Logix operational queues tile-driven: one selected queue list at a time, compact filters, no duplicated attention/list blocks.
9. Keep organisation identity, module subscription and organisation-connection setup inside the core platform gate so independently purchased modules can connect without email-address coupling.
10. Keep Alembic migration metadata valid and the recent Contractor/Works schema chain intact before expanding the operational workflow.
11. Keep Contractor Logix independently useful: manual job docket creation, private materials/time logs and scheduling must continue to work without a linked Works Logix work order.
12. Keep `docs/module_completion_register.md` current whenever a module is started, paused, split into another task or made dependent on another module.
