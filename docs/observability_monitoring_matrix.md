# Observability and Monitoring Matrix

Status: active operational health contract

Purpose: define how LogixPM modules expose health, errors, slowdowns, queue risk, sync failures and GAR source-adapter issues without leaking private data.

## Core Rule

Every module must expose enough operational signals to show whether it is healthy, degraded or blocked, while keeping logs and dashboards scoped to the correct organisation, module and role.

Monitoring is not a substitute for audit history. Logs explain system behaviour; audit records prove business actions.

## Signal Ownership Matrix

| Area | Signals To Monitor | Owner |
| --- | --- | --- |
| Core Platform | Login health, session errors, role resolution, notification delivery, media upload health, app shell health | Core platform owner |
| Property Management Logix | Client/profile route health, unit directory health, contract alert counts, key site info rendering | Property Management Logix owner |
| Members Logix | Portal login, linked unit visibility, request submission, evidence upload, reopen request flow | Members Logix owner |
| Works Logix | Member request triage, work order creation, contractor routing, completion review, reopen queues, evidence propagation | Works Logix owner |
| Contractor Logix | Work queue, accept/reject flow, job docket creation, calendar scheduling, completion submission, contractor private logs | Contractor Logix owner |
| Finance Logix | Finance dashboard readiness, invoice intake, payment request queue, accounting sync, balance feed freshness | Finance Logix owner |
| Director Logix | Director dashboard visibility, approval/vote queues, governance document access | Director Logix owner |
| HR Logix | HR dashboard health, staff profile access, sensitive record access failures | HR Logix owner |
| GAR AI Layer | Source adapter status, blocked visibility decisions, stale source warnings, failed answer envelopes, provider availability | GAR owner |
| External Integrations | Token expiry, webhook failures, sync cursor age, import/export failures, rate limits | Owning module |

## Monitoring Rules

- Each primary module dashboard should have a lightweight health signal or count that reflects real source records, not decorative placeholder data.
- Queue counts must match the records behind the tile and exclude archived records unless the user explicitly chooses an archived view.
- Error logs must not include passwords, API keys, portal invite codes, access codes, full private notes, payment details or excessive personal data.
- GAR source adapters must report degraded or unavailable states instead of fabricating answers.
- External integration sync jobs must expose last successful sync, last failure and owning module.
- Media/evidence upload failures must be visible to the workflow owner because missing evidence changes business decisions.
- Background jobs should be idempotent or record enough state to restart safely.
- Monitoring for standalone modules must not require another Logix module to be installed.

## Degraded State Rules

| State | Meaning | Required Behaviour |
| --- | --- | --- |
| Healthy | The module can read/write its primary source records and queues are consistent | Normal dashboard and workflow behaviour |
| Degraded | A non-critical feed, sync, GAR adapter, notification or export is failing | Show a clear operational warning and keep core workflows available where safe |
| Blocked | A primary source record, route, migration, queue or permission check is failing | Stop affected workflows and route to module owner/admin |
| Stale | A feed, sync, GAR source or dashboard count is older than its expected freshness window | Show stale status and avoid presenting derived output as current |
| Recovering | A restore, replay, retry or sync recovery is in progress | Restrict risky actions until source records and audit continuity are verified |

## GAR Monitoring Rules

- GAR must expose when a source adapter is unavailable, stale or blocked by role visibility.
- GAR must not hide source-adapter failure by returning generic confidence.
- GAR answers should record source references, answer status and any blocked source classes.
- GAR monitoring must not reveal records the user cannot access.
- GAR provider configuration and failures must follow the external integration and deployment environment contracts.

## Alerting Rules

Operational alerts should be created for:

- repeated login failures or suspicious role switching;
- route errors on primary module dashboards;
- queue count mismatch between a tile and the underlying list;
- failed evidence upload or evidence propagation;
- failed contractor routing or notification delivery;
- stale external sync or webhook failures;
- GAR source adapter failure or stale source records;
- migration or deployment health failures;
- backup, restore or recovery warnings.

## Red Flags

Stop and route the work through stabilisation if any of these appear:

- a dashboard count cannot be traced to the source query behind it;
- a tile shows records that are archived, hidden or outside the user's module boundary;
- an error log includes passwords, tokens, access codes, private notes, financial details or excessive personal data;
- GAR answers while its required source adapter is failing or stale;
- external sync failures are visible only in server logs and not in the owning module;
- evidence upload failures do not alert Works Logix, Contractor Logix or the submitting user;
- monitoring uses another module's credentials, settings or route access;
- a background job retries by duplicating business records.

## Guarded By

Primary checks:

```powershell
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\app_health_feed_contract_check.py
.\venv\Scripts\python.exe scripts\app_feed_contract_check.py
.\venv\Scripts\python.exe scripts\role_dashboard_surface_check.py
.\venv\Scripts\python.exe scripts\queue_surface_contract_check.py
.\venv\Scripts\python.exe scripts\gar_source_adapter_contract_check.py
.\venv\Scripts\python.exe scripts\notification_contract_check.py
.\venv\Scripts\python.exe scripts\phase3_runner_contract_check.py
```
