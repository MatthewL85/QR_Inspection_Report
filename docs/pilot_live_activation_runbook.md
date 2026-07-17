# Pilot and Live Activation Runbook

Status: active pilot/live activation contract

Purpose: define the practical steps required before a module, workflow, dashboard, integration or GAR surface is switched on for a real organisation.

This runbook sits after the production readiness gate. A feature can pass local checks and still be unsafe to expose to real users if the activation scope, support path, rollback path or real-data boundary is unclear.

## Core Rule

No module, workflow, dashboard, queue, document, external integration or GAR surface should be activated for real users until the activation scope, user roles, organisation boundary, source records, data classification, support owner, rollback owner and verification evidence are recorded.

## Activation Types

| Type | Meaning | Allowed data |
| --- | --- | --- |
| Internal Review | Used by internal review users only | Seeded or clearly marked review data |
| Controlled Pilot | Used by named real users for a named organisation | Limited real data with support and rollback owners |
| Live Activation | Normal customer use | Real data, live support, monitoring and recovery path |
| Module Add-On | A customer adds another Logix module later | Real data only after connection and settings checks pass |
| External Connector Activation | A customer connects an external system | Scoped sync data only after credential, mapping and rollback checks pass |

## Activation Preflight

Before activation, record:

- organisation or company being activated;
- module or workflow being activated;
- activation type;
- user roles allowed to use it;
- routes, dashboards, settings pages and document templates included;
- routes, dashboards, settings pages and document templates excluded;
- source records used;
- data classes exposed;
- GAR source adapters enabled or explicitly excluded;
- external integrations enabled or explicitly excluded;
- support owner;
- rollback owner;
- target activation date;
- end date or review date for pilots;
- checks run;
- known limitations.

## User and Role Verification

Activation requires at least one verified user journey for each role that will use the module.

Verify that:

- allowed users can reach the correct dashboard and settings areas;
- disallowed users cannot reach the module through direct URL, navigation, document links, settings links or notification links;
- Contractor Logix remains contractor-only;
- property management company users cannot enter Contractor Logix dashboards;
- contractor users cannot enter Property Management Logix, Finance Logix, Members Logix, Director Logix or HR Logix dashboards unless they also have a separate valid role for that module;
- GAR answers only from source records that the current user can open directly.

## Real Data Boundary

Before real data is used:

- seeded review users and seeded review records must be clearly separated from real organisation records;
- imports must match `docs/onboarding_data_import_matrix.md`;
- personal, financial, HR, contractor-private and security/access data must match `docs/privacy_data_classification_matrix.md`;
- records must use source IDs and stable UIDs rather than display labels or email-only matching;
- documents and media must attach to the source record they prove;
- dashboard counts must match the filtered records behind the tile.

## Support and Rollback

Every pilot and live activation must name:

- first-line support owner;
- escalation owner;
- rollback owner;
- incident owner;
- customer contact owner;
- expected response rule for support issues;
- rollback method, such as feature flag, module subscription removal, route guard, connector revocation, archive, deactivation or restore.

If the rollback would delete source records, evidence, audit history, signatures, completed records, paid records or external sync state, the activation must not proceed.

## Module Add-On Rule

When an organisation later adds another module, treat it as a new activation.

Examples:

- a Property Management Logix customer adds Contractor Logix;
- a Contractor Logix customer connects to a management company using Works Logix;
- a customer adds Finance Logix after using Property Management Logix;
- a customer adds HR Logix after using Core Platform users;
- a customer enables GAR across more modules.

Do not assume that because the organisation is live in one module, it is safe in another. Each module must prove its settings, roles, documents, support path, data classification and rollback path.

## External Connector Activation

Before enabling an external connector:

- confirm credential owner;
- confirm module owner;
- confirm sync scope;
- confirm source-of-truth direction;
- confirm field mapping;
- confirm duplicate prevention;
- confirm revocation path;
- confirm degraded-state display;
- confirm GAR behaviour if the connector is unavailable;
- confirm whether sync records are drafts, review items or operational records.

## Activation Sign-Off Record

For every controlled pilot or live activation, record:

- activation name;
- organisation;
- module;
- activation type;
- activation owner;
- support owner;
- rollback owner;
- data classes exposed;
- GAR adapters enabled;
- external connectors enabled;
- checks run;
- manual pages updated;
- known limitations;
- review date;
- decision: review, pilot, live, paused or rolled back.

Until a dedicated activation UI exists, this record can live in the relevant module documentation or release note.

## Red Flags

Stop activation if:

- a module is visible because a route exists rather than because role, subscription and settings ownership allow it;
- the organisation has not explicitly enabled the module;
- a user can move from one organisation workspace into another;
- a user can move from Contractor Logix into management-company settings;
- a dashboard tile does not match the list behind it;
- support ownership is not named;
- rollback would destroy source records, evidence, audit history, media, signed records, completed records or external sync state;
- seeded users or seeded data are mixed into the live activation;
- GAR can answer from records the user cannot open directly;
- Finance Logix or HR Logix is activated before its module-owned close-out is complete.

## Guarded By

Use these checks around pilot, live activation and module add-on work:

```powershell
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\pilot_live_activation_contract_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\module_settings_registry_check.py
.\venv\Scripts\python.exe scripts\module_completion_register_check.py
.\venv\Scripts\python.exe scripts\organisation_connection_boundary_check.py
.\venv\Scripts\python.exe scripts\notification_role_visibility_contract_check.py
.\venv\Scripts\python.exe scripts\queue_surface_contract_check.py
.\venv\Scripts\python.exe scripts\gar_source_adapter_contract_check.py
.\venv\Scripts\python.exe scripts\phase3_runner_contract_check.py
```
