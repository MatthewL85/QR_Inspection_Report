# Contractor Logix

Status: Phase 3 operating guide

Last updated: 2026-05-28

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

## Progress Updates

Contractors can add progress updates while a work order is active. This is used for access issues, attendance notes, delays, interim findings, photos or videos before final completion.

Each update has a visibility choice:

- Contractor Only
- Contractor + Management
- All Parties

Only `All Parties` updates are shown to the member/resident/reporter in Members Logix. Management users can see management-visible updates in the Works Logix review pack. Contractor-only updates remain inside Contractor Logix and contractor-safe GAR context.

Progress updates do not replace completion submission. Completion evidence is still required when the contractor is ready to submit the job for PM/Admin review.

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
