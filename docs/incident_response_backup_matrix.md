# Incident Response and Backup Matrix

Status: active security and recovery contract

Purpose: define how LogixPM modules protect, restore and incident-review source records, documents, media, audit trails and external sync state.

## Core Rule

Every module must know how its source records, evidence, audit logs and external sync state are backed up, restored and incident-reviewed.

Restores must preserve source references, visibility rules, audit history and finalised records. A restore must not silently overwrite signed, approved, completed, paid or closed business records.

## Backup Ownership Matrix

| Area | Backup Scope | Recovery Owner |
| --- | --- | --- |
| Core Platform | Users, roles, companies, organisation links, sessions, notifications, audit metadata and shared media metadata | Core platform owner |
| Property Management Logix | Clients, units, contracts, key site information, team assignments and site structure | Property Management Logix owner |
| Members Logix | Unit memberships, owners, co-owners, residents, portal access, member requests and member-visible evidence | Members Logix owner |
| Works Logix | Work orders, lifecycle events, contractor routing, member request conversion, reopen requests and evidence links | Works Logix owner |
| Contractor Logix | Job dockets, schedules, contractor-owned documents, completion updates, private materials/time logs and contractor calendar state | Contractor Logix owner |
| Finance Logix | Budgets, charges, invoices, balances, payments, ledgers, payment requests and accounting sync state | Finance Logix owner |
| Director Logix | Director approvals, governance records, voting decisions and director-visible document history | Director Logix owner |
| HR Logix | Staff records, HR documents, leave, reviews and staff self-service records | HR Logix owner |
| GAR AI Layer | Source references, answer metadata, recommendation metadata, prompts, role visibility checks and source adapter logs | GAR owner |
| External Integrations | OAuth tokens, API keys, webhook state, calendar feeds, mailbox intake cursors, accounting sync cursors and cloud document references | Owning module with core security support |

## Recovery Rules

- Backups must be environment-scoped, access-controlled and protected from accidental production/local mixing.
- Production recovery must not use local development data, seed data or test users.
- Restores must preserve stable UIDs, source IDs, audit IDs, media links and document references.
- Media and evidence storage must be restored with the same visibility rules as the source record.
- Archive state must survive restore; archived records must not reappear in active dashboards by default.
- External sync tokens, cursors and webhook positions must be reviewed before integrations are resumed.
- GAR indexes, summaries or cached answers must be treated as derived data; source records remain the authority.
- Each module owner must verify restored records before the module is treated as operational again.
- Recovery testing should include at least one source record with media/evidence and one cross-module link.

## Incident Response Workflow

1. Identify the issue, affected environment, module, organisation, users and source records.
2. Pause risky jobs, external syncs, webhooks, imports or GAR source adapters where needed.
3. Preserve audit logs, source records, uploaded evidence and relevant application logs.
4. Notify the correct module owner, platform owner and business/security stakeholders.
5. Fix the root cause before restoring or replaying data.
6. Restore only verified data, then check source IDs, visibility rules, media links and audit continuity.
7. Resume external integrations only after tokens, cursors and sync logs are confirmed safe.
8. Record the incident review, root cause, recovery action and follow-up guardrail.

## Module Incident Examples

| Scenario | Required Control |
| --- | --- |
| Contractor uploads completion evidence to the wrong job docket | Preserve the upload, correct the source link through an audited action and keep visibility contractor/management scoped until reviewed |
| Member request media is not propagated to Works Logix | Restore or relink evidence from the member request source record, then rerun the evidence propagation check |
| A closed work order is accidentally reopened by restore | Restore the closed state, record the correction and verify active dashboard counts exclude closed/archive records |
| Accounting sync posts duplicate supplier invoices | Pause the accounting integration, preserve sync logs and recover through Finance-owned invoice controls |
| GAR gives an answer from stale restored data | Mark GAR derived data stale, rebuild from verified source records and record source adapter review |
| Contractor calendar feed exposes another contractor's jobs | Revoke the feed, rotate the token, audit access and regenerate scoped feeds only |

## Red Flags

Stop and route the work through stabilisation if any of these appear:

- a restore overwrites a signed, approved, completed, paid or closed record;
- a backup excludes media, photos, videos or evidence needed to prove a business action;
- an incident is fixed by deleting audit logs or source history;
- production is recovered from seed data, local data or a developer machine export;
- an external sync resumes after restore without token, cursor and sync-log review;
- GAR answers from stale cached data after a restore;
- archived records reappear in active operational queues after recovery;
- a module cannot explain which records and media are required to recover its workflow.

## Guarded By

Primary checks:

```powershell
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\archive_inventory_check.py --strict
.\venv\Scripts\python.exe scripts\legacy_archive_isolation_check.py
.\venv\Scripts\python.exe scripts\migration_integrity_check.py
.\venv\Scripts\python.exe scripts\media_evidence_spine_check.py
.\venv\Scripts\python.exe scripts\works_evidence_audit_contract_check.py
.\venv\Scripts\python.exe scripts\phase3_runner_contract_check.py
```
