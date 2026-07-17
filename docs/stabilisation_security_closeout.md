# Stabilisation and Security Close-Out

Status: active close-out checklist

Purpose: give LogixPM a clear control point before the platform moves from Phase 3 stabilisation into deeper module expansion.

This document does not replace the module completion register. It is the short sign-off layer for security, settings ownership, module independence and future build readiness.

The role-by-module access contract is `docs/module_access_matrix.md`. Use it when adding dashboards, settings links, GAR feeds or cross-module navigation.

The module connection contract is `docs/module_connection_matrix.md`. Use it before connecting standalone modules, organisations or external systems.

The document ownership contract is `docs/document_template_ownership_matrix.md`. Use it before adding or moving any document template, PDF, export, quotation, payment request, work order or job docket output.

The GAR visibility contract is `docs/gar_visibility_matrix.md`. Use it before adding AI answers, summaries, recommendations, source adapters or role dashboards.

The auditability contract is `docs/auditability_matrix.md`. Use it before adding approvals, state changes, cross-module handoffs, external integrations, document finalisation or GAR-assisted actions.

The data retention contract is `docs/data_retention_deletion_matrix.md`. Use it before adding delete, archive, restore, deactivate, supersede or test-cleanup behaviour.

## Current Close-Out Position

The current stabilisation pass has guarded the platform-level boundaries that keep the ecosystem modular:

- users must stay inside the dashboards, settings and operational queues their role is allowed to use;
- Contractor Logix must not become accessible to property management company users;
- contractor users must not use shared settings or document links to reach LogixPM, Finance Logix or Members Logix management surfaces;
- each module must own the settings and documents for the workflows it creates;
- organisation connections must use governed organisation identity and connection records, not email-address coupling;
- GAR must read source-backed records with role and visibility controls rather than becoming the source of truth;
- cross-module actions must record module ownership, source records, acting users and human approvals where required;
- deletion must default to archive, deactivation, superseding or controlled amendment for business records;
- legacy/archive folders must remain outside active feature work.

Finance Logix is deliberately treated as a separate module-owned security slice. It can continue in its own build task, but it should not become production-active until its own roles, settings, document templates, GAR adapters and route boundaries are declared and checked.

## Release Readiness Rules

Before any larger feature expansion or deployment-style review:

1. Run the Phase 3 quick suite.
2. Run the full Phase 3 suite when a route, dashboard, queue, setting or document ownership rule changes.
3. Confirm `docs/module_completion_register.md` reflects any started, paused, split or deferred module work.
4. Confirm the relevant module owns its own settings routes and document templates.
5. Confirm no role can move into another organisation or module workspace through navigation, direct URL, settings links or document-template links.
6. Confirm GAR answers and feeds remain source-backed and role-aware.
7. Confirm new media or evidence behaviour attaches files to the record they prove.
8. Confirm any new role/module surface matches `docs/module_access_matrix.md`.
9. Confirm any new module or external integration link matches `docs/module_connection_matrix.md`.
10. Confirm any new document output matches `docs/document_template_ownership_matrix.md`.
11. Confirm any GAR answer, feed or recommendation matches `docs/gar_visibility_matrix.md`.
12. Confirm any state change, approval, cross-module handoff or finalised document matches `docs/auditability_matrix.md`.
13. Confirm any delete, archive, restore, deactivate or retention behaviour matches `docs/data_retention_deletion_matrix.md`.

## Module Expansion Checklist

When starting or extending a module, record:

- source-of-truth models;
- module-owned routes and settings;
- document-template ownership;
- allowed cross-module service/feed dependencies;
- GAR visibility rules;
- manual coverage;
- contract checks.

Do this before the module becomes a busy feature area. It is much cheaper to preserve boundaries early than to untangle them later.

## Red Flags

Stop and route the work back through stabilisation if any of these appear:

- a route checks only whether a user is logged in, but not whether they belong in that module;
- a template links from one module's settings to another module's operational settings;
- a document template is managed by a module that did not create the document;
- a PDF or export is added without a clear owning module;
- an integration uses email address matching instead of governed organisation, user, company, client, unit or work-order identifiers;
- a standalone module cannot operate unless another Logix module is present;
- a GAR response depends on free text without a source record reference;
- GAR reveals records the user could not open directly in the relevant module;
- a state-changing action has no acting user, source record or owning module audit trail;
- a signed, approved, completed or closed record can be overwritten instead of amended;
- a delete action removes source-linked business history rather than archiving or superseding it;
- active dashboard counts include archived records by default;
- a new feature reads from `legacy_archive` or `Old_QR` directly.

## Guarded By

Primary checks:

```powershell
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py --quick
.\venv\Scripts\python.exe scripts\phase3_readiness_check.py
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\stabilisation_register_gate_check.py
.\venv\Scripts\python.exe scripts\module_completion_register_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\module_settings_registry_check.py
.\venv\Scripts\python.exe scripts\module_service_contract_check.py
.\venv\Scripts\python.exe scripts\contractor_document_template_boundary_check.py
.\venv\Scripts\python.exe scripts\organisation_connection_boundary_check.py
.\venv\Scripts\python.exe scripts\legacy_archive_isolation_check.py
```
