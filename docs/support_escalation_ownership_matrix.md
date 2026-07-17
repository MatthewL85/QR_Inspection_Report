# Support and Escalation Ownership Matrix

Status: active support and escalation contract

Purpose: define who owns operational support, customer response, escalation and incident handoff across LogixPM modules.

This document keeps support from becoming informal or person-dependent as the platform grows. Each module can operate independently, but every live workflow must still have a clear support owner, escalation path and customer-facing response rule.

## Core Rule

Every production or pilot module must have an owning support role, an escalation path, a response expectation and a source record for support activity.

Support ownership must follow module ownership. A user should not need to guess whether an issue belongs to LogixPM, Works Logix, Contractor Logix, Members Logix, Finance Logix, HR Logix, Director Logix or GAR.

## Support Ownership Matrix

| Area | First-line owner | Escalates to | Source record |
| --- | --- | --- | --- |
| Core Platform | Super Admin / platform support | Platform owner | User, company, role, notification, audit or media record |
| Property Management Logix | Assigned PM/Admin | Super Admin / module owner | Client, unit, contract, key site info or assignment record |
| Works Logix | Assigned PM/Admin/Assistant | Works module owner / Super Admin | Member request, work order, evidence or reopen record |
| Contractor Logix | Contractor company admin | Contractor module owner / platform support | Job docket, contractor calendar, completion update or private log |
| Members Logix | Member support / assigned PM team | PM/Admin / Super Admin | Unit membership, portal invite, member request or resident record |
| Director Logix | PM/Admin governance support | Director module owner / Super Admin | Director approval, vote, governance or client record |
| Finance Logix | Finance user / finance admin | Finance module owner / Super Admin | Invoice, payment request, balance, budget or finance audit record |
| HR Logix | HR admin | HR module owner / Super Admin | Staff profile, HR record, leave or HR audit record |
| GAR AI Layer | Source module owner | GAR owner / platform owner | GAR inquiry, source adapter, answer audit or degraded-state record |
| External Integrations | Owning module admin | Platform owner / provider admin | Integration config, sync log, token audit or webhook event |

## Support Intake Rules

- Support must be linked to the source record where possible.
- A dashboard tile, notification or GAR answer is not the support source of truth.
- If support starts from a message, call or email, the handler must attach the outcome to the relevant source record.
- Contractor-only support must stay inside Contractor Logix unless the issue affects a connected Works Logix workflow.
- Finance and HR support must not be handled through general module notes if sensitive information is involved.
- GAR support must identify the source adapter or source record that produced the answer.

## Escalation Rules

Escalate when:

- a user cannot access a module they should be allowed to use;
- a user can access a module or organisation they should not be allowed to use;
- a dashboard count does not match the records behind it;
- a work order, job docket, invoice, payment request or portal invite links to the wrong organisation, client or unit;
- uploaded evidence cannot be opened by the correct role;
- an external integration stops syncing or sends duplicate records;
- GAR gives an answer that is stale, unsourced, role-inappropriate or inconsistent with the source record;
- a module is being used in pilot or production without a named support owner.

## Customer Response Rules

- Acknowledge urgent security, access or data exposure concerns before investigating non-urgent product improvements.
- Do not send sensitive personal, financial, HR, contractor-private, access/security or GAR-derived data through an ungoverned channel.
- When a support issue affects multiple modules, name the lead module and the supporting modules.
- When a support issue is caused by an external integration, record the external provider, last successful sync and current degraded state.
- When an issue is resolved, record the source record, action taken, acting user and whether GAR, external sync or a dashboard count needs rebuilding.

## Support Severity

| Severity | Meaning | Expected handling |
| --- | --- | --- |
| Critical | Data exposure, cross-organisation access, login failure for many users, production down | Immediate escalation to platform owner and affected module owner. |
| High | Core workflow blocked for a live module, evidence inaccessible, external sync broken | Same-day module owner review and workaround if possible. |
| Medium | Incorrect count, isolated workflow issue, document output defect | Triage, source-record check and planned fix. |
| Low | UI polish, wording, non-blocking usability issue | Backlog with owning module. |

## GAR Support Rules

GAR must not be treated as a support shortcut around module ownership.

For GAR issues, record:

- user role and organisation;
- GAR question or feed;
- source adapter used;
- source records cited or missing;
- answer visibility level;
- whether the source module data was correct;
- whether a degraded-state warning should have appeared.

If GAR is wrong because source data is wrong, fix the source module record. If GAR is wrong because it used the wrong source, fix the GAR adapter or visibility rule.

## Red Flags

Stop and route through stabilisation if:

- a support issue is resolved by editing database records directly;
- a contractor support issue exposes contractor-private logs to PM, member or director users;
- a Finance or HR support issue is discussed through general Works or client notes;
- a GAR answer is corrected only by editing the generated response instead of the source record or adapter;
- support relies on one person's memory rather than source records and audit history;
- a pilot or production module has no named support owner;
- a data exposure incident is treated as an ordinary UI bug.

## Guarded By

```powershell
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\notification_role_visibility_contract_check.py
.\venv\Scripts\python.exe scripts\works_access_control_check.py
.\venv\Scripts\python.exe scripts\works_evidence_audit_contract_check.py
.\venv\Scripts\python.exe scripts\gar_source_adapter_contract_check.py
.\venv\Scripts\python.exe scripts\gar_role_visibility_contract_check.py
.\venv\Scripts\python.exe scripts\app_health_feed_contract_check.py
.\venv\Scripts\python.exe scripts\support_readiness_contract_check.py
.\venv\Scripts\python.exe scripts\phase3_runner_contract_check.py
```
