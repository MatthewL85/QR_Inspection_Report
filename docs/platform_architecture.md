# LogixPM Platform Architecture

Status: Phase 1 architecture control document

Purpose: define the shared platform spine so LogixPM can grow as separate modules that can also work together through common source-of-truth records.

## Architecture Principle

LogixPM should not be built as disconnected features. Each Logix module should own its own workflows, screens, services and rules, while sharing a small number of core platform records.

The core records are the data spine. Modules should link to them instead of copying them.

## Core Platform Spine

These records sit underneath every module:

| Area | Source | Purpose |
| --- | --- | --- |
| Users, roles and permissions | `app/models/core` | Identity, access control, module permissions and team access |
| Companies and organisations | `app/models/onboarding` | Management company, contractor company and organisation setup |
| Clients and developments | `app/models/client/client.py` | Development/company record managed by the platform |
| Blocks, cores and units | `app/models/members/unit.py` | Physical asset spine used by Members, Works, Finance and GAR |
| Members and residents | `app/models/members` | Owners, co-owners, residents, tenants and unit relationships |
| Documents and media | `app/models/core/document.py`, `app/models/core/media_file.py` | Shared evidence, lease, compliance and workflow files |
| Audit logs | `app/models/audit`, `app/models/core/audit.py` | Accountability, change history and GAR review trace |
| Notifications and communication | `app/models/core/notification.py`, `app/models/communication` | Cross-module alerts and external communication logs |

## Organisation Identity And Connections

Each organisation/company must have a platform-owned `organisation_uid`. This is the permanent identity for the organisation across LogixPM, Contractor Logix, Members Logix, Finance Logix, HR Logix and GAR.

Separate module purchases should be represented by `ModuleSubscription` records. A company can therefore run only the modules it has enabled, while still using the same core identity if more modules are added later.

When two organisations need to work together, such as a management company and a contractor company, they should connect through a governed `OrganisationConnectionInvite` and accepted `OrganisationConnection`. Email addresses can be used for notification and invitation delivery, but email must not be the source-of-truth link between organisations.

Organisation connections define which records may be shared between modules. For example, Works Logix can offer a work order to a connected contractor organisation without copying the contractor's company profile into the management company's tenant.

Works Logix work orders should store `organisation_connection_id` when a contractor is routed through an accepted organisation connection. This gives Contractor Logix, GAR and future Finance Logix a governed company-to-company link for the job docket, updates, completion evidence and future invoice readiness.

Contractor profiles should have their own `company_id` link to the contractor organisation identity. Works Logix can then route through a real company-to-company connection instead of inferring the contractor organisation from user email or free-text contractor names.

GAR must respect these same connection boundaries. It may summarise connected records only when the user, company, module subscription and organisation connection allow that visibility.

## Module Layer

Each module should be able to operate independently, but should use shared IDs to connect to the rest of the platform:

| Module | Primary ownership | Shared links |
| --- | --- | --- |
| Client / Property Management Logix | Client setup, assignments, contracts, site structure | `company_id`, `client_id`, `unit_id`, `user_id` |
| Members Logix | Owners, co-owners, tenants, resident requests, member visibility | `member_id`, `resident_id`, `unit_id`, `client_id`, `user_id` |
| Works Logix | Work orders, lifecycle events, quote routing, contractor assignment, completion evidence and reopen reviews | `work_order_id`, `client_id`, `unit_id`, `contractor_id`, `member_request_id`, `user_id` |
| Finance Logix | Budgets, service charges, invoices, payments, arrears and reports | `client_id`, `unit_id`, `invoice_id`, `work_order_id`, `company_id` |
| Contractor Logix | Contractor profile, teams, compliance, performance and jobs | `contractor_id`, `company_id`, `work_order_id`, `user_id` |
| Director Logix | Director visibility, governance and approvals | `client_id`, `member_id`, `unit_id`, `user_id` |
| HR Logix | Internal staff profiles, leave, reviews, salary and policy records | `user_id`, `company_id` |
| Contract Manager | PSRA contracts, renewals, alerts, fee increases and governed documents | `client_id`, `template_version_id`, `user_id` |
| CAPEX / Asset Planning | Capital projects, approvals and contractor responses | `client_id`, `company_id`, `unit_id`, `user_id` |
| GAR / AI Layer | Cross-module intelligence, risk, governance and recommendations | Reads from all source-of-truth records, stores context and decisions |

## Current State

The model layer is already broadly modular. Models are separated into folders such as:

- `app/models/core`
- `app/models/client`
- `app/models/members`
- `app/models/works`
- `app/models/finance`
- `app/models/contractor`
- `app/models/contracts`
- `app/models/hr`
- `app/models/audit`

The route layer is partly modular but still has a strong Super Admin grouping. This is acceptable for the current build stage, but it should be cleaned gradually as each module becomes mature.

Current registered route groups include:

- `auth`
- `settings`
- `super_admin`
- `property_manager`
- `contractor`
- `director`
- `tenant`
- `unit_bp`
- `client_key_info`
- `super_admin_contracts`
- `super_admin_simple_contracts`
- `super_admin.organisation_connections`

## Target Shape

Each major module should eventually follow this pattern:

```text
app/models/<module>
app/routes/<module>
app/services/<module>
app/templates/<module>
tests/<module>
```

Shared functionality should stay in:

```text
app/models/core
app/services/core
app/templates/shared
```

GAR should sit above the modules as an intelligence layer, not as a replacement for module ownership.

Members Logix, Contractor Logix and HR Logix have an additional product requirement: they must remain mobile-first and app-ready.

- Members Logix should work naturally for owners, tenants and residents on phones, with a responsive/PWA-capable portal and future native app support.
- Contractor Logix should work naturally in the field, with app-ready job queues, status updates, evidence upload, notifications and completion workflows.
- HR Logix should support staff self-service from mobile devices, including profile, policy, leave, notification and future review workflows.

Any later native apps should use the same shared source-of-truth records and permission model rather than separate mobile data stores.

The current operating module contracts are recorded in:

```text
docs/module_contracts.md
app/services/core/module_registry.py
scripts/module_contract_check.py
scripts/module_dependency_boundary_check.py
```

The user-facing operating manual is recorded separately in:

```text
docs/manual/index.md
docs/manual/
```

Architecture documents explain how the system is built. The manual explains how each role uses the platform.

Phase 3 cross-module readiness is checked by:

```text
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py
```

Active route namespace boundaries are checked by:

```text
.\venv\Scripts\python.exe scripts\module_route_boundary_check.py
```

This helps each module stay independently navigable while still connecting
through shared IDs and services.

Service dependency boundaries are checked by:

```text
.\venv\Scripts\python.exe scripts\module_dependency_boundary_check.py
```

This protects the platform from hidden coupling by confirming models stay persistence-only, services do not import routes, and cross-module service dependencies are explicitly declared.

## Non-Negotiable Source-of-Truth Rules

1. A unit belongs to one client/development through `client_id`.
2. Work orders must link back to the relevant client and, where applicable, unit.
3. Finance records must link back to client and unit where unit-level finance applies.
4. Members, co-owners, residents and tenants must link through unit/member/resident relationships.
5. Contractors must be linked through contractor/company/user records, not free text only.
6. GAR may summarise and recommend, but it should not become the sole source of business data.
7. Documents and evidence should be linked to the thing they prove, such as a unit, work order, contract, invoice, contractor, client or member.
8. Completed legal or governed documents should be immutable unless a controlled amendment or renewal workflow is used.
9. Cross-module workflow history should be recorded once in the owning module, then exposed through services and role-aware views.
10. Organisations must connect through `organisation_uid`, module subscriptions and governed organisation connections, not email addresses or duplicated company records.
11. GAR must treat organisation connections as visibility boundaries for connected-company intelligence.

## Phase 1 Outcome

This document defines the platform spine. The next phase should use it to review each module boundary and remove confusion from legacy routes/templates without breaking working behaviour.
