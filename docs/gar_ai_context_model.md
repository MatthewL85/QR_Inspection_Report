# GAR AI Context Model

Status: Phase 1 architecture control document

Purpose: define how GAR should sit at the centre of the platform without taking ownership away from the business modules.

## GAR Role

GAR is the General Artificial Resident. GAR should understand the development, units, owners, residents, works, finance, contracts, documents and governance position.

GAR should be a cross-module intelligence layer. It should not replace the source-of-truth records.

## GAR Should Answer

For a selected client/development:

- What is the development?
- What units exist?
- Which blocks, cores and areas exist?
- Who owns each unit?
- Who occupies each unit?
- Are there open or recently closed works?
- Are there unresolved member requests?
- Are there finance risks, arrears or service charge issues?
- Are contracts active, expiring or expired?
- Are documents missing, expired or flagged?
- Are there governance risks?
- What should the PM, director, member or contractor know next?

## Context Sources

| Context | Source records |
| --- | --- |
| Organisation | `Company`, `User`, `Role`, `RolePermission` |
| Development | `Client`, `ClientKeyInfo`, compliance documents |
| Physical structure | `Block`, `Core`, `Unit` |
| Ownership | `Member`, `UnitMembership`, `member_units` |
| Occupancy | `Resident`, `Tenancy`, `UnitMembership` |
| Works | `WorkOrder`, `MaintenanceRequest`, `WorkOrderLifecycleEvent`, `WorkOrderCompletion`, `WorkOrderReopenRequest` |
| Contractor performance | `Contractor`, `ContractorPerformance`, `ContractorFeedback` |
| Finance | `Invoice`, `ServiceCharge`, `Arrears`, `Budget`, `Payment`, reports |
| Contracts | `ClientContract`, templates, renewal alert services |
| Documents | `Document`, `MediaFile`, compliance documents |
| Audit | `AuditLog`, `ProfileChangeLog`, `ContractAudit`, finance audit logs |

## GAR Context Object Target

Future GAR services should return a predictable context object:

```text
client_context
unit_context
ownership_context
occupancy_context
works_context
finance_context
contract_context
document_context
audit_context
risk_context
recommended_actions
visibility_rules
source_references
```

## Privacy and Visibility Rules

GAR must respect module and role boundaries.

Examples:

- A resident can see their own maintenance request, but not owner-only finance data.
- An owner can see their own unit and eligible building information, but not another owner's private contact data.
- A director can see governance summaries, but only detailed personal data where policy allows it.
- A contractor can see work order access information only where needed to complete the job.
- A Super Admin can see cross-platform configuration and audit information.

## Current State

GAR readiness exists across many models through fields such as:

- `gar_chat_ready`
- `gar_feedback`
- `gar_risk_score`
- `gar_recommendation`
- `ai_summary`
- `ai_extracted_data`
- `parsed_summary`
- `ai_confidence_score`

This is useful, but GAR is not yet centralised. The next design step should be a GAR context service that reads the platform spine instead of every screen building its own AI view.

## Recommended Next GAR Service Shape

```text
app/services/gar/context.py
app/services/gar/client_context.py
app/services/gar/unit_context.py
app/services/gar/risk_summary.py
app/services/gar/visibility.py
```

The first useful service would be:

```text
build_unit_context(unit_id, viewer_user_id)
```

That service would gather:

- Unit identity
- Client/development identity
- Block/core
- Owners and co-owners visible to the viewer
- Residents/tenants visible to the viewer
- Open/closed works counts
- Finance summary visible to the viewer
- Relevant documents
- GAR risk/recommendation fields

## Rule

GAR should always explain what source records informed an answer. No hidden magic. No invented data. No recommendation without source context.

## Phase 2 Foundation Added

Added:

```text
app/services/gar/context.py
scripts/gar_context_check.py
```

Current service functions:

```text
build_portfolio_context(company_id=None)
build_client_context(client_id, viewer_user_id=None)
build_unit_context(unit_id, viewer_user_id=None)
build_work_order_context(work_order_id, viewer_user_id=None, audience="admin")
```

These services return predictable context objects with:

- `context_type`
- business context sections such as `client_context`, `unit_context`, `works_context`, `finance_context`
- `risk_context`
- `recommended_actions`
- `visibility_rules`
- `source_references`

The Super Admin GAR AI Centre now reads from `build_portfolio_context()` instead of showing a placeholder.

## Phase 3 Works Context Added

The Works lifecycle now has a GAR-readable context path:

- `WorkOrderLifecycleEvent` records the persisted hand-off trail.
- `build_work_order_context()` returns the work order, source request, contractor, completion, member feedback, reopen and lifecycle context.
- The work order review screen shows a GAR AI Review Snapshot using the same context object.
- Members and Contractor views receive role-aware lifecycle summaries so future mobile/app surfaces can reuse the same source records.

GAR must treat the Works lifecycle as evidence, not editable truth. Actions such as approve completion, return to contractor, or accept/reject a reopen request stay inside Works Logix services.

Verification:

```text
.\venv\Scripts\python.exe scripts\gar_context_check.py
.\venv\Scripts\python.exe scripts\works_lifecycle_flow_check.py
```

Expected result:

```text
GAR context check
- Portfolio context checked: yes
- Client context checked: yes
- Unit context checked: yes
- Work order context checked: yes, or skipped when no real work orders exist

PASSED
```

The Works lifecycle check creates and removes a temporary work order flow so GAR work-order context can still be verified when the normal local database has no real work orders.
