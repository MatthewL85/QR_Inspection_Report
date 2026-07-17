# Auditability Matrix

Status: active accountability control note

Purpose: define what LogixPM must record when users, modules, external integrations or GAR move a workflow forward.

Auditability is the safety layer that lets the platform grow without losing trust. A user should be able to see who acted, what source record was touched, which module owned the decision and whether GAR only recommended or a human approved.

## Core Rule

Every business action that changes state, shares data across modules, creates a document, submits evidence, sends a request, approves a workflow, rejects a workflow or exposes a record to another organisation must have an audit trail.

The audit trail must link back to the source record. It must not live only in free text, a notification message or a GAR answer.

## Required Audit Fields

Every auditable event should be able to provide:

- event ID;
- source module;
- source record type;
- source record ID;
- acting user ID;
- acting user role;
- acting organisation ID;
- affected organisation ID, where different;
- action name;
- previous state, where applicable;
- new state, where applicable;
- visibility scope;
- source IP / device context, where available;
- timestamp;
- GAR recommendation reference, where GAR influenced the action;
- human approval reference, where a decision needed approval.

## Module Audit Ownership

| Module | Owns Audit Events For | Must Not Own |
| --- | --- | --- |
| Core Platform | Login/security events, user role changes, company settings, module subscriptions, organisation connections and shared notification events | Business decisions owned by Works, Contractor, Finance, HR or Director workflows. |
| Property Management Logix | Client/development changes, unit setup, site structure, key site information and management-side assignments | Contractor-private job logs or Finance ledger events. |
| Works Logix | Member request triage, work-order creation, routing, contractor offers, returns, reopen decisions, completion review and closure | Contractor internal material/time logs, Finance invoice approval and bank/payment execution. |
| Contractor Logix | Job docket creation, acceptance/rejection, scheduling, contractor progress updates, completion submissions, private material/time logs and contractor payment requests | Work-order ownership, member portal requests or PM-side approval decisions. |
| Members Logix | Portal access, member/resident requests, replies, feedback, reopen requests and member-visible evidence | PM-only notes, contractor-private logs or owner finance data visible only to owners. |
| Finance Logix | Budgets, service charges, balances, debtor snapshots, supplier invoice intake, approvals, ledgers, payment runs and reconciliation events | Contractor job docket actions or Works triage decisions. |
| Director Logix | Director approvals, votes, governance pack review, quotation/CAPEX decisions and board acknowledgements | PM source records, contractor private logs or HR staff records. |
| HR Logix | Staff profile changes, leave, policy acknowledgements, HR documents, manager approvals and HR integrations | PM/Works/Finance records unless separately assigned through those modules. |
| GAR AI Layer | Recommendations, source citations, confidence signals and answer history | Business state changes unless a governed workflow explicitly records the human approval. |

## Cross-Module Audit Rules

When a workflow crosses modules, both sides need source references:

- Works to Contractor: Works owns the work order event; Contractor owns the job docket event.
- Contractor to Works: Contractor owns the completion submission; Works owns PM/Admin approval, return or closure.
- Works to Finance: Works owns payment readiness; Finance owns invoice intake, approval, ledger and payment events.
- Works to Members: Works owns triage and work-order state; Members owns member replies, feedback and reopen requests.
- Contractor to Finance: Contractor owns payment request submission; Finance owns payment review and payment execution.
- Director to PM/Works/Finance: Director owns governance approval; source module owns the underlying operational or finance record.
- GAR to any module: GAR owns recommendation metadata; the module owns the action taken by a human or workflow rule.

## Human Approval Rule

GAR and external integrations may prepare, suggest, extract or draft. They must not silently complete high-impact actions.

Human approval is required before:

- creating or changing a contract;
- approving or rejecting a quotation;
- approving a supplier invoice;
- posting a ledger entry;
- running a payment;
- closing or reopening a disputed work order;
- exposing restricted records to another organisation;
- changing role, module or organisation access;
- sending a statutory or compliance document.

## Immutable / Controlled Amendment Rule

Completed or signed business records should not be edited in place.

Use controlled amendment workflows for:

- signed contracts;
- approved invoices;
- completed job dockets;
- closed work orders;
- approved governance decisions;
- published compliance records.

The amendment should record the original record, the new amendment, the reason, the acting user and the approval path.

## Red Flags

Stop and review if:

- a state change does not record an acting user;
- a cross-module update has no source record ID;
- a GAR answer cannot cite source records;
- a completed or signed document can be overwritten;
- a contractor-private event is visible in PM, Members or Finance views;
- a Finance approval or payment can happen without Finance-owned audit;
- a notification is treated as the audit trail;
- an external integration writes records without source, confidence and approval metadata.

## Guarded By

Primary checks:

```powershell
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\module_service_contract_check.py
.\venv\Scripts\python.exe scripts\works_evidence_audit_contract_check.py
.\venv\Scripts\python.exe scripts\gar_source_adapter_contract_check.py
```
