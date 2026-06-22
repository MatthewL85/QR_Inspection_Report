# Client Manager

Status: Phase 3 operating guide

Last updated: 2026-05-28

## Purpose

Client Manager is where developments and client records are created, reviewed and maintained.

It is the source for:

- client name
- property name
- address and location
- client type
- development structure
- contract and assignment summary
- assigned property manager
- assigned financial controller
- assigned assistant

## Opening Client Manager

Super Admin users open Client Manager from the dashboard or navigation.

The page lists active client records in a lighter table view with the key review fields visible without horizontal scrolling.

## Client Review Fields

The Client Manager list should show:

- client
- property name
- address and location
- structure
- team
- contract value
- contract dates
- next fee increase
- extras

## Filtering and Export

Client review reporting should support filters such as:

- location
- contract date
- next fee increase month
- value order

The export report should be used during portfolio reviews, contract reviews and management company performance checks.

## Connected Modules

Client Manager connects to:

- Unit Information through `client_id`
- Works Logix through client-level work order filters
- Contract Manager through client contract records
- GAR AI through development health and source context
- Team Manager through assigned user IDs

## Important Rule

Do not duplicate unit, owner, resident, finance or works data inside the client record. The client record should link to those areas through source IDs.
