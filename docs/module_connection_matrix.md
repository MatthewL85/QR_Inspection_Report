# Module Connection Matrix

Status: active integration boundary control note

Purpose: define how independently purchased Logix modules connect to each other and to external systems without becoming tangled or relying on email-address matching.

## Core Rule

Modules connect through governed organisation identity, module subscriptions, connection records, scoped service feeds and source IDs.

Do not use email addresses as the primary cross-organisation link. Email may be a notification destination, but it is not an integration identity.

## Platform Identity

| Concept | Purpose | Boundary |
| --- | --- | --- |
| `organisation_uid` | Stable identifier for a company/organisation using the platform | Never reused for another organisation. |
| Module subscription | Records which modules an organisation has enabled | Does not automatically grant access to another organisation's data. |
| Organisation connection | Governed link between two organisations, such as management company and contractor | Must record source organisation, target organisation, module scope, status and approval metadata. |
| Connection code / invite | Human-friendly setup mechanism for connecting organisations | Should create or request a governed organisation connection, not replace it. |
| User role and assignment | Defines what a person may see inside their organisation/module | Must still be checked after an organisation connection exists. |
| Source record ID | Links work orders, job dockets, units, invoices and requests across modules | The source module keeps ownership of the record. |

## Internal Module Connections

| Source Module | Target Module | Connects Through | Allowed Data Flow | Boundary |
| --- | --- | --- | --- | --- |
| Property Management Logix | Contractor Logix | Organisation connection, assigned contractor, `work_order_id` | Assigned work order context, site access, contact details, permitted evidence | Contractor does not enter PM dashboard or client list. |
| Contractor Logix | Works Logix | `work_order_id`, `job_docket_id`, completion/update service | Acceptance, rejection, scheduling status, progress updates, completion evidence | Contractor owns job docket; Works owns work order. |
| Works Logix | Members Logix | `member_request_id`, `unit_id`, visible work status | Request triage messages, status updates, reopen decisions | Members see only their own linked units/requests. |
| Works Logix | Finance Logix | `work_order_id`, payment readiness feed | Approved payment requests and supporting references | Finance owns invoice, approval, ledger and payment records. |
| Contractor Logix | Finance Logix | Contractor payment request, `contractor_company_id`, source work references | Payment request intake and contractor-visible payment status | Contractor cannot enter Finance workspace. |
| Property Management Logix | Director Logix | `client_id`, director assignment, governance feed | Board packs, quotation/CAPEX approvals, governance summaries | Director reads governed source data and does not own PM source records. |
| Core Platform | HR Logix | `user_id`, `company_id`, HR subscription | Staff profile creation, leave/policy visibility, HR notifications | HR owns HR records; Core owns identity. |
| GAR AI Layer | All modules | Source adapters, role visibility, source references | Summaries, recommendations, risk signals and answers | GAR reads what the user can access; GAR does not become the source of truth. |

## Standalone Module Rule

Each module must remain useful when purchased independently:

- Contractor Logix can create standalone job dockets without a linked Works Logix work order.
- Finance Logix can manage finance records without Works Logix or Contractor Logix.
- HR Logix can manage staff records without Property Management Logix workflows.
- Members Logix can expose portal data only when unit/member identity exists.

When a standalone module is later connected, existing records should link through governed IDs and source references rather than being recreated.

## External Integrations

External systems should be treated as module-owned integrations:

Credential ownership, sync scope, revocation and external intake approval are controlled by `docs/external_integration_security_matrix.md`.

| External System Type | Owning Module | Examples | Rule |
| --- | --- | --- | --- |
| Accounting packages | Finance Logix | Sage, Xero, QuickBooks | Finance owns credentials, mapping, sync logs and posting controls. |
| HR systems | HR Logix | HR Manager, payroll/leave platforms | HR owns credentials, mapping, staff sync and HR audit records. |
| Email intake | Owning workflow module | Contractor job inbox, Works request inbox | GAR may draft structured records, but a human or workflow rule must approve creation. |
| Calendars | Contractor Logix or HR Logix | Outlook, Google Calendar, phone calendars | Calendar export/sync must stay scoped to the owning organisation and assigned users. |
| Cloud document storage | Core Platform plus owning module | SharePoint, Google Drive, Box | Source record and visibility metadata must stay in Logix, even if files are stored externally. |

## Connection Lifecycle

1. Organisation creates or reveals its connection code.
2. Another organisation submits the code from its own module settings.
3. The platform creates a pending organisation connection.
4. The owning organisation approves or rejects the connection.
5. The connection defines allowed module scopes.
6. Users still need role and assignment checks before seeing connected records.
7. Disabling the connection stops future cross-module sharing without deleting historic audit records.

## Red Flags

Stop and review if:

- an integration links organisations by email address alone;
- a contractor can browse management company records because a connection exists;
- an external integration stores source-of-truth business facts only outside Logix;
- GAR creates records without source, confidence and approval metadata;
- a standalone module cannot operate unless another Logix module is present.

## Guarded By

Primary checks:

```powershell
.\venv\Scripts\python.exe scripts\organisation_connection_boundary_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\module_service_contract_check.py
.\venv\Scripts\python.exe scripts\gar_source_adapter_contract_check.py
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
```
