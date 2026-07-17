# Module Access Matrix

Status: active security control note

Purpose: keep user access boundaries explicit as LogixPM grows into separate modules that can work independently or connect together.

This matrix is the product-level access contract. Route guards, navigation, settings registries and GAR visibility rules should move toward this shape.

## Core Rule

Users may only enter the module workspace that belongs to their role, organisation and module subscription.

A connected module may share selected records through governed services, feeds, documents or notifications. That is not the same as giving another organisation direct dashboard access.

## Role Access Matrix

| Role / User Type | Core Platform | Property Management Logix | Works Logix | Contractor Logix | Members Logix | Finance Logix | Director Logix | HR Logix | GAR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Super Admin | Full platform administration for own organisation | Full management workspace | Full management-side Works workspace | No contractor operational workspace | Management visibility only | Finance administration when subscribed | Governance visibility | HR administration when subscribed | Role-wide source-backed access |
| Admin | Organisation administration for own company | Management workspace | Management-side Works workspace | No contractor operational workspace | Management visibility only | Finance access when assigned/subscribed | Governance support | HR access only when assigned | Role-aware source-backed access |
| Property Manager | Own assigned developments and teams | Assigned management workspace | Assigned Works queues and decisions | No contractor operational workspace | Management visibility for assigned developments | Read/limited finance visibility when allowed | Governance support for assigned developments | No HR workspace unless separately assigned | Assigned-development source-backed access |
| Assistant / APM | Assigned developments and delegated queues | Assigned/delegated management workspace | Assigned/delegated triage and routing | No contractor operational workspace | Management visibility for delegated developments | Limited finance visibility only when assigned | Governance support only when assigned | No HR workspace unless separately assigned | Delegated source-backed access |
| Financial Controller | Company/user identity | Finance-related management visibility | Payment/request visibility where finance review is required | No contractor operational workspace | No member portal access unless separately a member | Finance workspace for assigned developments | Finance/governance reporting when allowed | No HR workspace unless separately assigned | Finance-scoped source-backed access |
| Contractor Owner / Admin | Contractor organisation identity | No LogixPM management workspace | Assigned Works records only through governed contractor surfaces | Contractor workspace, settings, dockets, calendar and contractor documents | No member portal access unless separately a member | Contractor payment-request visibility only for own submissions | No director workspace | Contractor staff/HR only when Contractor Logix owns it | Contractor-scoped source-backed access |
| Contractor Engineer | Contractor user identity | No LogixPM management workspace | Assigned job context only | Assigned dockets, schedule, updates and completion evidence | No member portal access unless separately a member | No finance workspace | No director workspace | Own contractor staff profile if enabled | Assigned-job source-backed access |
| Member / Owner | Own identity and portal access | No management workspace | Own requests and visible linked work status | No contractor operational workspace | Own linked units, requests, replies and documents | Own balances only when Finance Logix exposes them | No director workspace unless also director | No HR workspace | Own-unit source-backed access |
| Resident / Tenant | Own identity and portal access | No management workspace | Own requests and visible linked work status | No contractor operational workspace | Own occupancy-linked requests and visible documents | No owner finance data unless explicitly allowed | No director workspace | No HR workspace | Own-request/source-backed access |
| Director / OMC | Own identity and governance access | Governance/read surfaces for assigned development | Governance visibility and approval workflows where allowed | No contractor operational workspace | No member portal access unless separately a member | Governance finance visibility when subscribed | Director workspace | No HR workspace | Director-scoped source-backed access |
| HR Manager | Company/user identity | No management workspace unless separately assigned | No Works workspace unless separately assigned | No contractor operational workspace unless contractor-side HR | No member portal access unless separately a member | No finance workspace unless separately assigned | No director workspace | HR workspace for assigned organisation | HR-scoped source-backed access |

## Boundary Examples

- A Property Manager can see a contractor's completion evidence through Works Logix, but cannot enter the contractor's dashboard, calendar, private material logs or contractor settings.
- A Contractor can see the site, unit, contact and evidence details needed for assigned work, but cannot browse the management company's client list, Finance Logix, Members Logix or LogixPM settings.
- A Financial Controller can review finance/payment data for assigned developments, but should not become a back door into Contractor Logix or Members Logix.
- A Member can see their own units, requests, replies and visible work status, but not another owner's records or contractor-private notes.
- GAR can answer across modules only when the user already has access to the underlying source records.

## Settings Ownership

Module settings follow the same rule as dashboards:

- Core Platform owns company profile, users, organisation identity, module subscriptions and connection records.
- Property Management Logix owns management company settings and management-owned document templates.
- Works Logix owns work-order, quotation-request and management-side payment handoff settings.
- Contractor Logix owns contractor profile, job docket, quotation response, payment request, calendar, bank, insurance and contractor document-template settings.
- Members Logix owns portal, unit-membership and member/resident visibility settings.
- Finance Logix owns finance settings, finance document templates, bank/reconciliation setup and accounting integrations.
- HR Logix owns staff profile, leave, policy and HR integration settings.

## Guarded By

Primary checks:

```powershell
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\module_settings_registry_check.py
.\venv\Scripts\python.exe scripts\contractor_document_template_boundary_check.py
.\venv\Scripts\python.exe scripts\organisation_connection_boundary_check.py
.\venv\Scripts\python.exe scripts\gar_role_visibility_contract_check.py
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
```
