# GAR AI

Status: Phase 3 operating guide

Last updated: 2026-05-28

## Purpose

GAR is the General Artificial Resident.

GAR is intended to become the intelligence layer across LogixPM, not a basic chatbot.

GAR should understand:

- clients and developments
- blocks, cores, units and common areas
- owners, co-owners, residents and tenants
- Works Logix lifecycle history
- contractor performance signals
- contracts and renewal risk
- finance summaries and future arrears/service charge data
- compliance documents
- governance records
- audit history

## Current GAR Areas

The current build includes:

- GAR context services
- portfolio context
- client context
- unit context
- work order context
- development health register
- Works intelligence signals
- operational digest feed for portfolio, development health and Works attention
- source references
- role-aware context structure

## How Users Should Use GAR

GAR should be used to:

- summarise a development
- highlight risk
- identify missing actions
- explain work order status
- identify when cover access or operational override context was used
- support review decisions
- recommend next steps
- show source records behind its answer

## What GAR Should Not Do Yet

GAR should not:

- replace the source record
- silently change work order status
- alter governed documents
- expose data outside role permissions
- invent facts without source records

## Source-Backed Principle

Every GAR answer should be able to point back to source records such as:

- client
- unit
- work order
- member request
- lifecycle event
- contract
- document
- finance record
- audit log

No hidden magic. No invented data. No recommendation without context.

## Works Cover Context

When Assistant Manager or Master Assistant cover is used in Works Logix, GAR should preserve the `assistant_manager_cover` context from lifecycle events.

GAR can then explain that a work order was routed under operational cover rather than normal assigned PM/assistant handling. This is important for holiday cover, escalation review and later performance reporting.

## Operational Digest

GAR now exposes a source-backed operational digest at `/super-admin/gar-insights/feed.json`.

The digest combines:

- portfolio counts
- development health
- Works attention signals
- assistant cover context
- issue pattern memory
- priority actions
- source references

This is read-only. It gives the future GAR interface and app surfaces one stable operational feed without taking ownership away from Clients, Units, Works Logix, Contracts or Compliance.

Role-scoped digest feeds exist across all current user types:

- Super Admin: `/super-admin/gar-insights/feed.json`
- Admin: `/admin-portal/gar/feed.json`
- Property Manager: `/property-manager/gar/feed.json`
- Assistant: `/assistant/gar/feed.json`
- Finance: `/finance/gar/feed.json`
- Director: `/director/gar/feed.json`
- Contractor: `/contractor/gar/feed.json`
- Member / Resident: `/members/gar/feed.json`

Role-scoped inquiry endpoints also exist for app/mobile clients and future GAR chat surfaces:

- Super Admin: `/super-admin/gar-insights/inquiry.json`
- Admin: `/admin-portal/gar/inquiry.json`
- Property Manager: `/property-manager/gar/inquiry.json`
- Assistant: `/assistant/gar/inquiry.json`
- Finance: `/finance/gar/inquiry.json`
- Director: `/director/gar/inquiry.json`
- Contractor: `/contractor/gar/inquiry.json`
- Member / Resident: `/members/gar/inquiry.json`

Each inquiry endpoint accepts `question` and returns the same source-backed inquiry envelope used by the dashboard Ask GAR panels. These endpoints are read-only and must not perform workflow actions.

The source-adapter contract is now protected by:

```text
.\venv\Scripts\python.exe scripts\gar_source_adapter_contract_check.py
```

This check makes sure every query-ready GAR domain has a declared source adapter. It also confirms that Finance Logix questions such as debtors, budget spend, arrears, invoice, payment and ledger queries remain blocked from live answers until Finance Logix owns validated source query services.

These feeds preserve role context and client visibility. A Property Manager receives only their assigned developments. An Assistant receives assigned developments, while Assistant Manager / Master Assistant cover users can receive the wider company operational view for cover handling. Financial Controllers receive their assigned finance developments, while broader Finance users receive the company finance view where permitted.

Admin and Director feeds use company/development governance scope until deeper director-specific appointment records are built. Contractor feeds are contractor-queue scoped and do not expose owner, resident or finance data. Member and resident feeds are unit-membership scoped and separate owner/resident visibility so GAR can support future mobile and app surfaces without breaking privacy boundaries.

Role visibility is protected by:

```text
.\venv\Scripts\python.exe scripts\gar_role_visibility_contract_check.py
```

This check confirms contractor, member and resident GAR access does not expose management-only contractor quality records, finance records, other member records, team-directory data, contract control or governance data where the role is not permitted.

Operational GAR digests now include a compact `quality_signals` section. Contractor quality patterns are visible only to Works management roles such as Super Admin, Admin, Property Manager and Assistant/Assistant Manager cover. Contractor, member, resident, director and finance role contexts do not receive contractor-quality risk records through this digest.

## Relevant Works History

GAR now adds relevant history to work order context. It compares previous work orders by unit, block/core, works category and text similarity, then creates:

- a PM/Admin source-backed history section on the work order review page
- a contractor-safe summary on the Contractor Logix work queue
- a routing recommendation to help PM/Admin decide whether to reuse previous contractor context, check recurrence, or review a reopen pattern before assignment

Contractors receive operational history only: previous issue type, outcome, completion summary and recurrence signals. GAR must not expose owner finance data, private member/resident details or internal-only notes through this contractor summary.

## Capability and Readiness Layer

GAR now has a capability registry at:

```text
/super-admin/gar-insights/capabilities.json
```

This registry tells the platform what GAR can answer from source-backed records today and what must wait for a module service to be completed.

The endpoint can also classify a question:

```text
/super-admin/gar-insights/capabilities.json?question=Tell%20me%20the%20debtors%20in%20Matthew%20Lavery
```

This is important because GAR must not pretend that a live answer is available where the underlying module is not query-ready.

The role-aware GAR feeds also include the same capability metadata:

- `/super-admin/gar-insights/feed.json`
- `/admin-portal/gar/feed.json`
- `/property-manager/gar/feed.json`
- `/assistant/gar/feed.json`
- `/finance/gar/feed.json`
- `/director/gar/feed.json`
- `/contractor/gar/feed.json`
- `/members/gar/feed.json`

Each feed accepts an optional `question` query parameter. The response then includes `answer_readiness` for that role. This lets future GAR chat, dashboard and app screens show the right answer boundary without duplicating logic.

Current readiness rules:

- Platform setup, enabled modules and organisation connections are source-backed for Super Admin/Admin users.
- Clients, developments and units are source-backed.
- Works Logix questions are source-backed, including relevant-history summaries.
- Contract renewal and expiry questions are partially source-backed.
- Finance Logix has many model foundations, but GAR must not answer live debtor, arrears, spend-against-budget, payment or ledger questions until Finance Logix has validated query services and role-gated finance visibility.
- Documents and AI extraction remain partial until document ingestion, extraction, source citation and approval workflows are complete.

Example:

If a user asks `Tell me the debtors in Matthew Lavery`, GAR should recognise this as a Finance Logix question but return that live answers are not ready yet. Once Finance Logix owns validated debtor, budget, invoice, payment and ledger services, GAR can answer that question by citing those source records.

## Inquiry Contract

GAR now has a standard inquiry contract at:

```text
/super-admin/gar-insights/inquiry.json?question=What%20open%20work%20orders%20are%20linked%20to%20this%20unit
```

This endpoint does not generate free-form AI text. It returns the safe answer envelope that future GAR chat, dashboard and mobile/app surfaces should use before showing an answer.

The response includes:

- `response_status`
- `answer_ready`
- `safe_message`
- `readiness`
- `source_policy`
- `source_query`
- `source_references`

Current response statuses:

- `ready_for_source_query`: GAR can route to the owning module's source query service before producing an answer.
- `not_query_ready`: GAR recognises the question, but the module is not safe for live answers yet.
- `permission_blocked`: the role should not receive that data.
- `needs_question`: no question was provided.
- `needs_source_adapter`: the domain exists, but a source query adapter still needs to be built.

The source policy always requires source records, source references and role visibility. Model-only answers are not allowed.

In the response envelope this is expressed as `allow_model_only_answer: false`. Future GAR screens, chat surfaces and mobile clients should treat that as a hard rule, not a display preference.

Source references should be structured enough for a user or later AI layer to trace the answer back to the owning record. Each ready source-query adapter should return references with a model name, record id field and source field list.

GAR can answer setup-readiness questions from the Core Platform source records. For example, a Super Admin can ask which modules are enabled, whether the organisation UID exists, how many active organisation connections exist and whether connection invites are pending. These answers come from `Company`, `ModuleSubscription`, `OrganisationConnection`, `OrganisationConnectionInvite` and the module contract registry. GAR must not create invites, enable modules or connect companies directly from this answer surface; those remain governed setup actions.

For notification questions, GAR should use the Notification Centre source references. This means an alert can be traced back to the underlying Work Order, Maintenance Request, Unit, Client, Contract or other source record instead of only citing the notification message itself.

## First Source Query Adapter: Works Logix

Works Logix is now the first GAR inquiry source adapter.

When a Works question is sent to the inquiry endpoint, GAR can execute the Works source query and return:

- a source-backed safe summary
- Works stats
- next actions
- GAR Works attention signals
- relevant-history review records
- compact open work order records
- compact completion-review records
- completion evidence quality signals
- compact open member request records
- source references

This means GAR can start answering operational Works questions from real Works Logix data rather than from free-form model memory.

Finance questions remain behind the Finance Logix readiness gate until debtor, budget, invoice, payment and ledger query services are complete.

Works completion records expose a shared `completion_evidence` object to GAR. GAR can use this to identify missing notes, missing evidence references, attachment counts, evidence type and review readiness.

GAR should use this evidence pack to support PM/Admin review, contractor follow-up and member/resident visibility. GAR should not create completion evidence, approve work, close work orders or reopen work orders by itself.

Member/resident reopen requests can also include source evidence. GAR can use this as context when summarising unresolved issues, repeated defects or reopen-review priority, but the approve/reject decision remains inside Works Logix.

Member/resident feedback can include source evidence too. GAR can use this to understand whether the completion was accepted, questioned or supported by additional member evidence, but GAR must not alter the feedback record or make the closure decision.

Returned contractor completions expose a source-backed return context from the Works Logix lifecycle event. GAR can use this to explain why a completion was returned and what the contractor needs to address, but GAR must not rewrite return reasons or resubmit work on behalf of a contractor.

GAR can also read the Works review-cycle signal for completion submissions, returns and resubmissions. This helps GAR identify when a job is moving normally through review versus when repeated returns may indicate unclear evidence, contractor performance concerns or a recurring defect pattern.

GAR Works Intelligence now treats repeated completion returns as a source-backed signal. If a contractor completion is returned more than once, GAR can surface it in operational queues, role digests and development health context, while the approve/return/close decision remains inside Works Logix.

When shown in the Works command centre, the repeated completion return GAR signal should route users to the dedicated Repeated Returns quality review queue. GAR identifies the pattern, but the user still reviews the Works evidence pack before deciding what to do next.

GAR Works Intelligence can also produce a contractor quality risk pattern from repeated completion returns and low member/resident feedback. This helps management review routing choices and contractor outcomes, but it is not a full Contractor Logix performance score and should not automatically block a contractor.

The management operational digest exposes this through `quality_signals.contractor_quality`. This gives dashboards and future app clients a clean role-gated summary without needing to parse full GAR pattern memory. The source remains Works Logix lifecycle events and contractor feedback records.

The Super Admin GAR AI Centre displays the same contractor quality review signal as a management panel when records exist. The panel links to the Repeated Returns queue so users can inspect evidence, review-cycle history and member/resident feedback before making any operational decision.

GAR can now recognise management questions such as "Which contractors have repeated returns or low feedback?" as Works Logix questions. For permitted management roles, the source query returns the contractor quality records, repeated-return work order records and source references. Contractor role queries do not receive the management-side contractor quality records.

The Super Admin GAR AI Centre includes an Ask GAR panel. This panel uses the same source-backed inquiry contract as `/super-admin/gar-insights/inquiry.json`: it classifies the question, routes to the owning source adapter where available, shows whether the answer is ready, and displays source references. It does not produce model-only answers.

Admin, Property Manager, Assistant, Finance and Director dashboards also include the same Ask GAR panel. Admin questions use company operational scope without Super Admin configuration control. Property Manager questions are scoped to assigned developments. Assistant questions are scoped to assigned developments unless Assistant Manager / Master Assistant cover access is active, in which case the cover queue uses the wider permitted company context. Finance questions are scoped to finance-visible developments and still block live debtor, arrears, budget, payment or ledger answers until Finance Logix query services are ready. Director questions use the `director_governance` context and should remain governance-focused until Director Logix has precise appointment/client membership scoping.

Contractor and Members Logix dashboards now include Ask GAR panels too, but they do not use the management Works command-centre adapter. Contractor Works questions route through the contractor queue source adapter, which returns only assigned, active, returned, submitted and closed jobs for that contractor profile. Member/resident Works questions route through the member works source adapter, which returns only linked units, submitted requests, visible work orders, feedback prompts and reopen requests for that member profile.

This separation is important. GAR can be multi-faceted across the ecosystem, but external-facing users must receive source-backed answers from their own lane only.

## Client and Unit Source Query Adapter

GAR now also has a source adapter for Clients, Developments and Units.

When a user asks a development or unit-structure question, GAR can identify the named development where possible and return:

- client identity
- property name and client code
- recorded source structure
- generated unit count
- block/core/area breakdown
- occupancy breakdown
- unit type breakdown
- compact unit records
- owner and resident link counts
- source references

This adapter intentionally does not return contact details or finance details.

Privileged management roles can receive owner/resident names in compact unit records. Contractor-facing use keeps names hidden and returns only counts. Finance details remain owned by Finance Logix and must come through finance-specific query services later.

## Contract Manager Source Query Adapter

GAR now has a source adapter for Contract Manager renewal and expiry questions.

When a permitted user asks a contract question, GAR can return:

- expired contract count
- contracts due within 30, 60 and 90 days
- active contract count
- missing end-date count
- archived contract count
- attention contract records
- active contract records
- renewal metadata
- source references

Archived contracts are excluded from operational counts. They remain available as retained history only.

This adapter covers structured renewal and expiry intelligence. It does not yet extract or reason over signed contract clauses; that remains part of the future document extraction and governance workflow.

## Team Manager Source Query Adapter

GAR now has a source adapter for Team Manager and user-directory questions.

When a permitted Super Admin or Admin asks a team question, GAR can return:

- active user count
- inactive user count
- role breakdown
- active role breakdown
- contact fields captured in Team Manager
- client assignment gaps for PM, Financial Controller and Assistant roles
- basic security readiness signals such as verified email and two-factor enabled counts
- source references

This adapter is intentionally limited to the core platform user and assignment records.

It does not include HR leave records, staff performance records, policy acknowledgements or employment document intelligence. Those must come from HR Logix once that module owns the proper records and workflows.

Contractors, members and residents should not receive Team Manager directory access through GAR. Their GAR visibility should remain scoped to their own contractor queue, unit membership or permitted development data.

## Governance Source Query Adapter

GAR now has a source adapter for governance and compliance attention questions.

When a permitted user asks which developments need governance or compliance attention, GAR can return:

- developments with GAR governance/compliance attention signals
- expired client compliance document count
- compliance documents expiring within 90 days
- compliance documents needing human review
- upcoming and recent AGM records
- open and critical CAPEX requests
- open CAPEX projects
- source references

This adapter is read-only and uses structured records only.

It does not extract full document text, reason over signed clauses, expose owner/resident private data, include finance ledger values, or claim director appointment scoping. Those remain later module builds owned by Documents, Finance Logix and Director Logix.

## Document Metadata Source Query Adapter

GAR now has a source adapter for document metadata questions.

When a permitted user asks which documents are expiring or need review, GAR can return:

- general document counts
- client compliance document counts
- client/unit media file counts
- exported report/file log counts
- expired document/media item counts
- items expiring within 90 days
- items needing manual review
- parsing/GAR-readiness status
- source references

This adapter is metadata-only. It does not return file paths, full document text, extracted JSON payloads, legal interpretation, invoice extraction or lease-clause analysis.

Contractor-facing document intelligence should be added later through Contractor Logix so contractor compliance documents are scoped to the contractor and their work queue.

## Notification Source Query Adapter

GAR now has a source adapter for notification and action-queue questions.

When a user asks what needs their attention, GAR can summarise that user's own notification queue from source records:

- unread count
- action item count
- high-priority count
- GAR-related count
- module and workflow-stage counts
- action queue records
- recent unread records
- source references

GAR also receives acknowledgement metadata from the Notification Centre source contract, including how many notifications have been acknowledged and the latest acknowledgement timestamp. This lets GAR explain attention history without marking notifications as read or taking workflow actions itself.

This adapter is recipient-scoped and read-only. GAR must not expose another user's notifications, mark items as read, open links, or take workflow actions directly from this query.
