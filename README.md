# LogixPM

LogixPM is being built as a modular SaaS ecosystem for property management, contractor operations, members/residents, directors, finance, HR and GAR AI.

The active build principle is simple: each module should work independently, while shared source-of-truth records let modules connect safely when organisations use more than one part of the platform.

## Start Here

| Document | Purpose |
| --- | --- |
| `docs/platform_architecture.md` | Core architecture, shared IDs and source-of-truth rules |
| `docs/platform_stabilisation_register.md` | Active stabilisation rules, verification gates and cleanup priorities |
| `docs/stabilisation_security_closeout.md` | Security/stabilisation sign-off checklist before wider feature expansion |
| `docs/module_access_matrix.md` | Role-by-module access boundaries for dashboards, settings and GAR visibility |
| `docs/module_connection_matrix.md` | Organisation, module and external integration connection boundaries |
| `docs/document_template_ownership_matrix.md` | Document template ownership boundaries by module and workflow |
| `docs/source_record_identity_matrix.md` | Source IDs, UIDs and safe human-readable numbering rules |
| `docs/external_integration_security_matrix.md` | External connector credentials, scopes, sync and revocation boundaries |
| `docs/deployment_environment_security_matrix.md` | Deployment secrets, feature flags, migrations and seed data boundaries |
| `docs/incident_response_backup_matrix.md` | Incident response, backup, restore and recovery ownership boundaries |
| `docs/privacy_data_classification_matrix.md` | Privacy, sensitive data and module data-classification boundaries |
| `docs/observability_monitoring_matrix.md` | Module health, monitoring, queue accuracy and degraded-state boundaries |
| `docs/release_change_management_matrix.md` | Release, change-control, validation and rollback boundaries |
| `docs/gar_visibility_matrix.md` | GAR source-backed answer and role visibility boundaries |
| `docs/auditability_matrix.md` | Audit ownership and human-approval boundaries for cross-module actions |
| `docs/data_retention_deletion_matrix.md` | Archive, deletion, retention and restoration rules by module |
| `docs/module_completion_register.md` | Formal register of unfinished module work, priorities and ownership boundaries |
| `docs/role_dashboard_surface_standard.md` | Shared dashboard UX pattern for every role surface |
| `docs/module_contracts.md` | Module ownership, integration points and GAR visibility boundaries |
| `docs/manual/index.md` | User-facing operating manual |

## Verification

For day-to-day development, run the faster Phase 3 contract suite:

```powershell
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py --quick
```

For release-style review, run the full Phase 3 suite:

```powershell
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py
```

To inspect the selected checks without running them:

```powershell
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py --quick --list
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py --smoke-only --list
```

The documentation spine is protected by:

```powershell
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
```
