# GAR Visibility Matrix

Status: active AI visibility control note

Purpose: define how GAR can work across LogixPM modules while respecting role, organisation, module and source-record boundaries.

GAR is intended to become the intelligence layer across the ecosystem. It can summarise, recommend, compare, detect risk and answer questions, but it must not bypass module permissions or become the source of truth.

## Core Rule

GAR may only answer from source records the current user is allowed to access.

If a user cannot open the underlying record through the relevant module, GAR must not reveal its details. GAR can say that it has no visible source-backed information for that question.

## Source-Backed Answer Rule

Every GAR answer should be able to point back to:

- source module;
- source record type;
- source record ID;
- user role and organisation scope;
- visibility decision;
- generated answer or recommendation;
- audit reference.

This allows GAR to become powerful without becoming opaque.

## Role Visibility Matrix

| Role / User Type | GAR Can Use | GAR Must Not Reveal |
| --- | --- | --- |
| Super Admin | Organisation-wide records for subscribed modules, platform health, module gaps, governance and operational risk | Another organisation's data unless connected and explicitly visible. |
| Admin | Management records for their organisation, assigned modules, Works queues, clients, units, contracts and settings context | Contractor-private logs, unrelated organisations, HR records without HR rights. |
| Property Manager | Assigned developments, units, Works lifecycle, key site info, contractor-visible completion evidence, assigned communications | Other PM portfolios, contractor-private material/time logs, finance records beyond allowed scope. |
| Assistant / APM | Delegated developments, request triage, Works routing, scheduled tasks and assigned follow-ups | Non-delegated developments, contractor-private logs, restricted finance/HR records. |
| Financial Controller | Finance-visible client/unit balances, debtors, budgets, payment requests and invoice records for assigned developments | Contractor dashboards, member-private messages, HR records, non-assigned finance data. |
| Contractor Owner / Admin | Assigned work orders, own job dockets, contractor calendar, contractor payment requests, own staff/engineer records where enabled | Management company client lists, Finance Logix workspace, Members Logix private records, other contractors' records. |
| Contractor Engineer | Assigned job dockets, schedule, permitted site information, own updates and completion evidence | Contractor company-wide finance unless allowed, management dashboards, member records not needed for the job. |
| Member / Owner | Own linked units, own requests, visible work status, owner-visible documents and approved finance balances when exposed | Other owners' details, contractor-private logs, management notes, director-only material. |
| Resident / Tenant | Own occupancy-linked requests, visible work status, replies and permitted documents | Owner finance data, other residents' records, management-only decisions. |
| Director / OMC | Assigned development governance, board packs, quotation/CAPEX approval context, visible finance/Works summaries | Contractor-private logs, unrelated developments, HR records. |
| HR Manager | HR-owned staff records, policies, leave and HR alerts for assigned organisation | PM/Works/Finance/Member records unless separately assigned. |

## Module Source Rules

| Source Module | GAR Can Summarise | Guardrail |
| --- | --- | --- |
| Core Platform | Users, roles, companies, module subscriptions, notifications and audit references | Do not expose admin/security details to non-admin roles. |
| Property Management Logix | Clients, developments, units, contracts, key site info and assignments | Respect assigned development and organisation scope. |
| Works Logix | Requests, triage, work orders, routing, completion reviews and reopen patterns | Respect member, contractor and management visibility partitions. |
| Contractor Logix | Assigned work, job dockets, contractor updates, calendar and payment requests | Do not expose contractor-private material/time logs outside Contractor Logix. |
| Members Logix | Linked units, member requests, replies and reopen requests | Keep owner/resident visibility separate. |
| Finance Logix | Budgets, balances, arrears, debtor summaries, supplier invoices and payment readiness | Finance answers require finance role/subscription and assignment checks. |
| Director Logix | Governance packs, approvals, votes and board summaries | Director scope is by development/board assignment. |
| HR Logix | Staff profiles, leave, HR documents and HR notifications | HR data must remain HR-scoped. |

## Recommendation Rule

GAR may recommend an action, but workflow authority stays with the module:

- Works Logix approves, returns or closes work orders.
- Contractor Logix schedules and completes job dockets.
- Finance Logix approves invoices, posts ledger entries and runs payments.
- Director Logix records governance approvals and votes.
- HR Logix owns HR actions.

GAR should explain the source signals behind a recommendation and whether the recommendation is low, medium or high confidence.

## Red Flags

Stop and review if:

- GAR answers from free text without a source record reference;
- GAR exposes contractor-private notes to PM/Admin/Member users;
- GAR exposes owner finance data to residents;
- GAR uses a module connection as permission to reveal all connected organisation data;
- GAR creates or mutates business records without a human approval path or workflow rule;
- GAR summaries cannot be audited back to source records.

## Guarded By

Primary checks:

```powershell
.\venv\Scripts\python.exe scripts\gar_role_visibility_contract_check.py
.\venv\Scripts\python.exe scripts\gar_source_adapter_contract_check.py
.\venv\Scripts\python.exe scripts\gar_inquiry_endpoint_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
```
