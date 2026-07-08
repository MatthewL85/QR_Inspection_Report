# Module Contracts

Status: Phase 2 architecture control document

Purpose: define the operating contract for each module so LogixPM can grow as a connected ecosystem without turning into one large, tangled feature.

The source registry lives in:

```text
app/services/core/module_registry.py
```

The validation script is:

```text
scripts/module_contract_check.py
```

Route namespace boundaries are validated by:

```text
scripts/module_route_boundary_check.py
```

Module dependency boundaries are validated by:

```text
scripts/module_dependency_boundary_check.py
```

Role dashboard surface consistency is validated by:

```text
scripts/role_dashboard_surface_check.py
```

## Rule

Each module should have:

- A clear owner for its business records.
- A dashboard or entry endpoint when it is user-facing.
- Shared links back to the platform spine.
- No duplicate copy of another module's source-of-truth data.

## Current Module Contracts

| Module | Status | Entry point | Owns | Shared links |
| --- | --- | --- | --- | --- |
| Core Platform | active | Internal | Users, roles, companies, documents, audit logs | `user_id`, `company_id` |
| Client / Property Management Logix | active | `super_admin.manage_clients` | Clients, development structure, team assignments | `company_id`, `client_id`, `unit_id`, `user_id` |
| Unit / Property Asset Spine | active | `unit_bp.list` | Units, block/core/area, occupancy metadata | `client_id`, `unit_id`, `member_id` |
| Contract Manager | active | `super_admin_contracts.contracts_overview` | PSRA contracts, renewals, contract documents | `client_id`, `template_version_id`, `user_id` |
| Finance Logix | shell | `finance.dashboard` | Budgets, service charges, invoices, payments, arrears | `client_id`, `unit_id`, `member_id`, `work_order_id` |
| Works Logix | partial | `super_admin.work_orders` | Work orders, work order lifecycle events, completion evidence, completion reviews, reopen requests | `work_order_id`, `client_id`, `unit_id`, `contractor_id`, `member_request_id`, `completion_id`, `reopen_request_id`, `user_id` |
| Members Logix | shell | `members.dashboard` | Members, residents, unit memberships, member requests, member notifications, mobile member app shell | `client_id`, `unit_id`, `member_id`, `resident_id`, `user_id` |
| Contractor Logix | shell | `contractor.contractor_dashboard` | Contractor profiles, teams, compliance, performance, contractor notifications, mobile contractor app shell | `contractor_id`, `company_id`, `work_order_id`, `user_id` |
| HR Logix | foundation | Internal | Employee profiles, leave records, employment documents, performance reviews, staff notifications, mobile staff app shell | `user_id`, `company_id` |
| Director Logix | shell | `director.dashboard` | Director visibility, approvals, governance views | `client_id`, `unit_id`, `member_id`, `user_id` |
| Assistant Workspace | partial | `assistant.dashboard` | Assigned follow-up, support queue, assigned Works routing, Assistant Manager cover queue | `client_id`, `unit_id`, `user_id`, `work_order_id`, `member_request_id`, `contractor_id` |
| Admin Portal | partial | `admin_portal.dashboard` | Admin operations, support views and company Works queue access | `client_id`, `unit_id`, `user_id`, `company_id`, `work_order_id`, `member_request_id`, `contractor_id` |
| GAR AI Layer | foundation | `super_admin.gar_insights` | Context summaries, risks, recommendations, explainability | source references, visibility rules, audit ids, work order lifecycle event ids |

## Status Meaning

| Status | Meaning |
| --- | --- |
| active | Current production-facing area with real workflows |
| partial | Some real functionality exists, but the full module is not complete |
| shell | Clean entry point exists; deep module workflows are still future work |
| foundation | Shared intelligence or platform layer exists but is not a standalone workflow |

## Build Rule For New Features

Before adding a feature, decide:

1. Which module owns the business record?
2. Which core IDs link it to the platform spine?
3. Which other modules may read it?
4. Which roles may see it?
5. What GAR can summarise, and what GAR must not overwrite?

If the answer crosses module boundaries, use a service/helper and IDs. Do not copy the same business fact into another module.

## Dependency Rule

Modules should be connected through declared services, shared IDs, source-backed feeds and governed workflow actions.

Do not connect modules by importing one module's routes into another module. Routes are presentation and workflow entry points; they are not integration APIs.

Do not import services from models. Models define persistence shape and relationships. Services own workflow orchestration.

Allowed cross-module service dependencies must be explicit. The dependency check currently permits only known service-level links such as:

- GAR reading Core, Contract Manager, Works Logix and Members Logix source services.
- Works Logix asking GAR for relevant history and work-order intelligence.
- Members Logix reading Works Logix context for member-visible work status.
- Core app/home feeds reading GAR capabilities.
- Dashboard summaries reading Contract Manager metrics.

If a new module needs another module's data, add a source-backed service or feed in the owning module and declare the dependency. Do not query another module's private internals from a route.

## Phase 3 Cross-Module Workflow Contract

The first real cross-module workflow is the Works lifecycle:

```text
Members Logix request
        ↓
Works Logix triage and route by PM/Admin/Assistant
        ↓
Contractor Logix completion
        ↓
Members Logix feedback / reopen request
        ↓
PM/Admin review and close or return
        ↓
GAR AI context and recommendations
```

Source-of-truth rule:

- Works Logix owns `work_orders`, `work_order_lifecycle_events`, completion records and reopen requests.
- Members Logix owns member/resident identities, requests and the member-facing notification experience.
- Contractor Logix owns contractor identity, compliance, contractor queue experience and contractor notifications.
- Assistant Workspace can route assigned developments. Assistant Manager / Master Assistant roles can access the company-wide cover queue so urgent requests do not stall when assigned staff are unavailable.
- GAR AI reads the workflow through source references and visibility rules. It may summarise risk and recommend next action, but it must not overwrite the business record.

The persisted lifecycle event record is the hand-off trail between modules. Other modules should link to it by `work_order_id` and related IDs rather than creating their own separate history.

Lifecycle events must record the acting user and access context where a human routes work, such as `assigned_assistant`, `assigned_property_manager`, `assistant_manager_cover` or `super_admin`. This keeps holiday cover and override access visible to GAR, audits and future management reports.

## Mobile/App Requirement

Members Logix, Contractor Logix and HR Logix must be mobile-first and app-ready.

- Members Logix needs touch-friendly owner, tenant and resident workflows, notification hooks, secure unit/member scoping and no separate mobile-only source of truth.
- Contractor Logix needs field-ready job queues, assigned work visibility, status updates, evidence capture/upload, completion submission and notification hooks.
- HR Logix needs staff self-service readiness for profile, policy, leave, notifications and future review workflows.

The current web portals should be built so they can become PWA/native apps later without rebuilding the business records.

## Verification

Run:

```text
.\venv\Scripts\python.exe scripts\module_contract_check.py
```

Expected result:

```text
Module contract check
- Module contracts declared: 13
- Dashboard endpoints checked: 11
- GAR inquiry endpoints checked: 8

PASSED
```

Module dependency boundary verification:

```text
.\venv\Scripts\python.exe scripts\module_dependency_boundary_check.py
```

This confirms models do not import services or routes, services do not import routes, and cross-module service dependencies remain declared rather than accidental.

GAR source-adapter contract verification:

```text
.\venv\Scripts\python.exe scripts\gar_source_adapter_contract_check.py
```

This confirms every query-ready GAR capability has a declared source adapter,
and that Finance Logix debtor, budget, arrears, invoice, payment and ledger
questions remain behind the not-query-ready gate until Finance owns validated
query services.

It also verifies ready GAR source-query envelopes return structured source
references with a model name, record id field and source field list. This keeps
future GAR answers traceable back to the owning module record.

GAR context verification:

```text
.\venv\Scripts\python.exe scripts\gar_context_check.py
```

This confirms the GAR layer can read portfolio, client and unit context from the shared platform spine.

GAR role-visibility verification:

```text
.\venv\Scripts\python.exe scripts\gar_role_visibility_contract_check.py
```

This confirms external-facing roles do not receive management-only, finance,
team-directory, contract or governance capabilities through GAR where those
roles are not permitted. It also checks contractor/member visibility flags stay
privacy-safe.

GAR inquiry API verification:

The module contract check also confirms the role-scoped GAR inquiry endpoints exist:

```text
super_admin.gar_inquiry
admin_portal.gar_inquiry
property_manager.gar_inquiry
assistant.gar_inquiry
finance.gar_inquiry
director.gar_inquiry
contractor.gar_inquiry
members.gar_inquiry
```

These endpoints are read-only and return the same source-backed inquiry envelope used by the Ask GAR dashboard panels. They are the protected app/mobile contract for future GAR chat surfaces.

Phase 3 Works lifecycle verification:

```text
.\venv\Scripts\python.exe scripts\works_lifecycle_flow_check.py
```

This creates a temporary Members -> Works -> Contractor -> feedback -> review -> reopen workflow, verifies lifecycle events and GAR work order context, then removes the temporary records.

App/mobile feed contract verification:

```text
.\venv\Scripts\python.exe scripts\app_feed_contract_check.py
```

This confirms the app-ready GAR, Works, Members, Contractor and Notification feed endpoints exist and remain read-only. Future mobile/PWA clients should use these feeds for display state and call governed workflow routes for actions.

Governed workflow action verification:

```text
.\venv\Scripts\python.exe scripts\workflow_action_contract_check.py
```

This confirms lifecycle actions such as converting member requests, assigning
contractors, contractor updates, member feedback, reopen requests and
notification mark-read actions remain POST-only. Display feeds and dashboard
links should never mutate the source records.

Notification contract verification:

```text
.\venv\Scripts\python.exe scripts\notification_contract_check.py
```

This confirms notification workflow-stage labels, audience labels, action
classification and source-target payloads stay stable across Works Logix,
Members Logix, Contractor Logix, Contract Manager, GAR and future app surfaces.

Navbar notification contract verification:

```text
.\venv\Scripts\python.exe scripts\navbar_notification_contract_check.py
```

This confirms the shared platform navbars use the Notification Centre service
for unread counts and recent items, link back to the governed source routes and
keep mark-all-read as a POST-only action.

Role dashboard notification contract verification:

```text
.\venv\Scripts\python.exe scripts\role_dashboard_notification_contract_check.py
```

This confirms Super Admin, Admin, Property Manager, Assistant, Finance,
Director, Contractor and Members dashboards all use the shared source-backed
Notification Action Queue instead of role-specific notification widgets.

Works command-centre contract verification:

```text
.\venv\Scripts\python.exe scripts\works_command_centre_contract_check.py
```

This confirms the Works Logix management command-centre payload keeps stable
operational queues, stats, filters, feed queues and GAR context for web,
dashboard and future app clients.

Works Evidence and Audit Pack contract verification:

```text
.\venv\Scripts\python.exe scripts\works_evidence_audit_contract_check.py
```

This confirms Works Logix keeps one source-backed audit pack for contractor
completion evidence, Members Logix request/feedback/reopen evidence, lifecycle
review cycles, Assistant Manager cover context and GAR source references.

Role dashboard attention contract verification:

```text
.\venv\Scripts\python.exe scripts\role_dashboard_attention_contract_check.py
```

This confirms Super Admin, Admin, Property Manager and Assistant dashboards surface the
same Works/GAR attention model and link back to the governed Works Logix command
centre or Repeated Returns review queue instead of becoming separate workflow
engines.
