# Deployment Environment Security Matrix

Status: active deployment and environment control note

Purpose: define how LogixPM and each standalone module should handle secrets, environment variables, debug settings, migrations, seed data and deployment configuration without leaking development behaviour into production.

## Core Rule

Production configuration must be explicit, module-aware and environment-owned.

Do not rely on local defaults, seeded test users, debug behaviour, hard-coded secrets or development-only routes in production.

## Environment Ownership Matrix

| Configuration Area | Owning Layer | Rule |
| --- | --- | --- |
| Database URL and connection pool | Core Platform / deployment environment | Production must use managed secrets and migration-controlled schema. |
| Flask secret key and session settings | Core Platform / deployment environment | Never commit real secrets. Rotate if exposed. |
| Module feature flags | Core Platform plus owning module | A module should only expose routes, dashboards and settings when enabled for the organisation. |
| External integration credentials | Owning module plus secure secret store | Follow `docs/external_integration_security_matrix.md`. |
| AI provider configuration | GAR AI Layer plus Core Platform | Provider keys, model choices and safety settings must be environment-owned and auditable. |
| File upload storage | Core Platform plus owning module | Storage path/bucket must preserve source record and visibility metadata. |
| Email/SMS/calendar sending | Owning workflow module | Sending credentials must be scoped to the module and organisation. |
| Branding/theme assets | Owning organisation/module | Branding may differ by organisation, but must not grant data access. |
| Debug toolbar/logging | Deployment environment | Must be off in production and must not reveal secrets or source data. |

## Production Safety Rules

1. Production must not run with debug mode enabled.
2. Production must not depend on local SQLite files unless intentionally configured for a non-production environment.
3. Production secrets must come from environment/secret storage, not committed files.
4. Seed scripts must be safe to run locally and must not create production test users unless explicitly marked as demo/test data.
5. Demo users, review users and seeded dashboard accounts must be blocked, removed or clearly separated before production activation.
6. Migrations must be the only normal way to change production schema.
7. Feature flags and module subscriptions must gate module routes, settings and dashboard links.
8. Background jobs and sync tasks must run with a declared module owner and audit context.
9. Upload limits, allowed file types and malware/safety scanning should be defined before public production use.
10. Error pages must not expose stack traces, environment variables, tokens, SQL strings or private record data.
11. Schema changes must follow the schema and migration ownership contract in `docs/schema_migration_ownership_matrix.md`.

## Module Deployment Rules

| Module | Deployment Boundary |
| --- | --- |
| Property Management Logix | Must not expose contractor, finance, HR or member-only settings unless those modules are enabled and the user is authorised. |
| Works Logix | May send work context to connected contractors, but only through governed organisation connections and scoped source records. |
| Contractor Logix | Must operate standalone with its own settings, job dockets, calendar and document templates. |
| Finance Logix | Must own finance credentials, invoice numbering, posting controls and finance-only settings before production activation. |
| HR Logix | Must own HR credentials, staff documents and employee privacy boundaries before production activation. |
| Members Logix | Must keep member portal access tied to verified unit membership and not broad client visibility. |
| GAR AI Layer | Must use source-backed adapters, role visibility and audit metadata before answering production questions. |

## Seed And Test Data Rules

Seeded data is useful for review, but it must be identifiable:

- use review/test naming conventions;
- avoid real personal data where possible;
- keep passwords out of committed docs unless they are deliberately local-only test credentials;
- do not give seeded users broader module access than the role being tested;
- keep demo data separate from migration-required reference data.

## Release Readiness Questions

Before production-style deployment, answer:

- Which modules are enabled for this organisation?
- Which environment variables and secrets are required?
- Which external integrations are connected and who owns them?
- Which seed/demo users exist and should they remain?
- Which migrations are pending?
- Which uploads/storage paths are production-ready?
- Which GAR providers and source adapters are enabled?
- Which background jobs or sync tasks are active?

## Red Flags

Stop and review if:

- production uses a local development secret key;
- debug mode is active outside local development;
- a seed script creates privileged users in production;
- a route is visible because the file exists rather than because the module is enabled;
- a module reads another module's environment variable or credential directly;
- a migration is bypassed by manual production database edits;
- logs expose private user, unit, finance, contractor or GAR source data;
- uploaded evidence is stored without a source record, owner module or visibility rule.

## Guarded By

Primary checks:

```powershell
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\migration_integrity_check.py
.\venv\Scripts\python.exe scripts\schema_migration_contract_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\module_settings_registry_check.py
.\venv\Scripts\python.exe scripts\app_module_settings_feed_contract_check.py
.\venv\Scripts\python.exe scripts\phase3_runner_contract_check.py
```
