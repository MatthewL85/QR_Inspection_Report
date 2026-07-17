# Release and Change Management Matrix

Status: active release and change-control contract

Purpose: define how LogixPM changes move from local work, through review, validation, deployment, rollback and module activation without mixing unfinished module work, unsafe seed data or unclear ownership into production.

## Core Rule

Every code, schema, data, setting, document-template, external-integration and GAR change must have an owner, scope, validation path and rollback or recovery plan before it is treated as production-ready.

Release control is not only a GitHub step. It is the operational boundary that protects the modular platform from becoming tangled, accidentally exposing unfinished modules or promoting local test data.

## Release Ownership Matrix

| Area | Release owner | Production rule |
| --- | --- | --- |
| Core Platform | Super Admin / platform owner | Auth, users, roles, organisations, notifications, media, audit and app shell changes must not weaken module boundaries. |
| Property Management Logix | Property Management module owner | Client, unit, contract, key-site-info and dashboard changes must preserve client and unit source records. |
| Works Logix | Works module owner | Work request, work order, evidence, reopen and contractor-routing changes must preserve lifecycle and audit history. |
| Contractor Logix | Contractor module owner | Job docket, calendar, private log, quotation response and payment-request changes must stay contractor-owned. |
| Members Logix | Members module owner | Member portal, linked unit, maintenance request and resident/owner visibility changes must preserve membership boundaries. |
| Director Logix | Director module owner | Director visibility, voting and governance changes must not expose non-director operational data. |
| Finance Logix | Finance module owner | Finance routes, records, settings, document templates and GAR adapters remain deferred until Finance-owned security close-out is complete. |
| HR Logix | HR module owner | HR records, settings and documents must stay HR-owned and HR-visible only. |
| GAR AI Layer | GAR owner plus source module owner | GAR may summarize and recommend only from source records the user can open directly. |
| External Integrations | Owning module plus platform owner | Credentials, scopes, sync jobs, webhooks and revocation must be owned by the module using the integration. |

## Change Classes

| Change class | Required release control |
| --- | --- |
| Code or UI change | List affected routes, templates, services and role surfaces. Run relevant contract and smoke checks. |
| Schema or migration change | Include migration with code, validate migration chain and document rollback or recovery impact. |
| Settings change | Confirm the setting belongs to the module that owns the workflow. Do not link users into another module's settings area. |
| Document-template change | Confirm the document output is owned by the module that creates and controls it. |
| Data or seed change | Keep review/test seed data local unless it is explicitly production-safe and environment-gated. |
| External integration change | Confirm credential owner, scope, sync logging, revoke path and degraded-state behaviour. |
| GAR change | Confirm source adapter, source references, role visibility, degraded-state handling and answer boundaries. |
| Media or evidence change | Confirm files attach to the source record they prove and do not become orphaned. |

## Release Rules

1. Do not stage unrelated dirty files just because they are already present locally.
2. Do not activate a module because a route exists. Module subscription, role access and settings ownership must allow it.
3. Do not promote local review users, demo records or seed scripts as production content.
4. Do not ship migrations without their matching model and route/service expectations.
4a. Schema and migration changes must follow the schema and migration ownership contract in `docs/schema_migration_ownership_matrix.md`.
5. Do not rewrite signed, approved, completed, paid or closed source records during release. Use controlled amendment, superseding or archive behaviour.
6. Do not move document templates into a shared settings area when the workflow belongs to a specific module.
7. Do not add GAR answers or feeds without source references and role visibility checks.
8. Do not widen an external integration scope without an owner, reason, audit trail and revocation plan.
9. Do not treat a dashboard count as production-ready unless the user can open the same filtered record list behind it.
10. Do not release if rollback would delete audit history, source IDs, media, evidence or external sync state.

## PR And Merge Checklist

Before merge or deployment-style review, confirm:

- the scope is stated clearly;
- affected modules are listed;
- unrelated local changes are excluded;
- migrations are present and validated where needed;
- module access and settings ownership rules are checked;
- document-template ownership rules are checked where documents are affected;
- GAR source-adapter and visibility checks are run where GAR changes are affected;
- queue, dashboard and route checks are run where operational surfaces change;
- the user manual is updated where a user-facing workflow changes;
- rollback or recovery notes exist for schema, integration, media or lifecycle changes.

## Module Activation Rules

A module is not production-active until it has:

- module-owned routes and settings;
- role access boundaries;
- document-template ownership boundaries where documents are created;
- source-record and numbering rules;
- relevant GAR source and visibility boundaries;
- manual coverage for real user workflows;
- validation checks in the Phase 3 suite or a module-owned release gate.

Finance Logix, HR Logix, Director Logix and future standalone modules must follow this same rule before they are treated as complete production modules.

## Rollback And Recovery Rules

- Roll back code separately from business data wherever possible.
- Preserve source record IDs, stable UIDs, audit events, media and evidence.
- Treat GAR summaries, caches and indexes as derived data that can be rebuilt from source records.
- Treat external sync cursors, tokens and webhook positions as recovery-critical integration state.
- If a release changes a lifecycle status, confirm old and new statuses can be reconciled without losing history.

## Red Flags

Stop and route the work back through stabilisation if:

- a release includes unrelated module work because it was already dirty locally;
- a module becomes visible because a route exists rather than because module subscription, role and settings ownership allow it;
- a migration, seed script, document-template change or GAR adapter is shipped without a scoped validation and rollback path;
- a test user, test client, demo invoice or seeded work item appears in a production path;
- a document template is edited from the wrong module;
- a dashboard tile count does not match the filtered list behind it;
- an external integration token is shared across modules;
- rollback would remove audit, media, evidence or finalised business records;
- Finance, HR or other deferred module code is activated before module-owned security close-out.

## Guarded By

```powershell
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\phase3_runner_contract_check.py
.\venv\Scripts\python.exe scripts\migration_integrity_check.py
.\venv\Scripts\python.exe scripts\schema_migration_contract_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\module_settings_registry_check.py
.\venv\Scripts\python.exe scripts\module_service_contract_check.py
.\venv\Scripts\python.exe scripts\app_module_settings_feed_contract_check.py
.\venv\Scripts\python.exe scripts\archive_inventory_check.py --strict
```
