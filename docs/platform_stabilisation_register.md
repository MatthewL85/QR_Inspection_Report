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
.\venv\Scripts\python.exe scripts\platform_system_map_check.py
.\venv\Scripts\python.exe scripts\archive_inventory_check.py --strict
.\venv\Scripts\python.exe scripts\core_platform_identity_check.py
.\venv\Scripts\python.exe scripts\migration_integrity_check.py
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\module_contract_check.py
.\venv\Scripts\python.exe scripts\module_route_boundary_check.py
.\venv\Scripts\python.exe scripts\module_dependency_boundary_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\app_company_setup_feed_contract_check.py
.\venv\Scripts\python.exe scripts\role_dashboard_surface_check.py
.\venv\Scripts\python.exe scripts\dashboard_review_login_check.py
.\venv\Scripts\python.exe scripts\operational_surface_render_check.py
.\venv\Scripts\python.exe scripts\key_site_info_contract_check.py
.\venv\Scripts\python.exe scripts\contractor_evidence_propagation_check.py
.\venv\Scripts\python.exe scripts\contractor_standalone_docket_check.py
.\venv\Scripts\python.exe scripts\queue_surface_contract_check.py
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

The formal unfinished-module register is `docs/module_completion_register.md`. The documentation entry points are protected by `scripts/platform_documentation_contract_check.py`. The runner mode split is protected by `scripts/phase3_runner_contract_check.py`. The access and settings ownership boundary is protected by `scripts/module_access_security_boundary_check.py`.

## Next Stabilisation Steps

1. Keep `legacy_archive` and `Old_QR` out of active feature work.
2. Standardise the remaining heavy pages against the current light dashboard pattern.
3. Extend route-level smoke checks as new role dashboards and queue pages are added.
4. Keep extending the user manual whenever a user-facing workflow becomes real.
5. Add module-level API/service contracts before deeper Finance, HR, Director and GAR build-out.
6. Keep media/evidence propagation covered whenever request, work order, docket or completion evidence changes.
7. Keep Key Site Information rich text, media, contractor visibility and safe rendering covered as it becomes an operational source of truth.
8. Keep Works Logix and Contractor Logix operational queues tile-driven: one selected queue list at a time, compact filters, no duplicated attention/list blocks.
9. Keep organisation identity, module subscription and organisation-connection setup inside the core platform gate so independently purchased modules can connect without email-address coupling.
10. Keep Alembic migration metadata valid and the recent Contractor/Works schema chain intact before expanding the operational workflow.
11. Keep Contractor Logix independently useful: manual job docket creation, private materials/time logs and scheduling must continue to work without a linked Works Logix work order.
12. Keep `docs/module_completion_register.md` current whenever a module is started, paused, split into another task or made dependent on another module.
