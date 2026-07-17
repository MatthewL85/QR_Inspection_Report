# Stabilisation and Security Close-Out

Status: active close-out checklist

Purpose: give LogixPM a clear control point before the platform moves from Phase 3 stabilisation into deeper module expansion.

This document does not replace the module completion register. It is the short sign-off layer for security, settings ownership, module independence and future build readiness.

The role-by-module access contract is `docs/module_access_matrix.md`. Use it when adding dashboards, settings links, GAR feeds or cross-module navigation.

The module connection contract is `docs/module_connection_matrix.md`. Use it before connecting standalone modules, organisations or external systems.

The document ownership contract is `docs/document_template_ownership_matrix.md`. Use it before adding or moving any document template, PDF, export, quotation, payment request, work order or job docket output.

The source record identity contract is `docs/source_record_identity_matrix.md`. Use it before adding or changing UIDs, portal access codes, work-order numbers, job-docket numbers, contractor job numbers, invoice numbers, quotation references or any cross-module record reference.

The external integration security contract is `docs/external_integration_security_matrix.md`. Use it before adding or changing OAuth credentials, API keys, calendar feeds, mailbox intake, accounting integrations, HR integrations, cloud document storage or AI-provider configuration.

The deployment environment security contract is `docs/deployment_environment_security_matrix.md`. Use it before changing environment variables, secrets, debug behaviour, seed scripts, feature flags, migrations, upload storage or production deployment configuration.

The incident response and backup contract is `docs/incident_response_backup_matrix.md`. Use it before changing backup scope, restore behaviour, incident response, recovery testing, media recovery, external sync recovery or GAR rebuild behaviour.

The privacy and data classification contract is `docs/privacy_data_classification_matrix.md`. Use it before exposing personal, financial, HR, contractor-private, security/access or GAR-derived data through screens, exports, notifications, documents, integrations or AI answers.

The observability and monitoring contract is `docs/observability_monitoring_matrix.md`. Use it before adding health feeds, dashboard counts, operational alerts, background jobs, queue tiles, sync monitoring, degraded states or GAR source-adapter monitoring.

The release and change management contract is `docs/release_change_management_matrix.md`. Use it before merging, deploying, activating modules, running seed scripts, shipping migrations, updating document templates, changing GAR adapters or widening external integration scopes.

The production readiness gate is `docs/production_readiness_gate.md`. Use it before treating any module, workflow, dashboard, queue, integration or GAR surface as ready for live customer use.

The support and escalation ownership contract is `docs/support_escalation_ownership_matrix.md`. Use it before piloting or activating any module, workflow, integration, dashboard queue or GAR surface that users may rely on operationally.

The onboarding and data import contract is `docs/onboarding_data_import_matrix.md`. Use it before importing, seeding, migrating, bulk-inviting or syncing real organisations, clients, users, units, owners, residents, contractors, documents, media or external system records.

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
- cross-module links must use source IDs, stable UIDs and safe human-readable references rather than display labels or short numbers alone;
- external integrations must be owned by the module that uses them, with scoped credentials, sync logs and revocation controls;
- deployment configuration must keep secrets, debug behaviour, seed data, migrations and module feature flags environment-owned;
- backup, restore and incident response must preserve source records, media, audit history, visibility rules and external sync state;
- personal, financial, HR, contractor-private and security/access data must be classified before it is displayed, exported, notified or used by GAR;
- dashboard counts, health feeds, operational alerts and degraded states must be source-backed, module-owned and privacy-safe;
- release changes must be scoped, validated, rollback-aware and kept separate from unrelated dirty module work;
- production readiness must be explicit: prototype, review, pilot, production or deferred;
- support ownership and escalation must follow the module that owns the workflow;
- onboarding and imports must be batch-aware, duplicate-checked, source-mapped and rollback-aware;
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
11. Confirm any new UID, display reference or cross-module source reference matches `docs/source_record_identity_matrix.md`.
12. Confirm any external credential, connector, mailbox, calendar, cloud storage or sync behaviour matches `docs/external_integration_security_matrix.md`.
13. Confirm any environment variable, secret, seed script, migration, feature flag or deployment behaviour matches `docs/deployment_environment_security_matrix.md`.
14. Confirm any backup, restore, incident response, recovery test or external sync recovery matches `docs/incident_response_backup_matrix.md`.
15. Confirm any personal, financial, HR, contractor-private, security/access or GAR-derived data use matches `docs/privacy_data_classification_matrix.md`.
16. Confirm any health feed, dashboard count, operational alert, background job, degraded state or sync monitor matches `docs/observability_monitoring_matrix.md`.
17. Confirm any merge, deployment, migration, seed, rollback, module activation or external scope change matches `docs/release_change_management_matrix.md`.
18. Confirm any live customer use, pilot, module activation or production sign-off matches `docs/production_readiness_gate.md`.
19. Confirm any operational support, escalation, customer response or degraded-state support path matches `docs/support_escalation_ownership_matrix.md`.
20. Confirm any onboarding, import, migration, seed, bulk invite or external data intake matches `docs/onboarding_data_import_matrix.md`.
21. Confirm any GAR answer, feed or recommendation matches `docs/gar_visibility_matrix.md`.
22. Confirm any state change, approval, cross-module handoff or finalised document matches `docs/auditability_matrix.md`.
23. Confirm any delete, archive, restore, deactivate or retention behaviour matches `docs/data_retention_deletion_matrix.md`.

## Module Expansion Checklist

When starting or extending a module, record:

- source-of-truth models;
- module-owned routes and settings;
- document-template ownership;
- source record identity and numbering rules;
- external integration credential, sync and revocation rules;
- deployment environment, feature flag, seed data and migration rules;
- incident response, backup, restore and recovery ownership rules;
- privacy and data classification rules;
- observability, monitoring and degraded-state rules;
- release, validation and rollback ownership rules;
- production readiness level, blockers and sign-off owner;
- support owner, escalation route and customer-response rule;
- onboarding, import and data-quality rules;
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
- a cross-module link uses a human-readable reference, display name or email address instead of a source ID or stable UID;
- a work-order, job-docket, invoice, quotation or payment request number can collide across organisations without source context;
- a module uses another module's external integration credential, calendar feed, mailbox or accounting/HR connector;
- an external sync creates or changes business records without source references, audit trail and approval controls;
- production uses debug mode, local secrets, unreviewed seed users or manual schema changes;
- a backup excludes media, evidence, audit history or external sync state needed to recover a module workflow;
- a restore overwrites signed, approved, completed, paid or closed source records;
- an incident is resolved by deleting audit logs or source history;
- personal, financial, HR, contractor-private or security/access data is displayed without a role, organisation and purpose check;
- GAR reveals personal, financial, HR or contractor-private data the user cannot open in the source module;
- dashboard counts cannot be traced to source queries or include archived/hidden/out-of-scope records;
- logs or monitoring feeds expose passwords, tokens, access codes, private notes, financial details or excessive personal data;
- external sync, evidence upload or GAR source-adapter failures are visible only in server logs;
- a release includes unrelated module work because it was already dirty locally;
- a module becomes visible because a route exists rather than because module subscription, role and settings ownership allow it;
- a migration, seed script, document-template change or GAR adapter is shipped without a scoped validation or rollback path;
- a module is described as production-ready while it still depends on seed data, debug mode, missing settings ownership or undocumented user workflows;
- a pilot or production module has no named support owner or escalation path;
- a live import creates operational records without source mapping, duplicate checks, data classification or rollback path;
- bulk portal invites are sent before memberships and unit links are validated;
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
