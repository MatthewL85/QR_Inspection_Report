# Contractor Logix

Status: Phase 3 operating guide

Last updated: 2026-06-26

## Purpose

Contractor Logix is the contractor-facing job and compliance area.

It should be mobile-first and app-ready because contractors will often use it in the field.

## Current Works Flow

Contractors can:

- view assigned work orders
- filter their job queue
- see a short Next Actions strip prioritising returned work, new assignments and active work
- see the same contractor Next Actions signal on the Contractor Logix dashboard
- consume a read-only contractor work queue feed at `/work-orders/feed.json` for future app/mobile clients
- consume a read-only GAR contractor feed at `/contractor/gar/feed.json`
- ask GAR source-backed questions from the Contractor Logix dashboard
- accept assigned work
- start work
- add progress updates with photos, videos or documents
- submit completion notes
- submit evidence reference
- resubmit returned completion work

When a Members Logix request is approved by Works Logix triage, the PM/Admin/Assistant selects the contractor before conversion. The created work order is assigned immediately, so it appears in the selected contractor's queue without needing a second routing step.

## Calendar-Centred Job Dockets

Contractor Logix is being shaped around the operational flow:

Work Order -> Accept -> Job Docket -> Assign -> Schedule -> Complete -> Report -> Invoice.

When a contractor accepts a work order, Contractor Logix now creates a real Job Docket linked back to the Works Logix work order. This gives the contractor an operational record without moving ownership of the original work order out of Works Logix.

Contractor Logix also supports standalone job dockets. This is for contractors who use Contractor Logix even when the instructing property manager, client or management company does not use LogixPM. A contractor can create a docket manually from a phone call, email, WhatsApp message, site instruction or another external system.

Standalone dockets use the same Job Docket and Contractor Calendar workflow as connected Works Logix jobs. They capture the client/customer name, property/site, address, block/core/unit or area, contact details, access notes, trade/category, priority, scope of works, optional contractor job number and optional source/external work order reference. They do not require a linked Works Logix work order.

The contractor job number is the contractor's internal reference. The source/external work order reference is for a WO, ticket or instruction number received from another management company, email, client system or other communication channel.

This keeps Contractor Logix independently useful while preserving future connection readiness. If that client later joins LogixPM, historic standalone dockets can be linked to the proper organisation connection rather than being lost in a separate workflow.

Accepted job dockets appear in the Contractor Calendar as an Unscheduled Job Queue until the contractor assigns an engineer/team and chooses a calendar slot.

Each job docket has its own operational detail page. The page shows the linked work order, schedule, engineer/team assignment, site and contact information, scope of works, evidence, contractor updates and the shared Works Logix lifecycle. This separates the contractor's operational file from the pre-acceptance work order pack while keeping both records linked.

The contractor dashboard links scheduled and overdue operational tiles into the mobile-ready Today's Jobs view at `/contractor/today`. This view groups scheduled job dockets into Today, Overdue and Upcoming, shows the field essentials for each visit, and links directly to the job docket or update area. It is designed as the first engineer-friendly schedule surface before the later full mobile app build.

Once a job is accepted and scheduled, the Job Docket page becomes the contractor's main field workspace. Contractors can start the job, add progress updates, upload multiple photos/videos/documents and submit completion notes from the docket itself. The original Work Order Pack remains available for pre-acceptance review and PDF download, but active job handling should happen from the Job Docket.

Scheduling a job docket:

- records the scheduled date/time
- assigns the engineer and/or team
- creates a Contractor Calendar entry
- changes the job docket and linked work order to `Scheduled`
- writes a lifecycle event for Works Logix and GAR context

The Contractor Calendar has an `.ics` feed. This allows the schedule to be opened or subscribed to from Outlook, Google Calendar, Apple Calendar and phone calendars. This is the Phase 1 integration approach because it is standard, lightweight and avoids prematurely adding full OAuth/two-way sync. Later phases can add direct Google/Microsoft calendar connections, conflict detection, drag-and-drop scheduling and GAR scheduling recommendations.

The Contractor Calendar also exposes a read-only app feed at `/contractor/calendar/feed.json`. This feed returns the contractor-scoped unscheduled dockets, scheduled entries, today, overdue and upcoming schedule data for future mobile Contractor Logix clients. It does not mutate records; all operational actions still route through Contractor Logix web actions and Works Logix services.

When a contractor schedules a job docket, Works Logix management views show the scheduled visit beside the open work order. PM/Admin/Assistant users can therefore see the planned attendance date, time and engineer from the Works command centre without entering Contractor Logix.

For standalone job dockets, scheduling creates the Contractor Calendar entry without updating Works Logix. This is intentional because there may be no connected LogixPM company on the other side.

## Future GAR Email Intake

Standalone job dockets are designed for a future premium email intake product.

The future flow should be:

Email instruction -> GAR extracts a draft -> Contractor reviews -> Job Docket created -> Schedule -> Complete -> Report -> Invoice.

Each contractor company could have a unique intake email address. Incoming emails and attachments would be saved as intake records. GAR would read the sender, subject, body and attachments, then draft the same structured fields used by the standalone job docket form. At first, GAR should prepare a draft for human approval rather than automatically creating live jobs. Trusted automation can be added later for known clients and low-risk instruction types.

## Updates

Contractors can add updates while a work order is active. Updates can be marked as either `Progress Update` or `Completion`.

Progress updates are used for access issues, attendance notes, delays, interim findings, photos or videos before final completion.

Completion updates are used when the contractor believes the works are complete and wants the item submitted for PM/Admin review. A completion update creates/updates the Works Logix completion evidence pack, moves the work order to `Completion Submitted`, and keeps the formal PM/Admin approve-or-return flow intact.

Each update has a visibility choice:

- Contractor Only
- Contractor + Management
- All Parties

Completion defaults to `All Parties`, but the contractor can change visibility where appropriate. Only `All Parties` updates are shown to the member/resident/reporter in Members Logix. Management users can see management-visible updates in the Works Logix review pack. Contractor-only updates remain inside Contractor Logix and contractor-safe GAR context.

Ordinary progress updates do not replace completion submission. A contractor should use the `Completion` update type when the job is ready for PM/Admin review.

## Returned Work

If PM/Admin reviews completion and returns it, the item should go back into the contractor queue with review notes.

The contractor can then add more information, correct the issue and resubmit completion.

Returned work rows should show a compact return context, including the PM/Admin reason, returned date and reviewer where available.

This return context comes from the Works Logix lifecycle event, not from a separate contractor-only note. The same return context is included in the contractor work queue feed as `return_context` so future mobile/app clients can show exactly what needs to be corrected before resubmission.

The contractor work queue also includes a `review_cycle` signal. It shows completion submissions, returns and resubmissions so returned work does not become vague or hidden once a job has bounced back for correction.

## Completion Evidence

Contractor Logix should show a compact evidence status beside submitted, returned and completed jobs.

The status comes from the shared Works Logix `completion_evidence` object, not from a separate contractor-only calculation. This keeps the contractor queue, PM/Admin review screen, GAR AI and future mobile/app views aligned.

In Phase 3, contractors can submit notes, upload multiple photos/videos/documents at once and add an evidence reference such as an external secure link. Uploaded evidence is stored against the completion source record and included in the same Works Logix evidence pack used by PM/Admin review, GAR and future app clients.

## Visibility Rules

Contractors should only see work assigned to them or their contractor organisation.

Contractors should not see:

- owner-only information
- unrelated client data
- unrelated work orders
- finance ledgers
- internal PM/Admin notes unless specifically shared

## GAR AI Role

GAR can later support Contractor Logix by identifying:

- missing completion evidence
- repeated returns
- contractor performance patterns
- overdue jobs
- risk signals

GAR should read source records and make recommendations. Contractor performance records should remain owned by Contractor Logix and Works Logix.

In Phase 3, GAR can flag an early contractor quality risk where source records show repeated completion returns or low member/resident feedback. This should support management review and future Contractor Logix design, but it should not be treated as a final contractor performance score.

## App Readiness

The contractor work queue feed returns only the current contractor user's permitted work order queues, stats and Next Actions.

It is read-only. Contractor actions such as accept, start and submit completion remain controlled by Contractor Logix routes and Works Logix services.

The GAR contractor feed is also read-only and contractor-scoped. It gives GAR the contractor's assigned, active, returned and submitted work signals without exposing owner-only, resident-only or finance information.

## Ask GAR

The Contractor Logix dashboard includes an Ask GAR panel.

This panel uses the GAR inquiry contract, but Works questions are routed through the contractor work queue source adapter. That means GAR can answer from assigned contractor work records, returned work, submitted completion evidence and contractor-safe relevant history only.

GAR must not use the management Works command centre for contractor-facing answers. Contractor Ask GAR should not expose company-wide work orders, owner/resident private details, finance records or management-only contractor quality review records.

## GAR Relevant History on Jobs

Contractor Logix now shows a contractor-safe GAR history summary beside job lifecycle tracking.

This helps the contractor understand previous related work without giving them unrestricted historic access. The summary can include previous issue type, outcome, completion notes and recurrence signals. It must not expose owner finance data, private resident/member details or PM/Admin-only notes.

The same compact signal is included in the contractor work queue feed as `gar_relevant_history` so future mobile/app clients can show the same context on the job docket.
