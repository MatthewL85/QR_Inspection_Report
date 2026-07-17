# Data Retention and Deletion Matrix

Status: active data-governance control note

Purpose: define how LogixPM handles deletion, archive, retention and restoration across independent modules.

The platform should protect business history without keeping operational screens cluttered. Users need clean active views, but source records, audit trails and completed documents must remain available where law, governance, evidence, finance or operational history require them.

## Core Rule

Default to archive, deactivate, supersede or controlled amendment for business records.

Permanent deletion should be limited to disposable drafts, accidental setup records with no downstream links, test data, temporary uploads and records that a lawful retention policy says must be erased.

## Deletion Types

| Type | Meaning | Use For | Must Record |
| --- | --- | --- | --- |
| Soft archive | Hide from active views while retaining the record | Completed contracts, old work orders, inactive clients, outdated documents | Actor, reason, date, original status and restore path. |
| Deactivation | Keep record but prevent active login/use | Users, contractors, members, staff profiles, suppliers | Actor, reason, date and reactivation rules. |
| Superseded record | Replace current version while preserving old version | Key site info, compliance documents, templates, policies | Version chain, actor, reason and effective date. |
| Controlled amendment | Add a correction without overwriting the original | Signed contracts, approved invoices, closed work orders, completed job dockets | Original record, amendment record, approval path and audit reference. |
| Hard delete | Permanently remove data | Temporary test data, failed uploads, empty drafts, lawful erasure cases | Actor, reason, legal basis and confirmation that no protected links exist. |

## Module Retention Rules

| Module | Archive / Retain | Hard Delete Only When |
| --- | --- | --- |
| Core Platform | Users, roles, companies, module subscriptions, organisation connections, notifications and audit references | A duplicate/test setup has no business links or a lawful erasure workflow approves removal. |
| Property Management Logix | Clients, developments, units, key site info, contracts, assignments and governance history | A setup record was created in error and has no units, contracts, members, works, finance or document links. |
| Works Logix | Member requests, work orders, lifecycle events, evidence, reopen decisions and closure history | A draft/test request has no attached evidence, no member communication and no contractor routing. |
| Contractor Logix | Job dockets, schedules, completion evidence, private material/time logs, payment requests and quotation responses | A standalone draft docket was abandoned before scheduling, evidence, completion, payment or external sharing. |
| Members Logix | Portal memberships, owner/resident links, requests, replies, feedback and reopen requests | A portal invite or draft link is unused, expired and has no verified access history. |
| Finance Logix | Budgets, charges, balances, invoices, ledger, payments, debtor snapshots and reconciliation history | A draft finance intake was rejected before approval, posting, payment or statutory retention. |
| Director Logix | Board packs, votes, quotation/CAPEX decisions, governance approvals and acknowledgements | A draft pack or test vote has no issued document, approval dependency or audit requirement. |
| HR Logix | Staff profiles, contracts, leave, policy acknowledgements, HR documents and HR audit history | A draft profile or imported staging record was never activated and has no HR history. |
| GAR AI Layer | Source references, answer history, recommendations, confidence and visibility decisions | A generated draft has no user-facing answer, workflow action or audit dependency. |

## Protected Records

Do not hard delete without a formal retention/legal workflow:

- signed contracts;
- approved invoices;
- payment records;
- ledger/reconciliation records;
- completed job dockets;
- closed work orders with evidence;
- member/resident requests with replies or evidence;
- key site information versions used by contractors;
- compliance documents;
- director votes or approvals;
- HR records with employment history;
- audit logs and source references.

## Active View Rule

Archive should remove noise from active dashboards without deleting history.

Examples:

- Contract Manager active tiles must exclude archived contracts unless the user chooses an archived view.
- Contractor Work Queue active tiles should separate assigned, active, submitted, returned, invoice-ready and closed work.
- Works Logix command centre should show one selected queue list at a time, not every archive/closed list by default.
- Members Logix should show current requests first but keep closed/reopened history accessible.
- Finance Logix should keep posted records out of editable draft queues while retaining searchable audit history.

## Restore Rule

If a record can be archived, the system should define whether it can be restored.

Restoration must record:

- who restored it;
- why it was restored;
- previous archived status;
- new active status;
- affected module;
- any downstream warnings.

Some records should not be restored directly. Signed, posted, approved or completed records should usually be amended or renewed instead.

## GAR Rule

GAR may use archived, closed or superseded records only when the current user has permission to view that history.

GAR must clearly distinguish:

- active/current records;
- archived records;
- superseded versions;
- closed/completed records;
- draft/test records.

GAR should not treat an archived record as active operational work.

## Red Flags

Stop and review if:

- a delete action removes a record with source links, evidence, payments, approvals or notifications;
- active dashboard counts include archived records by default;
- an archived record can be edited as if it is current;
- a completed document is overwritten rather than superseded or amended;
- a user is deleted instead of deactivated while audit history exists;
- test cleanup scripts can target real non-test data;
- GAR uses archived records without labelling them as archived.

## Guarded By

Primary checks:

```powershell
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\audit_retention_contract_check.py
.\venv\Scripts\python.exe scripts\archive_inventory_check.py --strict
.\venv\Scripts\python.exe scripts\legacy_archive_isolation_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\works_evidence_audit_contract_check.py
```
