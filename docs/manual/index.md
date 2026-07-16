# LogixPM User Manual

Status: living operating manual

Last updated: 2026-05-28

Purpose: explain how each part of LogixPM is used day to day by the people working inside the platform.

This manual is separate from the architecture documents. Architecture documents explain how the system is built. This manual explains how the platform should be used.

## Architecture And Governance Notes

The main platform architecture and active build guardrails are recorded in:

| Document | Purpose |
| --- | --- |
| `docs/platform_architecture.md` | Shared source-of-truth records, module boundaries and cross-module linking rules |
| `docs/platform_stabilisation_register.md` | Current stabilisation rules, verification gates and next cleanup priorities |
| `docs/module_completion_register.md` | Formal register of unfinished module work, ownership boundaries and close-out priorities |
| `docs/role_dashboard_surface_standard.md` | Shared dashboard UX rules for all role surfaces |
| `docs/module_contracts.md` | Module-level ownership, shared links and GAR visibility boundaries |

## Manual Structure

| Area | Manual page | Primary users |
| --- | --- | --- |
| Core Platform | `docs/manual/core_platform.md` | All roles |
| Super Admin | `docs/manual/super_admin.md` | Super Admin, platform owner |
| Client Manager | `docs/manual/client_manager.md` | Super Admin, Admin, Property Manager, Assistant |
| Unit Information | `docs/manual/unit_information.md` | Super Admin, Admin, Property Manager, Assistant |
| Assistant Workspace | `docs/manual/assistant_workspace.md` | Assistant, Assistant Manager, Master Assistant |
| Contract Manager | `docs/manual/contract_manager.md` | Super Admin, Admin, Property Manager |
| Works Logix | `docs/manual/works_logix.md` | Admin, PM, Assistant, Master Assistant |
| Members Logix | `docs/manual/members_logix.md` | Owners, co-owners, tenants, residents |
| Contractor Logix | `docs/manual/contractor_logix.md` | Contractors, contractor teams |
| Finance Logix | `docs/manual/finance_logix.md` | Finance Controller, PM, Super Admin |
| Director Logix | `docs/manual/director_logix.md` | OMC Directors, PM, Super Admin |
| HR Logix | `docs/manual/hr_logix.md` | Staff, Admin, HR users |
| Admin Portal | `docs/manual/admin_portal.md` | Admin users |
| Notifications | `docs/manual/notifications.md` | All roles |
| App / Mobile Readiness | `docs/manual/app_mobile_readiness.md` | All roles, mobile/PWA surfaces |
| Dashboard Review Logins | `docs/manual/dashboard_review_logins.md` | Local reviewers |
| GAR AI | `docs/manual/gar_ai.md` | All roles, role-aware |

## Operating Principles

1. Each module should be usable on its own.
2. Shared records such as clients, units, users, members and work orders connect the modules together.
3. Users should only see the data that matches their role and assignment.
4. GAR AI supports decision-making with source-backed context. It does not replace the owning module record.
5. Completed or governed records should be protected by audit history and controlled amendment workflows.

## How This Manual Should Be Updated

Each time a feature is added or changed, update the relevant manual page in the same work item.

Every feature note should capture:

- who uses it
- where they find it
- what they can do
- what happens in the background
- what other modules are connected
- what GAR can read or recommend

This keeps the final platform manual ready as LogixPM grows, instead of trying to reconstruct everything at the end.

Manual coverage is checked by:

```text
.\venv\Scripts\python.exe scripts\manual_coverage_check.py
```

The Phase 3 operating manual contract is checked by:

```text
.\venv\Scripts\python.exe scripts\phase3_manual_contract_check.py
```

This protects the current cross-module workflow guidance for Works Logix, Members Logix, Contractor Logix, Assistant cover, Notifications and GAR AI readiness boundaries.

The app/mobile feed contract is checked by:

```text
.\venv\Scripts\python.exe scripts\app_feed_contract_check.py
```

This confirms the read-only feed endpoints that future mobile and PWA clients can depend on.

The app shell readiness contract is checked by:

```text
.\venv\Scripts\python.exe scripts\app_shell_readiness_check.py
```

This confirms the install metadata, service worker route, static shell registration and core app-ready feed routes remain stable without creating a separate mobile source of truth.

The focused Phase 3E app/mobile readiness gate is checked by:

```text
.\venv\Scripts\python.exe scripts\phase3e_app_readiness_check.py
```

This confirms the app feed, shell, health, home, capabilities, mobile surface and manual contracts remain aligned as one app/mobile close-out suite.

The governed workflow action contract is checked by:

```text
.\venv\Scripts\python.exe scripts\workflow_action_contract_check.py
```

This confirms lifecycle actions remain POST-only while feeds remain read-only.

The notification intelligence contract is checked by:

```text
.\venv\Scripts\python.exe scripts\notification_contract_check.py
```

This confirms notification workflow stages, role/audience labels, source-target payloads and mark-read route behaviour remain stable for web and future app clients.

The navbar notification contract is checked by:

```text
.\venv\Scripts\python.exe scripts\navbar_notification_contract_check.py
```

This confirms the shared notification bell uses the same source-backed notification service as the Notification Centre and keeps notification actions governed.

The Works command-centre contract is checked by:

```text
.\venv\Scripts\python.exe scripts\works_command_centre_contract_check.py
```

This confirms the Works operational queue definitions, feed queues, stats and GAR payload remain stable for management dashboards and future app clients.

The Works Evidence and Audit Pack contract is checked by:

```text
.\venv\Scripts\python.exe scripts\works_evidence_audit_contract_check.py
```

This confirms completion evidence, member feedback evidence, reopen evidence, review-cycle risk and GAR source references remain stable for PM/Admin review.

The role dashboard attention contract is checked by:

```text
.\venv\Scripts\python.exe scripts\role_dashboard_attention_contract_check.py
```

This confirms Super Admin, Admin, Property Manager and Assistant dashboards keep the same Works/GAR attention queue, GAR quality strip and next-action links back to Works Logix.

The wider Phase 3 cross-module readiness suite is checked by:

```text
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py
```

For day-to-day iteration, use the faster contract-focused form:

```text
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py --quick
```

To run only the role dashboard and operational surface render smoke checks:

```text
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py --smoke-only
```

To see the selected checks without running them:

```text
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py --quick --list
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py --smoke-only --list
```

Full mode includes both the fast contracts and the slower role dashboard / operational surface render smoke checks. A failed child check is retried once by default to absorb transient local database disconnects; repeated failures still fail the suite.

The readiness runner mode split is protected by:

```text
.\venv\Scripts\python.exe scripts\phase3_runner_contract_check.py
```

The architecture/manual/stabilisation documentation spine is protected by:

```text
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
```

The module dependency boundary check is:

```text
.\venv\Scripts\python.exe scripts\module_dependency_boundary_check.py
```

This protects the operating principle that each module remains independent, loosely coupled and service/API driven.

The module access and settings ownership boundary check is:

```text
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
```

This protects the rule that Contractor Logix, LogixPM, Finance Logix, Members Logix and future standalone modules keep their own settings and role boundaries.

The module settings registry ownership check is:

```text
.\venv\Scripts\python.exe scripts\module_settings_registry_check.py
```

This protects the rule that each module keeps its own settings surface, document template ownership and standalone/connected setup while the shared registry remains role-aware.

The organisation connection boundary check is:

```text
.\venv\Scripts\python.exe scripts\organisation_connection_boundary_check.py
```

This protects the rule that standalone modules connect through organisation UIDs, module subscriptions and accepted connection records rather than shared email addresses or direct cross-company shortcuts.

The contractor document template ownership check is:

```text
.\venv\Scripts\python.exe scripts\contractor_document_template_boundary_check.py
```

This protects the rule that Contractor Logix owns contractor-created documents such as job dockets, quotation responses and payment requests, while Works/LogixPM owns work orders and quotation requests.

The archive inventory check is:

```text
.\venv\Scripts\python.exe scripts\archive_inventory_check.py
```

This is a read-only guardrail that lists legacy/archive areas and confirms whether active app code references old project roots. The formal policy is kept in `docs/architecture/archive_strategy.md`.
