# Source Record Identity Matrix

Status: active identity and numbering control note

Purpose: define how LogixPM, Works Logix, Contractor Logix, Finance Logix, Members Logix, Director Logix, HR Logix and GAR identify records safely when modules work independently or together.

## Core Rule

Internal database IDs, platform UIDs and human-readable reference numbers are different things.

Use source IDs and stable UIDs for system links. Use human-readable references for screens, PDFs, reports and search.

Do not use email addresses, display names, short work-order numbers or document labels as the primary cross-module link.

## Identity Types

| Identity Type | Purpose | Boundary |
| --- | --- | --- |
| Internal database `id` | Local persistence inside the current database | Never use alone as a public or cross-organisation identity. |
| Stable platform UID | Global record identity where records must be safely recognised across modules or organisations | Never reused after deletion, archive or merge. |
| Module source ID | The owning module's source record key, such as `work_order_id` or `job_docket_id` | Other modules may reference it, but ownership stays with the source module. |
| Human-readable reference | User-facing number shown on dashboards, PDFs and emails | Must include enough source context to avoid collisions. |
| External reference | Number supplied by a third-party system, email, phone instruction, contractor job number or accounting package | Store as supporting metadata, not as the Logix source identity. |

## Record Identity Matrix

| Record | Owning Module | System Link | Human Reference Rule |
| --- | --- | --- | --- |
| Organisation | Core Platform | `organisation_uid` | Organisation code or company display name may be shown, but the UID controls links. |
| Client / Development | Property Management Logix | `client_id` plus company scope | Client code belongs to the management company context. |
| Unit | Unit / Property Asset Spine | `unit_id`, `unit_uid`, `client_id` | Unit number may repeat across blocks or clients; show block/core and development context. |
| Member / Owner link | Members Logix | `unit_membership_id`, `user_id`, `unit_id`, `client_id` | Portal invite/access codes should create membership links, not replace them. |
| Member maintenance request | Members Logix | `member_request_id` | Use a Members-owned reference where visible, such as `MR-...`. |
| Work order | Works Logix / Property Management Logix | `work_order_id`, source organisation, optional `organisation_connection_id` | Use a prefix or source context so `WO-100` from one management company cannot be confused with `WO-100` from another. |
| Job docket | Contractor Logix | `job_docket_id`, optional `work_order_id` | Job docket numbers belong to Contractor Logix, such as `JD-2026-00006`. |
| Contractor job number | Contractor Logix / contractor external system | Contractor-owned metadata | Keep separate from the Logix job docket number. It may be blank or match a contractor's internal system. |
| Quotation request | Works Logix / Property Management Logix | `quotation_request_id` | Management owns the request reference. |
| Quotation response | Contractor Logix | `quotation_response_id`, source request ID | Contractor owns the response reference. |
| Payment request | Contractor Logix until Finance intake | `payment_request_id`, `job_docket_id`, optional `work_order_id` | Contractor payment request numbers stay separate from Finance invoice numbers. |
| Invoice / ledger record | Finance Logix | `invoice_id`, ledger source IDs | Finance owns invoice numbers, posting references and accounting sync IDs. |
| Contract / PSRA record | Property Management Logix / Contract Manager | `contract_id`, `client_id` | Contract numbers stay with the contract workflow. |
| Key Site Information section | Property Management Logix | `key_site_section_id`, `client_id` | Section titles are editable labels, not source IDs. |
| Audit event | Core Platform / owning module | `audit_event_id`, source record reference | Audit entries must point back to the source record and acting user. |
| GAR answer / recommendation | GAR AI Layer | source references plus visibility metadata | GAR may cite human references, but must store source record references. |

## Reference Display Rules

For user-facing screens and documents:

- show the module-owned reference first;
- show source context when a number may collide across organisations;
- keep linked source references behind the screen action;
- do not change historic references when a company renames or rebrands;
- show the contractor job number only as an external/internal reference beside the Logix job docket.

Examples:

| Situation | Safe Display |
| --- | --- |
| Work order from Bohan Hyland | `WO-BH-000541` |
| Work order from Savills with the same short number | `WO-SAV-000541` |
| Contractor job docket for an accepted work order | `JD-2026-00006` with source `WO-BH-000541` |
| Contractor internal reference | `Contractor Job No. ABC-7781` |
| Unit with repeated number across blocks | `Dodder View / Unit 7` |

## Cross-Module Linking Rules

1. The owning module creates and owns the source record.
2. Other modules store source references, not copied business facts.
3. Display references may be regenerated for UI formatting only if the source ID and immutable audit trail remain unchanged.
4. A module may expose a compact reference to another module only through a governed service, feed or organisation connection.
5. GAR must cite and store the source record references used for an answer or recommendation.

## Red Flags

Stop and review if:

- a record is linked across modules by email address, display name or free text;
- a contractor job number is treated as the Logix job docket number;
- a work-order number can collide across two management companies without source context;
- a unit number is shown without block/core/development context where duplicates are possible;
- a historic reference is changed by editing the current numbering template;
- GAR gives an answer without source record references;
- an external system ID replaces the Logix source identity.

## Guarded By

Primary checks:

```powershell
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\module_service_contract_check.py
.\venv\Scripts\python.exe scripts\organisation_connection_boundary_check.py
.\venv\Scripts\python.exe scripts\gar_source_adapter_contract_check.py
```
