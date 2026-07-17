# Onboarding and Data Import Matrix

Status: active onboarding and import-control contract

Purpose: define how real organisations, clients, users, units, owners, residents, contractors, documents, media and external records are brought into LogixPM without corrupting source records, module boundaries or production readiness.

## Core Rule

No imported or onboarded data becomes operational until it has an owning module, mapped source records, validation checks, duplicate checks, data classification, an audit or review path, a rollback plan and a named support owner.

Onboarding is not just data entry. It is the first point where the platform proves that each module can work independently while still connecting safely through shared source-of-truth records.

## Scope

This contract applies to:

- organisation and company setup;
- users, roles and permissions;
- clients and developments;
- units, blocks, cores, streets, areas and common areas;
- owners, co-owners, residents and tenants;
- contractor companies and contractor employees;
- key site information;
- contracts, documents, photos, videos and media;
- work orders, job dockets and completion records;
- Finance Logix imports, which are deferred until Finance-owned close-out;
- HR Logix imports, which are deferred until HR-owned close-out;
- external integrations, including accounting, HR, email, calendar and document storage systems.

## Import Ownership Matrix

| Area | Owning Module | Import Rule |
| --- | --- | --- |
| Organisations, companies, users, roles, module subscriptions and organisation UIDs | Core Platform | Core owns identity, access, module entitlement and organisation connection setup. |
| Clients, developments, units, contracts and key site information | Property Management Logix | PM Logix owns the property record and must map client, unit, block, core and contract data before use. |
| Owners, co-owners, residents, tenants, unit memberships and portal invites | Members Logix | Members Logix owns portal-facing membership links, but must use the unit and client source records from the property spine. |
| Work order history, member requests, reopen requests and evidence | Works Logix | Works Logix owns operational work history, routing state and management-side evidence records. |
| Standalone contractor clients, jobs, job dockets, calendar imports and contractor-only logs | Contractor Logix | Contractor Logix can import or manually create standalone dockets without a linked Works Logix work order. |
| Budgets, invoices, supplier records, balances, service charges and accounting sync | Finance Logix | Finance Logix imports are deferred until Finance-owned security, access, settings and document-template close-out is complete. |
| Staff records, HR documents, leave, reviews and HR integrations | HR Logix | HR Logix imports are deferred until HR-owned security, access, settings and document-template close-out is complete. |
| GAR source indexes, summaries and extraction drafts | GAR AI Layer | GAR may assist parsing or summarising imports, but GAR must not directly create operational records without a human or workflow review. |
| External systems and third-party connectors | Importing module | The module using the connector owns mapping, sync state, duplicate prevention, audit trail and rollback. |

## Import Readiness Checklist

Before importing, seeding, migrating, bulk inviting or syncing real data:

- identify the source file, source system or source organisation;
- name the owning module;
- map source fields to target model fields;
- identify required source IDs, stable UIDs and human-readable references;
- generate or match `organisation_uid`, `client_id`, `unit_id`, `unit_uid`, `user_id`, membership IDs and connector IDs where relevant;
- check for duplicate companies, users, clients, units, members, contractors, documents and work records;
- validate required relationships, including client to unit, unit to member, contractor to organisation and work order to source request;
- apply data classification before display, export, notification, GAR use or contractor sharing;
- test a sample import before full import;
- record or plan an import batch id, source reference, imported-by user and import timestamp;
- confirm a rollback, quarantine, deactivation or archive path;
- name the support owner for import errors and user questions.

## Data Quality Rules

- Do not key cross-module links off email address, display name, unit number, phone number, document label or free text alone.
- Use stable identifiers such as `unit_uid`, `organisation_uid`, `client_id`, `unit_id`, `user_id`, `member_id`, `work_order_id`, `job_docket_id` and external connector IDs.
- Missing block, core, address, Eircode, contractor or owner information should be imported as incomplete and reviewable, not guessed.
- Malformed records should be quarantined or marked for review rather than silently accepted.
- Live onboarding must not mix seeded test records with production records.
- Production imports should have a batch id, source file or source system, imported-by user and import timestamp.
- No direct database edits should be used as the normal onboarding path.

## Portal and Membership Onboarding

Create and validate memberships before sending portal invites.

Portal codes and invites must be tied to a membership, unit, user and client record. They must not be free-floating codes that can reveal data by email address, unit number or display name alone.

Bulk portal invites are allowed only after owner and resident records have been validated against their unit memberships. Expired, revoked or superseded invites must not grant access.

When a member owns multiple properties, the portal should resolve their visible units through verified membership records rather than by asking the member to know internal `unit_uid` values.

## Document and Media Onboarding

Documents, photos, videos and evidence must attach to the correct source record: client, unit, member request, work order, job docket, key site information, contract, invoice, audit event or support case.

Folder names, email subjects and document labels are not primary identifiers.

Imported documents and media need provenance: source system or file, upload/import user, timestamp, classification and visibility rule. Contractor-private, finance, HR, security/access and personal data must be classified before it is shared or used by GAR.

## External Data Migration

API, sync or connector imports require:

- module ownership;
- connection scope;
- credential ownership;
- source system ID;
- last sync state;
- duplicate prevention;
- idempotent retry behaviour;
- rollback or disconnect path;
- a clear rule for whether Logix or the external system is the source of truth.

External sync must not overwrite signed, approved, completed, paid, closed or legally sensitive records without a controlled amendment workflow.

## Red Flags

Stop and route the work back through stabilisation if:

- an import uses email, unit number, phone number or display name as the only link;
- seeded test data is mixed with live onboarding;
- GAR-generated extraction directly creates records without human or workflow review;
- Finance Logix or HR Logix imports are run before their module-owned security close-out;
- media or documents are imported without a source record;
- a bulk portal invite is sent before owner/resident records are validated;
- imported records cannot be reversed, quarantined, archived or deactivated;
- imported records become visible in dashboards before role access, module subscription and data classification are checked.

## Guarded By

Use these checks around onboarding, import, migration, bulk invite and connector work:

```powershell
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\migration_integrity_check.py
.\venv\Scripts\python.exe scripts\core_platform_identity_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\module_settings_registry_check.py
.\venv\Scripts\python.exe scripts\organisation_connection_boundary_check.py
.\venv\Scripts\python.exe scripts\media_evidence_spine_check.py
.\venv\Scripts\python.exe scripts\contractor_evidence_propagation_check.py
.\venv\Scripts\python.exe scripts\app_company_setup_feed_contract_check.py
.\venv\Scripts\python.exe scripts\onboarding_data_import_contract_check.py
.\venv\Scripts\python.exe scripts\phase3_runner_contract_check.py
```
