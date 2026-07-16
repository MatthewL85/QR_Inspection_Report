# Unfinished Module Completion Register

Status: active completion control register

Purpose: keep LogixPM's growing module ecosystem honest. New module work should be recorded here before it expands, so unfinished foundations are visible and modules stay independent, loosely coupled and able to connect safely.

## Register Rule

No module should move into wider feature expansion unless its unfinished work is recorded here with:

- the module owner and source-of-truth records;
- the current completion state;
- the next unfinished items;
- the security and settings ownership boundaries;
- the document/template ownership boundary;
- the GAR visibility rule;
- the user manual and validation coverage needed to prove it has not drifted.

If a module is being built in a separate task, that task may own its feature work, but this register remains the control point for platform-level boundaries.

## Completion States

| State | Meaning |
| --- | --- |
| Live | Usable now with guarded routes, documented workflow and validation coverage. |
| Foundation | Core models/routes/services exist, but important workflow or polish items remain. |
| Shell | Entry point or early structure exists, but business workflows are not complete. |
| Planned | Strategic module is defined, but implementation has not started. |
| Deferred | Deliberately parked until prerequisite modules or workflows are ready. |

## Cross-Cutting Close-Out Register

| Item | Priority | Status | Owner | Required before expansion |
| --- | --- | --- | --- | --- |
| Module access/security boundaries | P0 | Guarded | Core Platform | Role checks must stop users entering another organisation/module workspace. Contractor Logix routes must require Contractor role. Management users must not use settings links as a route into Contractor Logix. |
| Module settings ownership | P0 | Guarded | Core Platform plus each module | Shared Settings Centre may group connected modules, but each standalone module owns its own settings pages, document templates, bank/insurance records and connection setup. |
| Organisation identity and connections | P0 | Foundation | Core Platform | Organisations connect by `organisation_uid`, module subscriptions and governed connection records, not email addresses. |
| Document template ownership | P0 | Guarded | Core Platform plus document-owning module | Shared renderer can be reused, but document ownership stays with the module that creates the document. Work orders and quotation requests are Works/LogixPM documents; job dockets, quotation responses and payment requests are Contractor Logix documents. Guarded by `scripts/contractor_document_template_boundary_check.py`. |
| Media and evidence spine | P1 | Partial | Core Platform | Photos, videos and documents need a consistent media/evidence service across member requests, work orders, job dockets, key site info and completion evidence. |
| Manual and validation coverage | P1 | Active | Core Platform | User manual and contract checks must be updated in the same slice as user-facing workflow changes. |
| Legacy/archive isolation | P1 | Active | Core Platform | `legacy_archive` and `Old_QR` remain out of active feature work unless a migration/cleanup task explicitly brings something forward. |

## Module Completion Register

| Module | Current state | Source-of-truth ownership | Must remain independent | Unfinished items |
| --- | --- | --- | --- | --- |
| Core Platform | Foundation / Active | Users, roles, companies, organisation identity, document/media foundations, audit, notifications | Yes. It supplies shared foundations, not module business workflows. | Permission matrix hardening, organisation connection lifecycle, audit coverage, media service consolidation, module settings ownership checks. |
| Property Management Logix | Active | Clients/developments, assignments, contracts, key site information, management-side settings | Yes. It can run without Contractor, Members, Finance or HR Logix. | Remaining heavy-page UI cleanup, client edit/profile consistency, settings ownership polish, document template boundaries for management-owned documents. |
| Unit / Property Asset Spine | Foundation | Units, block/core/area, unit identity, portal access and membership links | Shared core spine used by other modules. | Finance balance link, owner/resident directory refinement, unit membership verification hardening, globally safe unit UID display/claim workflow. |
| Works Logix | Foundation / Phase 3 Active | Work order lifecycle, request triage, routing, completion review, reopen decisions | Yes for management workflow. Contractor Logix may act on assigned work but must not own the work order. | Queue pages per tile across roles, quotation request lifecycle, payment request handoff, role-specific dashboards, notification and evidence hardening. |
| Contractor Logix | Foundation | Contractor profile, job dockets, calendar, contractor document templates, private materials/time logs, payment/quotation responses | Yes. It must work with standalone manual job dockets even when the PM company does not use LogixPM. | Settings close-out, engineer/team setup, document/PDF polishing, quotation response workflow, payment request workflow, calendar/mobile field workflow depth. |
| Members Logix | Foundation | Owner/resident portal access, member requests, linked unit visibility, replies and reopen requests | Yes. It must remain mobile/app-ready. | Multi-property portal polish, evidence upload hardening, reply/reopen UX, resident/owner visibility separation, PWA/mobile finish. |
| Finance Logix | Foundation | Budgets, service charges, debtors, arrears, aged debtor snapshots, invoice/payment read models, supplier payables, scoped ledger/reconciliation snapshots, balances and finance documents | Yes. It may connect to Works/Contractor payment requests through `work_order_id`, but owns finance records and must remain usable as a standalone module through `company_id`, `client_id`, `unit_id` and future `member_id` visibility. | Governed invoice approval, ledger posting, payment runs, bank reconciliation execution, chart of accounts depth, creditor-master scoping, invoice templates, accounting integrations and member-facing owner balance rules. |
| Director Logix | Shell | Director visibility, governance, quotation/CAPEX approvals, board packs | Yes. It reads governed records and should not own PM, Works or Finance source data. | Director assignments, voting, quotation review, governance pack documents, role-aware GAR summaries. |
| HR Logix | Planned / Foundation | Employee profiles, leave, policy documents, HR notifications and manager approvals | Yes. It links to Core users but owns HR records. | Staff profile creation from user onboarding, leave/policy workflows, HR document templates, external HR integration settings. |
| GAR AI Layer | Foundation | Source-backed context, role-aware digests, recommendations, explainability and audit references | GAR is cross-module, but must not become the source of truth. | Deeper finance/works/contracts query coverage, source adapter registry hardening, role-aware answer permissions, document extraction pipeline, recommendation audit trails. |

## Current Sprint Decision

This stabilisation task owns the P0 boundary work: module access/security boundaries and module settings ownership.

The separate Finance Logix task may build Finance foundations, but it should not alter shared route guards, module settings ownership rules, organisation connections or cross-module visibility without bringing the change back through this register.

## Boundary Rules To Preserve

1. A property management company user must not enter Contractor Logix operational screens.
2. A contractor user must not enter LogixPM management settings, Finance Logix settings or Members Logix management data through shared settings links.
3. Standalone modules must expose their own settings routes, even when a connected Settings Centre shows the combined module map.
4. Shared document rendering does not transfer ownership of the document.
5. GAR may read only what the user's role, organisation, module subscription and connection allow.
6. New module routes must be added to the relevant contract checks before they become business-critical.
