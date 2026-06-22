# Members Logix

Status: Phase 3 operating guide

Last updated: 2026-06-21

## Purpose

Members Logix is the owner, co-owner, tenant and resident facing part of the ecosystem.

It must be mobile-first and app-ready because many users will interact from a phone.

## Current Works Flow

Members and residents can:

- view their permitted maintenance information
- see a short Next Actions strip for feedback, reopen tracking, requests and live works
- see the same Members Logix Next Actions signal on the member dashboard
- consume a read-only member works feed at `/members/works/feed.json` for future app/mobile clients
- consume a read-only GAR member/resident feed at `/members/gar/feed.json`
- ask GAR source-backed questions from the dashboard and maintenance page
- submit a maintenance request
- add description and context
- include media references for photos or videos
- see linked open and closed work orders where permitted
- see member-safe contractor completion evidence status
- provide feedback after contractor completion
- add feedback evidence such as a photo, video, document or secure link
- request a reopen if the issue was closed but not resolved
- add a reopen evidence reference such as a photo, video, document or secure link

## Visibility Rules

Members Logix must keep owner and resident data separated.

Examples:

- An owner can see owner-related unit information.
- A tenant or resident should not see owner-only finance or ownership details.
- A co-owner should be linked to the relevant unit ownership record.
- Social housing bodies, investment companies or portfolio owners may later need a portfolio view across their linked units.

## Portal Access Codes

Members should not manually enter the internal `unit_uid`. That value is a permanent platform identifier and should remain system-controlled.

The safe member-facing workflow is:

1. A Super Admin creates a portal access code from the unit or client Unit Information section.
2. The code is linked to one unit, one client, a role and, where possible, the owner's email address.
3. The member signs into Members Logix.
4. The member enters the portal code in Add another property.
5. The system creates or updates the controlled UnitMembership link for that user.

If the member owns multiple units, they should claim one portal code per unit. After claiming, all permitted units appear in the same Members Logix portal.

The current Phase B workflow creates, tracks and can email portal codes. Email delivery is recorded on the UnitAccessInvite record with delivery status, sent date, send count and last delivery error.

If email delivery fails, the code is not lost. The invite remains visible in the client Unit Information tracking table and can be sent again after email configuration is corrected.

Invite emails should include the full login URL generated from the live application request or configured public base URL. Members should not be sent internal-only or relative links.

Future magic-link access should be added later on top of the same UnitAccessInvite records.

## Mobile and App Readiness

Members Logix should keep:

- touch-friendly actions
- clear request status
- short forms
- readable work order history
- notification hooks
- media evidence support
- future PWA or native app compatibility

## Connected Modules

Members Logix connects to:

- Unit Information through unit ownership and occupancy records
- Works Logix through maintenance requests and work order visibility
- Notifications through member/resident alerts
- Finance Logix through future owner-visible balances
- GAR AI through role-aware summaries

## Important Rule

Members Logix should not duplicate the work order record. It should show the permitted status and allow feedback or reopen requests through Works Logix services.

The member dashboard and the Members Works page use the same member Works context so request counts, open work orders, reopen tracking, feedback prompts and Next Actions stay aligned.

The member works feed is also powered by this same context. It returns linked units, member requests, permitted work orders, reopen requests, attention queues and Next Actions.

Work orders in the Members Works screen and feed include a member-safe `completion_evidence` summary. It tells the member/resident whether contractor completion has been submitted, whether evidence is recorded, the evidence type, attachment count and a review hint.

Detailed completion notes or evidence links should only be visible to the member/resident if the completion record explicitly allows member, resident or owner visibility and is not access-masked. This keeps member feedback useful while protecting contractor/admin-only evidence where required.

Reopen requests also support a dedicated `evidence_reference`. This should be used when a member/resident says the issue was not resolved and wants to provide supporting photos, video or documents. The reopen evidence remains attached to the reopen request source record and is visible in the member feed and Works Logix review flow.

Member/resident feedback also supports a dedicated evidence reference. This should be used when the member wants to support their feedback after contractor completion, especially where the issue is only partly resolved or not resolved. Feedback evidence remains attached to the feedback source record and is visible to Works Logix review users.

It is read-only. Creating requests, submitting feedback and requesting reopen remain controlled by Members Logix routes and Works Logix services.

The Phase 3 readiness check verifies this member feed contract so future mobile/app work can rely on the same payload shape as the live Members Logix screen.

The GAR member/resident feed is unit-membership scoped. It identifies whether the current user is acting as a member/owner or resident-only user, then exposes only linked unit, maintenance, reopen and feedback signals appropriate for that relationship.

## Ask GAR

The Members Logix dashboard and Members Works page include an Ask GAR panel.

This panel uses the GAR inquiry contract, but Works questions are routed through the member works source adapter. GAR can answer from the current member's linked units, submitted maintenance requests, visible open/closed work orders, feedback prompts and reopen requests.

GAR must not answer from company-wide Works Logix records for a member/resident. It must not expose other member records, owner-only finance information, management-only quality review signals or private data from unrelated units.
