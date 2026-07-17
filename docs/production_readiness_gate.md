# Production Readiness Gate

Status: active production-readiness gate

Purpose: define the minimum conditions a LogixPM module, workflow or integration must satisfy before it is treated as safe for production use.

This gate sits after release/change control. A feature can be merged and still not be production-ready. Production readiness means the feature is role-safe, module-owned, recoverable, observable, documented and ready for real organisation data.

## Core Rule

Nothing is production-ready until the owning module can prove its access rules, settings ownership, source records, documents, data classification, audit trail, monitoring, rollback and user workflow are all in place.

## Readiness Levels

| Level | Meaning | Allowed use |
| --- | --- | --- |
| Prototype | Shape, UX or technical proof only | Local testing and product thinking only. |
| Review | Feature works locally and is being checked | Internal review users and seeded test data only. |
| Pilot | Controlled real-world trial with known users | Limited clients, limited modules and explicit owner approval. |
| Production | Safe for normal customer use | Live customer data, normal user access and support process active. |
| Deferred | Intentionally not active | Hidden or guarded until its owning module close-out is complete. |

## Module Readiness Checklist

Before a module or workflow becomes production-ready, confirm:

- role access is declared and enforced;
- module-owned settings exist where the module needs settings;
- document templates are owned by the module that creates the document;
- source records use stable IDs and safe human-readable references;
- data classification is understood for every user-visible field;
- GAR reads only permitted source records and reports degraded source states;
- dashboard tiles match the lists behind them;
- media, evidence and uploads attach to the record they prove;
- state changes create audit history with acting user and owning module;
- archive, retention, restore and rollback behaviour is known;
- migrations are validated and reversible or recoverable;
- seed/demo data is excluded from production activation;
- user manual coverage exists for the real workflow;
- support and incident ownership is clear.

## Module-Specific Gates

| Module | Must be true before production |
| --- | --- |
| Core Platform | Auth, roles, company identity, notifications, audit, uploads and settings shell are stable. |
| Property Management Logix | Clients, units, contracts, key site information and team assignments are source-backed and role-safe. |
| Works Logix | Member request triage, work-order routing, evidence, completion review and reopen flows are auditable. |
| Contractor Logix | Contractor-only dashboard access, job dockets, calendar, private logs, evidence and payment/quotation surfaces stay contractor-owned. |
| Members Logix | Linked units, portal invites, maintenance requests and owner/resident visibility are controlled by membership records. |
| Director Logix | Director access is limited to governance and approval records for their developments. |
| Finance Logix | Finance-owned roles, settings, document templates, GAR adapters, exports and accounting boundaries are complete before activation. |
| HR Logix | HR-owned records, sensitive visibility, settings, documents and retention rules are complete before activation. |
| GAR AI Layer | Source adapters, role visibility, answer citations, degraded states and audit metadata are complete. |
| External Integrations | Credentials, scopes, sync status, logs, revocation and fallback behaviour are owned by the using module. |

## Production Blockers

A module or workflow must stay out of production if:

- a user can enter another module or organisation through direct URL, settings, dashboard tile or document link;
- a contractor can see property-management settings, or a property-management user can enter Contractor Logix;
- a dashboard count cannot be traced to the same source records shown behind the tile;
- a workflow requires local seed data, manual database edits or debug mode;
- a document template is edited from the wrong module;
- a route is live but the module has no settings owner or support owner;
- GAR can answer from data the user cannot open directly;
- uploaded evidence is stored without a source record link;
- a finalised record can be overwritten instead of amended;
- rollback would delete source IDs, audit history, media, evidence or external sync state;
- the user manual does not explain the workflow a real user is expected to follow.

## Pilot Rules

Pilot use is allowed only when:

- the pilot organisation and module scope are named;
- seeded review data is clearly separated from real data;
- support owner and rollback owner are named;
- the pilot has explicit end conditions;
- risks are recorded in `docs/module_completion_register.md`;
- GAR and external integrations are either fully gated or explicitly excluded from the pilot.

## Sign-Off Record

For each production-ready module or major workflow, record:

- owner;
- readiness level;
- affected routes and dashboards;
- settings owner;
- document owner;
- data classes exposed;
- GAR source adapters used;
- checks run;
- known limitations;
- rollback or recovery notes;
- support owner.

The record can live in the module documentation until a dedicated release-management UI exists.

## Guarded By

```powershell
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\pilot_live_activation_contract_check.py
.\venv\Scripts\python.exe scripts\phase3_runner_contract_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\module_settings_registry_check.py
.\venv\Scripts\python.exe scripts\module_completion_register_check.py
.\venv\Scripts\python.exe scripts\module_service_contract_check.py
.\venv\Scripts\python.exe scripts\app_module_settings_feed_contract_check.py
.\venv\Scripts\python.exe scripts\support_readiness_contract_check.py
.\venv\Scripts\python.exe scripts\role_dashboard_surface_check.py
.\venv\Scripts\python.exe scripts\queue_surface_contract_check.py
.\venv\Scripts\python.exe scripts\gar_source_adapter_contract_check.py
.\venv\Scripts\python.exe scripts\archive_inventory_check.py --strict
```
