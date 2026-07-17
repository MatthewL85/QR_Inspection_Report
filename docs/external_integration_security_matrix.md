# External Integration Security Matrix

Status: active integration credential and sync control note

Purpose: define how Logix modules connect to external systems such as Sage, Xero, Outlook, Google Calendar, Gmail, HR platforms and cloud document stores without leaking access across modules or organisations.

## Core Rule

The module that uses an external integration owns the credentials, scopes, sync logs, mapping rules, error handling and disconnect controls for that integration.

Shared platform services may provide encryption, token storage primitives, audit logging and connector utilities. They must not make an integration global unless the organisation has explicitly configured that scope.

## Credential Ownership Matrix

| Integration Type | Owning Module | Examples | Credential Boundary |
| --- | --- | --- | --- |
| Accounting package | Finance Logix | Sage, Xero, QuickBooks | Finance owns OAuth tokens, ledger mappings, posting rules and sync logs. |
| HR platform | HR Logix | HR Manager, payroll, leave systems | HR owns staff sync credentials, employee mappings and HR audit logs. |
| Contractor calendar | Contractor Logix | Outlook Calendar, Google Calendar, phone calendar feeds | Contractor Logix owns job docket calendar feeds for the contractor organisation and assigned engineers. |
| Property management calendar | Property Management Logix | PM site visits, AGMs, contract renewal reminders | PM module owns management-side calendar visibility. |
| Email intake | Owning workflow module | Contractor job inbox, Works request inbox, Finance invoice inbox | The module receiving the workflow owns mailbox credentials, intake rules and approval controls. |
| Cloud document storage | Core Platform plus owning module | SharePoint, Google Drive, Box | Core may store file metadata and visibility; the owning module controls which records may sync. |
| Messaging / collaboration | Owning workflow module | Teams, Slack, email notifications | Notifications may be sent externally, but source records and permissions stay in Logix. |
| AI provider | GAR AI Layer plus Core Platform | OpenAI, Google AI, future providers | GAR owns AI source-adapter policy; Core owns provider configuration and audit. |

## Sync And Scope Rules

1. Store credentials against the owning organisation, module and integration type.
2. Store sync logs with source record references and acting/sync user metadata.
3. Limit requested external scopes to the minimum needed for the workflow.
4. Never let a user's personal calendar, mailbox or drive token grant access to another user's private records.
5. Never let a contractor integration token access a property management company's private settings, documents or finance records.
6. When an organisation disconnects an integration, stop future sync without deleting historic audit or source records.
7. When a module is disabled, pause its external integrations until the module is re-enabled or formally disconnected.

## External Intake Rules

GAR or an intake parser may draft structured records from external email, calendar or document data, but creation must remain controlled:

- Works Logix owns work-order/request intake approval.
- Contractor Logix owns standalone job docket intake approval.
- Finance Logix owns invoice/payment intake approval.
- HR Logix owns HR record intake approval.

External content should be stored as evidence or source material linked to the created record, not as the only source of truth.

## Revocation And Audit Rules

Every external integration should support:

- connected by user and organisation;
- connected module and integration type;
- created, refreshed, failed and revoked timestamps;
- current status;
- last successful sync;
- last error summary;
- disconnect/revoke action;
- audit trail of sync-created or sync-updated records.

## Red Flags

Stop and review if:

- one module uses another module's external credential;
- a contractor calendar token can expose PM-only client or finance records;
- a Finance accounting token is configured inside general PM settings instead of Finance settings;
- a mailbox parser creates business records with no human or workflow approval route;
- external sync overwrites a finalised, approved, signed or closed Logix record;
- external documents are stored without source record and visibility metadata;
- GAR receives external data without module source references and role visibility checks.

## Guarded By

Primary checks:

```powershell
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\module_settings_registry_check.py
.\venv\Scripts\python.exe scripts\module_service_contract_check.py
.\venv\Scripts\python.exe scripts\organisation_connection_boundary_check.py
.\venv\Scripts\python.exe scripts\gar_source_adapter_contract_check.py
```
