# Works Logix

Status: Phase 3 operating guide

Last updated: 2026-05-28

## Purpose

Works Logix manages maintenance and operational work from request through completion, feedback and reopen review.

It connects:

- Members Logix requests
- PM/Admin/Assistant triage
- Contractor Logix job queues
- completion evidence
- member/resident feedback
- reopen requests
- GAR AI operational intelligence

## Core Flow

The Phase 3 cross-module flow is:

1. Member or resident submits a maintenance request.
2. Works Logix shows the request in the operational queue.
3. PM, Admin, assigned Assistant or Master Assistant reviews it.
4. The request can be converted to a work order only after a contractor is selected.
5. The new work order is immediately routed to the selected contractor queue.
6. Contractor accepts, starts and submits completion evidence.
7. Member or resident is notified and can provide feedback.
8. PM/Admin reviews completion.
9. PM/Admin approves and closes, or returns it to the contractor.
10. If the member/resident says the issue is not resolved, a reopen request can be raised.
11. PM/Admin reviews the reopen request and either reopens the work order or rejects the request with notes.

If completion is returned, the PM/Admin return reason is stored as a Works Logix lifecycle event. Contractor Logix should show this as a return context so the contractor can see what to fix before resubmitting.

Works Logix also tracks a review-cycle signal from lifecycle events:

- completion submissions
- completion returns
- resubmissions
- latest return reason
- whether repeated returns need management attention

This is not yet a full contractor performance score. It is a source-backed operational signal for PM/Admin review, Contractor Logix follow-up and GAR AI context.

When a completion is returned more than once, Works Logix surfaces it as a Repeated Returns management signal. This should prompt a PM/Admin or Assistant Manager to review the evidence, return reasons, contractor performance context and whether the issue is really recurring or unresolved.

GAR Works Intelligence also derives a contractor quality risk signal from repeated completion returns and low member/resident feedback. This is an early management signal only; it does not replace a future Contractor Logix performance score or automatically restrict contractor routing.

The Works command centre should show contractor quality signals inside the GAR Works Intelligence section. The display should remain compact: contractor name, severity, repeated return count and low-feedback count. This lets managers see the pattern without leaving the Works command centre.

## Operational Queues

Works Logix should separate:

- open work orders
- closed work orders
- member maintenance requests
- quote requests
- payment requests
- returned contractor work
- repeated completion returns
- reopen requests
- GAR Works intelligence
- a short Next Actions strip that ranks the most urgent operational queue items

Closed work orders should be accessed through the closed work orders tile or section. This keeps the page readable and avoids mixing closed history into the active work queue.

Quote requests should be accessed through the Quote Requests tile. A PM/Admin can request quotations from one or more active Contractor Logix contractors from an open work order. Works Logix creates `QuoteRecipient` records for the selected contractor users, records a lifecycle event, sends contractor notifications and moves the work order into `Quote Requested` so it is separated from the normal open work order queue.

This is the first foundation for the future quotation workflow. The work order remains owned by Works Logix. Contractor Logix receives the quotation invitation and can review or decline it without becoming the assigned contractor for the job.

Contractors can submit a quote response from the Contractor Logix work pack. The response stores the main quote file, optional supporting files, quoted total, summary and contractor note against the existing `QuoteResponse` model. Works Logix updates the source work order to `Quote Submitted`, records the lifecycle event and notifies management users. The Quote Requests tile shows submitted quote files and totals so management can review them without mixing quotation records into the normal open work order queue.

Management users can select one submitted quote from the Quote Requests queue. Selecting a quote marks that response as approved, marks the other submitted quotes as not selected, assigns the chosen contractor to the source work order and moves the work order back into the live `Assigned` workflow. Selected and non-selected contractors are notified, and the decision is recorded in the work order lifecycle for audit and GAR context.

Later phases can add Director Logix comparison/voting and Finance Logix approval/invoice readiness on top of the same source records.

Payment requests should be accessed through the Payment Requests tile. When a contractor completes work and sends a Payment Request from the linked Job Docket, Works Logix surfaces that record for PM/Admin/Assistant/Finance review without giving property-management-company users access to Contractor Logix. Authorised management users can preview the source-backed Payment Request document from the Works Logix queue or the work-order review page before the future Finance Logix payment workflow takes over.

After review, Works Logix can mark the Payment Request as `Ready for Finance`. This records a lifecycle event and moves the contractor request out of the active payment-request queue. It does not create, approve or pay a Finance Logix invoice.

Work orders, quotation requests and payment request review packs should use the shared Core Document Template foundation for branding, terms, numbering and future PDF output. Works Logix owns the operational workflow and review queues; Documents Logix owns the governed document-template foundation.

This is a Finance Logix readiness handoff, not a full invoice ledger yet. The source remains the Works Logix work order and linked Contractor Logix job docket. The management user should review the completed work pack, evidence, docket number, contractor and invoice/payment state before the future Finance Logix payment workflow takes over.

The Next Actions strip is derived from the same source queues. It does not create new workflow state. It helps PM/Admin/Assistant users decide whether to route unassigned work, triage member requests, review reopen requests, check contractor follow-up or approve/return completion evidence.

Repeated Returns is also derived from lifecycle events. It does not create a new work-order status. It highlights work orders where contractor completion has been returned more than once so management can intervene before the issue drifts.

The Repeated Returns tile opens a dedicated Quality Review queue. This page should show the affected work orders, development, unit, current status, contractor, evidence quality, member/resident feedback signal, review-cycle count, latest return context and a link to the full evidence/audit pack. The purpose is to keep the main open work queue readable while still giving management a focused place to investigate quality or performance issues.

Repeated Returns should also be visible from role dashboards where the user has Works management access. Super Admin, Admin, Property Manager and Assistant users should be able to open the dedicated quality review queue directly from their dashboard attention cards or Next Actions strip.

Where GAR identifies contractor quality risk patterns, the same management dashboards show a compact GAR Quality Signal strip beneath the Works Attention Queue. This strip is hidden when no risk is present and links back to the Repeated Returns review queue when action is needed.

At the point a completion is returned for the second time, Works Logix should notify the relevant management users with a Quality Review notification. The contractor still receives the normal returned-work notification.

Workflow notifications should carry source references back to the owning record. Member request notifications point to the Maintenance Request; assignment, completion, return, feedback, reopen and closure notifications point to the Work Order. This lets the Notification Centre, GAR and future app views show the same traceable source.

The same Next Actions signal is also surfaced on role dashboards for Super Admin, Admin, Property Manager and Assistant users so the operational priority is visible before opening the full Works command centre.

Returned contractor work should remain separate from newly assigned or active work. This keeps contractor follow-up visible without confusing it with first-time assignments.

Role dashboards are an attention surface, not a second workflow engine. Super Admin, Admin, Property Manager and Assistant dashboards should all show the same source-backed Works Attention Queue, Next Actions strip and GAR quality signal pattern. The links can be role-scoped, but they must route back to the governed Works command centre or the Repeated Returns quality review queue.

This protects the user experience: staff can see urgent Works/GAR priorities as soon as they land on their dashboard, while conversion, routing, completion review and reopen decisions still happen inside Works Logix.

The role dashboard attention contract is protected by:

```text
.\venv\Scripts\python.exe scripts\role_dashboard_attention_contract_check.py
```

This confirms Super Admin, Admin, Property Manager and Assistant dashboards keep the same Works/GAR queue shape, route links, GAR quality strip and next-action partials.

Management-side Works queues also expose read-only command-centre feeds for future app/API clients:

- Super Admin: `/super-admin/work-orders/feed.json`
- Admin: `/admin-portal/work-orders/feed.json`
- Property Manager: `/property-manager/work-orders/feed.json`
- Assistant: `/assistant/work-orders/feed.json`

These feeds return role-scoped stats, operational queues, next actions, permitted work records and GAR summary context. They are read-only. Conversion, contractor assignment, completion review and reopen decisions remain controlled by Works Logix routes and services.

The command-centre queue contract is protected by:

```text
.\venv\Scripts\python.exe scripts\works_command_centre_contract_check.py
```

This confirms the operational queue definitions, stats, feed queues, filters and GAR command-centre payload remain stable even when a development has no active work records. That lets the web UI, future mobile apps and GAR panels rely on the same structure.

Lifecycle actions must remain POST-only. App/mobile clients should read display
state from feeds, then call the governed Works Logix action routes for
conversion, contractor assignment, contractor status changes, feedback and
reopen decisions. The contract is protected by:

```text
.\venv\Scripts\python.exe scripts\workflow_action_contract_check.py
```

The command-centre feed also exposes `gar.contractor_quality` as a compact app-ready collection of contractor quality risk patterns. This lets future mobile/app clients show the same GAR contractor-quality context without parsing the full pattern-memory object.

GAR operational digests also expose contractor quality patterns through a role-gated `quality_signals` section. Super Admin, Admin, Property Manager and Assistant/Assistant Manager cover roles can see this summary. Contractor, member, resident, director and finance feeds do not receive the management-side contractor quality records.

The Phase 3 lifecycle check verifies the command-centre and contractor feed contract shape so future app work can rely on stable queue keys and GAR summary context.

## Permissions

Current management rules:

- Admin and Super Admin can manage company work orders.
- Assigned Property Manager can manage work orders for their assigned developments.
- Assigned Assistant can manage work orders for their assigned developments.
- Master Assistant / Assistant Manager can provide company-wide cover.
- Contractors can update assigned contractor workflow only.
- Members and residents can view permitted work and submit feedback or reopen requests, but cannot manage the platform work order state.

When Assistant Manager or Master Assistant cover is used, conversion and routing actions should be marked with the `assistant_manager_cover` access context. This keeps holiday cover, urgent cover and management override activity visible to audit history and GAR.

The work order lifecycle timeline should show this access context as a small audit pill where it applies. This lets reviewers see how an item moved through the platform without reading raw database metadata.

## Contractor Work Order Pack

Contractor Logix should let the assigned contractor open a dedicated work order pack before accepting or returning the job.

The contractor pack shows:

- work order title, type, status and description
- development, block/core, unit and address
- access notes where available
- PM, assistant, occupier/reporter and contractor contact details
- linked request evidence such as member images, videos or document references
- contractor-safe GAR relevant history
- lifecycle history for the assigned work order

Contractors can accept the work order from this pack, or return/reject it to Works Logix with a reason. Rejections create a lifecycle event and notify the relevant management users so the job can be reviewed or rerouted.

The downloadable work order PDF is controlled. It becomes available only after the contractor accepts the work order or the work order is further along the contractor lifecycle. This prevents a contractor from downloading a formal docket before taking responsibility for the job.

## Work Order Progress Updates

Active work orders can have progress updates before completion. This is a Contractor Logix action stored against the Works Logix work order.

Each progress update records:

- update note
- created by and created date
- visibility scope
- linked photos, videos or documents
- lifecycle event for audit and GAR context

Visibility is controlled per update:

- `Contractor Only`: visible inside Contractor Logix and GAR contractor context only.
- `Contractor + Management`: visible to the contractor and Works management users.
- `All Parties`: visible to the contractor, Works management users and the member/resident/reporter through Members Logix.

Progress updates are not completion evidence. They are an operational timeline for jobs that take time, need access, have delays, require interim attendance or need interim photos. Completion evidence remains the formal close-out submission.

## Member Request Triage

Members Logix maintenance requests must be reviewed before they are converted into Works Logix work orders.

PM, Assistant/APM, Admin and Super Admin users should open the request review screen from the Member Request Triage queue. The review screen shows the issue details, development, unit, reporter context, urgency and any linked photo, video, document or evidence reference.

The triage decision has three controlled outcomes:

- `Convert to Work Order`: use only when the issue is valid for the OMC or management company to progress. The user must select the contractor before conversion, so the work order is sent to the correct Contractor Logix queue immediately.
- `Ask for Information`: sends a message back to the member/resident and moves the request to `More Info Requested`.
- `Reject`: sends a clear decision message back to the member/resident and moves the request to `Rejected`.

Requests marked `More Info Requested` or `Rejected` should not remain in the live conversion queue. This prevents every member request from being treated as something that must become a work order.

The contractor selector is GAR-ready. It can show suggested routing context based on the request category, preferred contractor flags and current open workload. GAR suggestions are advisory only: PM/Admin/Assistant users still decide who receives the work.

Members can attach request evidence either by uploading a supported file or by pasting a secure evidence link. The evidence reference stays on the Maintenance Request and is copied into the Work Order evidence context if the request is converted.

When Works Logix asks for more information, Members Logix should open the member/resident into a dedicated Maintenance Request review page. That page shows the original issue, the Works Logix reply, linked unit/development context, evidence and a response form. The member/resident can add the requested clarification and attach another evidence file or secure link. Sending the response returns the request to `Pending` so it appears in the triage queue again.

## Evidence and Audit Pack

The work order review screen includes an Evidence and Audit Pack.

It brings together:

- source member request
- work order details
- contractor progress updates visible to management
- contractor completion
- member feedback
- reopen request history
- lifecycle events
- access context such as Assistant Manager cover actions

This gives PM/Admin users a clear source-backed view before approving, returning or reopening work.

The audit pack also includes a `completion_evidence` object. This is the shared evidence contract used by Works Logix, Contractor Logix, GAR AI and future mobile/app views.

It records whether completion has been submitted, whether notes are present, whether an evidence reference or media exists, attachment count, evidence reference type, quality status and review flags.

The quality status should guide review:

- `awaiting completion`: the contractor has not submitted completion yet
- `missing_evidence`: completion was submitted without usable evidence
- `needs_review`: completion exists but has review flags
- `review_ready`: completion notes and evidence are present

This does not replace PM/Admin judgement. It gives the reviewer a fast source-backed signal before deciding to approve, close or return the work order.

Member/resident reopen requests can include a dedicated evidence reference. If present, that reopen evidence is included in the Evidence and Audit Pack as Members Logix source evidence and remains attached to the reopen request record.

This gives PM/Admin a clear review trail when deciding whether to approve or reject a reopen request after a work order was closed.

Member/resident feedback can also include a dedicated evidence reference. If present, the feedback evidence is included in the Evidence and Audit Pack and shown in the Member / Resident Feedback section of the work order review screen.

This gives PM/Admin a clearer view of whether the contractor completion appears resolved from the member/resident side before approving, returning or reopening the work order.

The Evidence and Audit Pack contract is protected by:

```text
.\venv\Scripts\python.exe scripts\works_evidence_audit_contract_check.py
```

This confirms completion evidence, member request media, feedback evidence, reopen evidence, review-cycle flags, Assistant Manager cover context and GAR/source references stay in one stable audit shape.

## GAR Relevant History

The work order review screen also includes GAR Relevant History.

GAR checks previous work orders for the same unit, same block/core, same works category and similar title/description wording. It then summarises related prior work so PM/Admin users can see recurrence, previous outcomes, reopen history and contractor signals before deciding what to do next.

This does not replace the source work order. It is a read-only intelligence layer with source records behind it.

Management-side Works feeds also include a compact `gar_relevant_history` object on work order rows. This lets future PM/Admin/Assistant app views show the same recurrence and previous-outcome signal without rebuilding the logic in the client.

GAR also provides a routing recommendation. This is advisory only. PM/Admin still decide whether to assign the same contractor, choose a different contractor, inspect for root cause or hold the work for review.

In the Works command centre, rows with related history show a small `GAR history` chip. This lets users spot potentially recurring jobs before opening the full work order review screen.

The full Works command centre also shows a GAR Relevant History Review panel when related-history jobs are present. This gives PM/Admin/Assistant users a quick list of work orders where previous outcomes or recurrence should influence routing or closure review.

The command-centre JSON feeds include the same list under `gar.history_review`, so mobile/app clients can render the same decision-support panel without duplicating GAR matching logic.

## GAR AI Role

GAR reads the work order lifecycle and can summarise:

- current owner
- current stage
- missing evidence
- member dissatisfaction signals
- contractor progress updates by role visibility
- recommended next step
- audit signal
- repeated issue patterns
- whether Assistant Manager / Master Assistant cover was used in the current Works view

GAR does not close, reopen or return work orders by itself. Those actions remain governed inside Works Logix.

## Checks

The cross-module flow is protected by:

```text
.\venv\Scripts\python.exe scripts\works_lifecycle_flow_check.py
.\venv\Scripts\python.exe scripts\works_access_control_check.py
```
