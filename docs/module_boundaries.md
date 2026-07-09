# Module Boundaries

Status: Phase 1 architecture control document

Purpose: define what each module owns, what it can read, and what it should not duplicate.

## Core Platform

Owns:

- User identity
- Roles and permissions
- Company and organisation setup
- Shared documents and media
- Audit logs
- Notifications
- Shared UI shell and navigation rules

Should not own:

- Work order business logic
- Finance calculations
- Member-only workflows
- Contractor performance calculations

Key files:

- `app/models/core`
- `app/models/onboarding`
- `app/models/audit`
- `app/models/communication`
- `app/routes/auth`
- `app/routes/settings`

## Client / Property Management Logix

Owns:

- Client/development profile
- Development structure
- Client assignment to PM, FC and assistant
- Contract and assignment summary
- Unit generation trigger
- Client-level governance, compliance and key site information

Can read:

- Users for team assignment
- Units for client profile display
- Contracts for contract summary
- Works and finance summary counts

Should not duplicate:

- Owner data
- Resident/tenant data
- Finance ledgers
- Work order history

Key files:

- `app/models/client/client.py`
- `app/routes/super_admin/client`
- `app/services/unit_generation_service.py`

## Unit / Property Asset Spine

Owns:

- Unit identity
- Block/core/area structure
- Unit status
- Occupancy status metadata
- Service charge metadata hooks
- GAR unit context hooks

Can read:

- Client/development
- Member ownership
- Resident occupancy
- Works summary
- Finance summary

Should not duplicate:

- Client profile fields
- Owner profiles
- Resident profiles
- Full finance transactions

Key files:

- `app/models/members/unit.py`
- `app/routes/unit.py`
- `app/services/unit_service.py`

## Members Logix

Owns:

- Member and owner records
- Co-owner details
- Correspondence addresses
- Resident and tenant profiles
- Unit membership history
- Member maintenance requests
- Member portal visibility rules
- Member/resident notification experience
- Future mobile app/PWA member shell

Can read:

- Unit details
- Client/development identity
- Work order status visible to that member/resident
- Finance balances visible to that member/owner

Should not duplicate:

- Unit records
- Work order records
- Finance ledgers

Key files:

- `app/models/members/member.py`
- `app/models/members/resident.py`
- `app/models/members/unit_membership.py`
- `app/models/maintenance/maintenance_request.py`

Mobile / app rule:

- Members Logix must be designed mobile-first because owners, tenants and residents will often use it from a phone.
- The web version should remain PWA-ready, with responsive layouts, touch-friendly actions, offline-friendly future potential and notification hooks.
- Future native app work should consume the same Members Logix routes/services or a dedicated API layer. It should not create a separate mobile-only source of truth.
- Member, tenant and resident visibility must remain compartmentalised by `client_id`, `unit_id`, `member_id`, `resident_id` and `user_id`.

## Works Logix

Owns:

- Work order lifecycle
- Work order lifecycle events and cross-module hand-off trail
- Contractor routing
- Quote request/response workflow
- Completion evidence
- Completion review outcome
- Reopen requests
- Work order policy/settings
- Contractor performance linkage

Can read:

- Unit location and occupancy access data
- Client/development details
- Contractor details
- Member maintenance request source

Should not duplicate:

- Contractor company master data
- Owner profiles
- Finance invoice ledgers

Key files:

- `app/models/works/work_order.py`
- `app/models/works/work_order_lifecycle_event.py`
- `app/models/works/work_order_completion.py`
- `app/models/works/work_order_reopen_request.py`
- `app/services/works/workflow_service.py`
- `app/services/work_order_reopen_service.py`

Cross-module workflow rule:

- A member or resident request can become a Works Logix work order, but Members Logix still owns the original member request record.
- Assistants may triage and route work orders for their assigned developments only.
- Assistant Manager / Master Assistant roles may use a company-wide cover queue for operational continuity when assigned PMs or assistants are unavailable.
- Contractor Logix may update assigned work order status and submit completion evidence, but Works Logix owns the work order lifecycle state.
- Members Logix may show visible open/closed status, feedback prompts and reopen requests, but it should not duplicate the work order history.
- GAR should read lifecycle events with source references and visibility rules, then recommend action without becoming the source record.

## Contractor Logix

Owns:

- Contractor profile
- Contractor teams
- Contractor compliance
- Contractor performance
- Contractor messages/schedules
- Contractor notifications
- Future mobile app/PWA contractor shell

Can read:

- Assigned work orders
- Required site or unit access information within privacy rules
- Compliance requirements

Should not duplicate:

- Work order source records
- Finance payment records
- Client master records

Key files:

- `app/models/contractor`
- `app/routes/contractor.py`

Mobile / app rule:

- Contractor Logix must be mobile-first because contractors will complete most work in the field.
- The contractor workflow should be PWA/app-ready for assigned job queues, directions/access notes, status updates, completion notes, evidence upload, return requests and notifications.
- Future native app work should consume the same Works Logix and Contractor Logix records. It should not create a separate contractor-only work order database.
- Contractor visibility must remain scoped to assigned `work_order_id`, `contractor_id`, `company_id` and `user_id`.

## Finance Logix

Owns:

- Budgets
- Service charges
- Invoices
- Payments
- Debtors and creditors
- Arrears
- Ledgers and reports
- Finance audit history

Can read:

- Client/development
- Unit
- Member/owner relationship where billing requires it
- Work order and contractor references for supplier invoices

Should not duplicate:

- Unit ownership records
- Work order lifecycle state
- Contractor master profile

Key files:

- `app/models/finance`
- `app/models/finance/invoice.py`
- `app/models/finance/service_charge.py`
- `app/models/finance/arrears.py`

## Contract Manager

Owns:

- PSRA contracts
- Contract renewal alerts
- Fee increase tracking
- Governed contract documents
- Contract archive/immutability workflow
- GAR contract recommendation fields

Can read:

- Client/development data
- Company profile
- User/team assignment
- Contract templates

Should not duplicate:

- Client master profile
- Finance ledger records

Key files:

- `app/models/contracts/client_contract.py`
- `app/routes/super_admin/contracts`
- `app/services/contract`

## Director Logix

Owns:

- Director view of governance
- Director-specific approvals and visibility
- Director area/client assignments

Can read:

- Client/development
- Units
- Members and residents where permitted
- Works and finance summaries where permitted
- GAR governance summaries

Should not duplicate:

- Member/owner records
- Finance transactions
- Work orders

Key files:

- `app/models/director`
- `app/routes/director.py`

## HR Logix

Owns:

- Internal employee profile
- Leave and policy records
- Employment documents
- Performance and director/management reviews
- Staff notifications
- Future mobile app/PWA staff self-service shell

Can read:

- User identity
- Company assignment

Should not duplicate:

- User login credentials
- Role permission records

Key files:

- `app/models/hr`
- `app/services/user_profile_service.py`

Mobile / app rule:

- HR Logix should be app-ready for staff self-service, including profile updates, policy acknowledgement, leave requests, notifications and future review workflows.
- HR should link to the core user record by `user_id`; it must not duplicate login identity, role assignment or permission control.
- Future native app work should use the same HR Logix services/API layer and shared user/company source of truth.
- HR visibility must remain compartmentalised by `company_id`, role and the relevant employee `user_id`.

## GAR / AI Layer

Owns:

- Cross-module context building
- Risk summaries
- Governance recommendations
- AI/GAR review metadata
- Explainability records
- GAR chat/readiness status

Can read:

- All relevant module records according to permissions and privacy rules

Should not own:

- The core business record itself
- Legal source documents without document linkage
- Manual override authority without audit trail

Key files:

- `app/services/gar_parser.py`
- `app/services/gar`
- GAR fields across models

## Boundary Rule

If a feature needs data from another module, it should link by ID and read through a service/helper. It should not copy and maintain a second version of the same business fact.

## Settings Boundary Rule

Settings follow the same ownership model as operational data.

- Core Platform owns shared settings foundations: company profile, branding primitives, users, roles, module subscriptions, organisation connections, notifications, audit logs and the shared document template engine.
- Each module owns the settings for the workflows it creates and operates.
- If a module is bought or used independently, it should expose its own settings without requiring unrelated modules.
- If modules are connected, the Settings Centre should show the same module-owned settings in one grouped view.
- A shared engine does not transfer ownership. For example, the document template renderer is core infrastructure, but Work Order templates belong to Works Logix and Job Docket templates belong to Contractor Logix.

The current registry is implemented in `app/services/core/module_settings_registry.py` and exposed through `Settings -> Module Settings`.

## Route Boundary Check

Active module route namespaces are protected by:

```text
.\venv\Scripts\python.exe scripts\module_route_boundary_check.py
```

This confirms current module routes stay under their own prefixes such as
`/members`, `/contractor`, `/finance`, `/assistant`, `/pm`, `/admin-portal`,
`/units`, `/notifications` and `/super-admin`. GAR feed routes are also checked
so each role-facing feed remains in the expected module namespace.
