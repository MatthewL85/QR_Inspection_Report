# Notifications

Status: Phase 3 operating guide

Last updated: 2026-05-28

## Purpose

Notifications give users a clear action queue across modules.

They should help users know what needs attention without forcing them to manually search each module.

## Current Notification Centre

The Notification Centre supports:

- unread and read summaries
- search
- priority action queue
- workflow stage labels such as Member Request, Contractor Assigned, PM Review, Reopen Requested and Renewal Alert
- workflow stage filtering and stage count chips for operational review
- audience labels so the user can see whether the alert is aimed at Works, Contractor, Members, Management or GAR review
- type filters
- GAR category filters
- suggested action filters
- direct links back to the relevant source screen
- a JSON feed that includes module, stage, audience and source target context for future app/mobile clients
- a service-backed notification feed contract at `/notifications/feed.json`

The shared top navigation notification bell uses the same notification service as the Notification Centre. It should show a compact unread count and recent unread notifications for the signed-in user only.

The navbar is an attention surface, not a separate notification system. It must not query a different source or expose another user's queue. Opening or marking notifications from the navbar must still use the governed notification routes. Navbar notification rows should use the same source-aware view objects as the Notification Centre so users see the module, workflow stage and source record consistently.

Role dashboards may show a compact Notification Action Queue. This should use the same unread, source-aware notification view objects as the navbar and Notification Centre. It is an attention surface only: users open or clear notifications through the governed Notification Centre routes.

The dashboard strip should show action-required unread notifications only. General unread informational notifications still belong in the navbar dropdown and full Notification Centre. This keeps dashboards focused on work that needs a decision, review or follow-up.

## Works Logix Notifications

Works-related notifications may point to:

- new member maintenance requests
- contractor assignment
- contractor completion review
- repeated returns quality review
- member feedback
- closed work order updates
- reopen requests

Links should take the user to the relevant source row or section, not just the top of a page.

Notification open targets must remain internal LogixPM paths. If a notification has an empty, malformed or external link, the platform should take the user back to their role dashboard instead of following that link. This keeps notifications as trusted operational prompts rather than open redirects.

Notification read actions also use governed internal return paths. Marking one or all alerts as read should preserve the current Notification Centre filters or return the user to the originating LogixPM screen, while external and malformed referrers are rejected.

When an alert is acknowledged, the platform records `read_at` as well as `is_read`. GAR, audit/reporting screens and future app clients should use this timestamp to explain when a user saw or cleared an operational prompt instead of inferring timing from the boolean status.

The notification feed summary exposes acknowledgement totals through `acknowledged_count` and `last_acknowledged_at`. This allows dashboards, app clients and GAR to distinguish between unread workload, read history and the most recent acknowledgement without changing notification records from a read-only feed.

The JSON notification feed keeps the original `link_url` for compatibility, but app/mobile clients should use `safe_link_url` or the governed notification open route. `safe_link_url` is always an internal LogixPM path or a safe fallback, so future mobile/PWA surfaces do not need to trust raw notification data.

Each notification feed item also includes a `source_reference` and `source_label`. These identify the primary source record behind the alert, such as a Work Order, Maintenance Request, Unit, Client or Contract. GAR, dashboards and app clients should use this shared source reference instead of rebuilding source labels from raw IDs.

The JSON feed also exposes `action_queue`, which contains the unread action-required notifications using the same safe payload shape as `notifications`. Future dashboards, app clients and GAR notification inquiries should use this field for decision queues instead of filtering the general notification list themselves.

The on-screen Priority Action Queue shows the same source label as the feed, so users can see which Work Order, Maintenance Request, Unit, Client or Contract sits behind an alert before opening it.

The feed includes a top-level `source_references` list as well as item-level source references. This gives GAR and future app clients a compact set of source records that support both the visible notification list and the unread action queue without walking every notification row.

When a contractor completion is returned more than once, management users should receive a `works_quality_review` notification. This is separate from the contractor-facing `works_returned` notification. It should link to the Repeated Returns quality review queue and include source context such as the work order, unit, client, return count and GAR repeated-return signal.

Works management notifications are sent to assigned PM/assistant users, Admin/Super Admin users and active Assistant Manager / Master Assistant cover users in the same company. Cover users receive the alert for operational continuity, while the source record and lifecycle audit still show whether the action was handled by an assigned user or by `assistant_manager_cover`.

## Role Visibility Matrix

Notifications are always recipient-scoped. A user should only see alerts created for their own user account.

The current Phase 3D visibility rules are:

| Role | Works management alerts | Own queue alerts | Finance/contract alerts | Notes |
| --- | --- | --- | --- | --- |
| Super Admin | Yes | Yes | Yes | Company-wide operational control. |
| Admin | Yes | Yes | Yes | Company-wide operational management. |
| Property Manager | Assigned developments only | Yes | As assigned | PM sees work linked to their assigned portfolio. |
| Assistant / Assistant Property Manager | Assigned developments only | Yes | No | Does not receive unassigned company-wide Works alerts. |
| Assistant Manager / Master Assistant / Assistant Lead / Senior Assistant | Company-wide cover alerts | Yes | No | Cover continuity for holidays, absence and urgent routing. |
| Finance users | No internal Works management alerts by default | Yes | Yes | Finance should receive finance, contract and portfolio financial alerts, not routine Works routing alerts. |
| Director | No internal Works management alerts by default | Yes | Governance/development scoped | Director visibility should remain development scoped. |
| Contractor | No | Assigned contractor job alerts only | No | Contractor sees their own job queue and contractor-facing returns. |
| Member / Owner / Resident | No | Own unit/request alerts only | Own permitted data only | Members see their submitted requests, linked work orders, closure and reopen updates. |

The notification role visibility contract is checked by:

```text
.\venv\Scripts\python.exe scripts\notification_role_visibility_contract_check.py
```

This check creates a live Members Logix request and confirms Works management alerts go to assigned PM/assistant, Admin/Super Admin and active assistant cover roles only. It also confirms unassigned assistants, inactive cover users, finance, directors, contractors, members and other-company admins do not receive those internal Works management alerts.

## GAR AI Role

GAR can classify notifications by:

- action required
- workflow stage
- intended audience
- risk category
- source module
- recommended next action

GAR should help prioritise the queue but should not hide source records from users.

The notification feed is read-only and uses the same notification intelligence service as the on-screen Notification Centre. Phase 3 readiness checks verify its context type, summary keys, filters and workflow-stage counts so mobile clients can depend on a stable payload.

The notification intelligence contract is also checked independently by:

```text
.\venv\Scripts\python.exe scripts\notification_contract_check.py
```

This protects the workflow-stage labels, audience labels, action-required classification, source-target payload keys, read-only feed route and POST-only mark-read actions. It gives future app screens and GAR panels a stable notification shape without depending on the full Works lifecycle smoke test.

The navbar notification contract is checked by:

```text
.\venv\Scripts\python.exe scripts\navbar_notification_contract_check.py
```

This confirms the shared navbars use the source-backed notification context, link to the Notification Centre and keep mark-all-read as a POST action.

## GAR Notification Source Query

GAR can now answer permitted action-queue questions from the current user's own notification records.

The GAR notification source query can summarise unread, acknowledged, action-required, high-priority and GAR-related notifications. It also returns workflow stage and module counts so future dashboard and mobile surfaces can show a clear operational queue.

This is recipient-scoped. GAR should not expose another user's notifications or perform actions such as marking notifications as read from the inquiry response.
