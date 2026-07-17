# Contract Manager

Status: Phase 3 operating guide

Last updated: 2026-05-28

## Purpose

Contract Manager tracks PSRA contracts, renewal dates, expiry alerts, fee increases and governed contract records.

## Current Use

Users can review contract status by:

- expired contracts
- due in 30 days
- due in 60 days
- due in 90 days
- active contracts

The dashboard tiles should link into the filtered Contract Manager view and should exclude archived contracts from the main operational count.

## Review Behaviour

Archived contracts are retained for history and audit purposes. They should not be included as active operational contracts unless the user intentionally filters for archived records.

Completed or governed contract documents should not be altered or removed casually. Corrections should use a controlled renewal, amendment or archive workflow.

## Connected Modules

Contract Manager connects to:

- Client Manager through `client_id`
- Team Manager through assigned users
- GAR AI through contract risk, expiry and fee increase signals
- Finance Logix later through fee and budget planning

## GAR Source Query

GAR can now query Contract Manager source records for renewal and expiry questions.

The GAR contract source adapter returns operational counts for expired, 30-day, 60-day, 90-day and active contracts, plus attention records and source references.

Archived contracts are excluded from operational counts and retained only for history/audit review.

GAR does not yet read signed contract clauses or generate legal interpretation from documents. That will come through the future document extraction and governance workflow.
