# Director Logix

Status: shell operating guide

Last updated: 2026-05-28

## Purpose

Director Logix will give OMC directors role-appropriate visibility over governance, development health, works summaries, compliance and future approvals.

## Future Scope

Directors should be able to see:

- assigned developments
- governance summaries
- key site information
- compliance status
- open works summaries
- GAR AI governance recommendations
- director approvals where permitted

## Visibility Rule

Director access must be role-aware and client-aware. Directors should not automatically see private owner, resident or staff information unless policy allows it.

## Connected Modules

Director Logix connects to:

- Client Manager
- Unit Information
- Works Logix summaries
- Finance Logix summaries
- GAR AI governance context

## GAR Feed

Directors have a read-only GAR governance feed at `/director/gar/feed.json`.

The current feed is company-scoped and uses the `director_governance` role context. Future phases should replace this with precise director appointment/client membership scoping once Director Logix governance records are expanded.

The Director dashboard also includes Ask GAR for source-backed governance questions. It should be used for governance, compliance, document metadata, contract and Works summary questions only. It does not yet replace board packs, appointment-level access control or formal approval workflows.

## GAR Governance Source Query

GAR can now answer permitted governance attention questions from structured source records.

The current governance source query can summarise:

- client governance attention flags
- compliance document expiry and review status
- AGM records
- CAPEX requests and projects

This does not yet replace Director Logix board packs, director appointment scoping, document extraction, or formal approval workflows. Those should be built as dedicated Director Logix and Documents module services, with GAR reading from them rather than owning them.
