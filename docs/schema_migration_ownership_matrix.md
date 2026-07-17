# Schema and Migration Ownership Matrix

Status: active schema-control contract

Purpose: define how database schema changes move through a modular LogixPM ecosystem without turning independent modules into one tangled database change stream.

## Core Rule

Every schema change must have an owning module, a matching model/service expectation, an Alembic migration, a validation path and a recovery plan.

Manual production database edits are not a normal delivery path.

## Ownership Matrix

| Schema area | Owning layer | Rule |
| --- | --- | --- |
| Users, roles, companies and organisation identity | Core Platform | Shared identity schema must not grant module access by itself. |
| Clients, properties, contracts and key site records | Property Management Logix | Management records must stay client-scoped and module-owned. |
| Units, unit UIDs and memberships | Unit / Property Asset Spine | Unit identity must stay globally stable and linkable without exposing unrelated units. |
| Member requests, owners, residents and portal access | Members Logix | Member schema must preserve unit membership visibility and mobile/app readiness. |
| Work orders, triage, routing and reopen requests | Works Logix | Works schema owns work-order lifecycle records, not contractor job dockets. |
| Job dockets, schedules, private logs and contractor documents | Contractor Logix | Contractor schema must work standalone and must not depend on LogixPM-only work orders. |
| Budgets, invoices, balances and payments | Finance Logix | Finance schema must stay finance-owned and guarded until Finance close-out is complete. |
| Staff, HR documents and leave records | HR Logix | HR schema must stay HR-owned and HR-visible only. |
| GAR source indexes, summaries and prompts | GAR AI Layer | GAR schema stores derived/source references, not replacement business facts. |

## Migration Rules

1. Migrations must be the only normal way to change production schema.
2. A migration must not mix unrelated module work unless the change is deliberately shared core infrastructure.
3. A migration must have matching model, service and route or feed expectations.
4. A migration must preserve source IDs, stable UIDs, audit history, media/evidence links and external sync references.
5. A migration must not rewrite signed, approved, completed, paid or closed records without an amendment/superseding plan.
6. A migration that introduces a public or cross-module reference must follow `docs/source_record_identity_matrix.md`.
7. A migration that adds personal, financial, HR, contractor-private or security/access data must follow `docs/privacy_data_classification_matrix.md`.
8. A migration that enables a deferred module must not make that module production-active without the relevant module close-out.
9. A migration must include rollback or recovery notes before pilot or live activation.
10. Local seed or review data must never be required for a migration to succeed in production.

## Review Questions

Before adding or changing a migration, answer:

- Which module owns this schema?
- Is this a core shared table or a module-owned table?
- Which model and service logic expects the new fields?
- Which dashboards, queues, documents, exports or GAR adapters can see the data?
- Does this alter source identity, role visibility, data classification or document ownership?
- Does this require backfill, duplicate checking, data cleanup or import mapping?
- What happens if the migration succeeds but the deployment is rolled back?
- What happens if the deployment succeeds but the migration needs recovery?

## Red Flags

Stop and route the work back through stabilisation if:

- a migration includes Finance, HR, Contractor, Works and Members changes in one unscoped file;
- a production issue is fixed by direct database edits instead of a migration or controlled admin workflow;
- a migration creates a route-visible feature before module subscription, role access and settings ownership are ready;
- a migration introduces a human-readable reference that can collide across organisations;
- a migration deletes or rewrites audit history, evidence, media, source references or external sync state;
- a migration makes GAR the only holder of a business fact;
- a migration depends on local seed data, demo users or debug-only defaults;
- the Alembic chain has multiple unexpected heads or missing parents.

## Guarded By

Primary checks:

```powershell
.\venv\Scripts\python.exe scripts\schema_migration_contract_check.py
.\venv\Scripts\python.exe scripts\migration_integrity_check.py
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
```
