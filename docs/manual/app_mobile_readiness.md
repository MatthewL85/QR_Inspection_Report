# App / Mobile Readiness

Status: Phase 3E operating guide

Last updated: 2026-06-17

## Purpose

App and mobile readiness is the foundation for making LogixPM usable from phones, tablets, installed PWA surfaces and future native app shells.

This is not a separate mobile product. It uses the same database, same permissions, same source records, same notifications and same GAR role-aware context as the web platform.

## Operating Rules

1. App/mobile views must use the same source of truth as the web platform.
2. App/mobile read-only display contracts should come from governed feed endpoints.
3. Creating, approving, returning, closing, reopening or routing work must remain on governed POST routes and service functions.
4. The service worker caches static shell files only. It must not cache work orders, member records, finance data, documents or GAR answers as offline business records.
5. Members Logix and Contractor Logix should remain mobile-first and app-ready because those users are most likely to work from phones.
6. GAR app surfaces must be role-aware and source-backed, not model-only shortcuts.

## Current App Shell

The current shell gives LogixPM the first install-ready layer:

- `app/static/manifest.webmanifest` defines the install metadata, app name, theme colour and icons.
- `/app-shell-sw.js` serves the service worker from the root scope.
- `app/static/app-shell-sw.js` caches static shell assets only.
- `app/static/js/register_app_shell.js` registers the service worker without blocking login or dashboards.
- Shared layouts include the manifest, app icon and mobile web app metadata.

This gives future PWA/native wrapper work a clean starting point while protecting live operational workflows.

## App-Ready Feeds

The app/mobile layer should use read-only feeds for display and dashboard context.

Current key feeds include:

- `/app/health/feed.json`
- `/app/home/feed.json`
- `/app/capabilities/feed.json`
- `/notifications/feed.json`
- `/members/works/feed.json`
- `/members/gar/feed.json`
- `/contractor/work-orders/feed.json`
- `/contractor/gar/feed.json`
- `/super-admin/work-orders/feed.json`
- `/super-admin/gar-insights/feed.json`

These feeds expose source-backed information for screens, notifications and GAR context. They should not be used to mutate data.

The app health feed is the lightweight bootstrap check for future PWA/native clients. It confirms the app shell is reachable, the active app contract versions, the service worker and manifest endpoints, the read-only/governed runtime rules, and GAR's source-backed operating mode. It can be called before login, but business feeds still require an authenticated server session.

The app home feed is the role-aware bootstrap feed for future PWA/native clients. It tells the client who is signed in, what modules are available, where the governed feeds live, how many notifications need attention and which GAR/Works surfaces are permitted for that role.

The app home feed also exposes role-aware quick actions. These are not shortcuts around governance. GET actions may open screens or GAR inquiry endpoints, while POST actions are metadata only and must be submitted through the owning module route with CSRF protection and the required record context.

Each quick action includes an action contract for mobile clients: owning module, required context fields, online-only behaviour, confirmation requirements, evidence-reference support and server-authoritative handling. Contractor completion, member maintenance requests and member reopen requests must never be queued offline or sent without the owning module's record context.

The app home feed also exposes an `app_policy` section. This tells future PWA/native clients that the app must use an authenticated server session, enforce role visibility server-side, keep offline caching to the static shell only, treat feeds as read-only, send mutations through governed POST routes, use evidence references for media at this stage, and keep GAR source-backed and role-aware.

The app home feed also exposes an `app_scope` section. This is the signed-in user's data boundary contract. Management roles operate inside their company/client portfolio, contractors operate inside assigned Contractor Logix work, and members/residents operate inside linked member units. App clients must treat this as display guidance only; server-side filters and role checks remain the authority for all company, client, unit, contractor and GAR visibility.

The app home feed also exposes an `app_navigation` section. This is the role-aware bottom-tab contract for future PWA/native screens. It defines Home, Alerts, Works and GAR navigation items when the signed-in role is allowed to see them, and badge counts come from the same notification summary used by the web platform.

The app home feed also exposes an `app_surfaces` section. This is the role-aware screen registry for future PWA/native screens. Each source-backed surface declares its module, URL, feed key, layout, empty state, online requirement, safe-area requirement and pull-to-refresh support so the app can show the right screens without hard-coding module behaviour.

The app home feed also exposes an `app_deep_links` section. This is the safe app routing contract for opening dashboards, alerts, Works queues, GAR and capabilities from notifications or quick actions. Deep links must be relative-path links created by the server, not guessed by the client. Unsafe schemes such as javascript, data, file and non-allowlisted external links are blocked. Notification targets must remain source-backed, role-checked, support return targets and keep mark-read actions on governed POST routes.

The app home feed also exposes an `app_session` section. This is the app session contract for server-session cookie authentication, CSRF handling, device identity and logout. App clients must treat the server session as the authority, send CSRF tokens on governed mutations, treat client device IDs as diagnostics or future push targets only, redirect to login when business feeds become unauthenticated, and clear cached business state after expiry or logout.

The app home feed also exposes an `app_notifications` section. This is the app notification contract for badges, in-app delivery, future push readiness and read actions. Phase 3E uses in-app notification feed delivery now and push later. Badge counts come from `notification_summary`, notification records remain recipient-scoped and source-backed, opening a notification uses a safe target, and mark-read / mark-all-read remain POST-only CSRF-protected actions.

The app home feed also exposes an `app_resilience` section. This is the app resilience contract for offline display, stale feed warnings, HTTP error handling, mutation failure, GAR degraded mode and user-facing messages. The app may show the cached static shell offline, but business feeds and mutations are unavailable until the session is online again. Stale feeds should show a warning, source records must be refetched after failed mutations, server stack traces must never be shown to users, and GAR must not fall back to model-only answers when source records are missing.

The app home feed also exposes an `app_observability` section. This is the privacy-safe diagnostics contract for future app support and performance monitoring. It allows health, feed latency, screen load, static shell cache and mutation timing signals, but it must not include business payloads, GAR answers, document text or personal contact details. App support references may include contract versions and role context, but not raw user or company identifiers.

The app home feed also exposes an `app_compatibility` section. This is the app compatibility and version governance contract for responsive web, installed PWA and future native app clients. The server remains the authority for supported contract bundles, feed versions and feature flags. Clients must check the health feed, refresh capabilities when contract versions change, keep old clients in a read-only safe state when needed, and never enable features that are not listed by the server capabilities feed.

The app home feed also exposes an `app_sync` section. This is the mobile refresh and offline contract. It tells the app to use session-bound polling, refresh priority alerts faster than slow-changing capability metadata, cache only the static shell, keep business records and GAR answers out of offline storage, require the user to be online for operational actions, and refetch from the server after governed mutations.

The app home feed also exposes an `app_media` section. This is the mobile evidence contract for photos, videos, documents and secure evidence references. Phase 3E supports online multi-file uploads for member maintenance request evidence, member request responses, contractor progress updates and contractor completion evidence. Offline upload queueing remains disabled. Evidence remains online-only, CSRF-protected, role-visible and tied to the owning source record. Secure evidence references remain supported alongside uploaded files, using `MediaFile` as the source model marker for the future dedicated upload service.

The app media contract supports four governed evidence contexts: member maintenance request evidence, contractor completion evidence, member work order feedback evidence and member reopen request evidence. Each context declares its owning module, action key, related table and required context fields so the app cannot submit loose media without a unit, work order, request, feedback or completion record. GAR may process evidence only after the source record exists and must keep parsed summaries, extracted data and classifications source-backed.

The app capabilities feed is the read-only capability map for future PWA/native clients. It exposes module contracts, app-ready module signals, GAR capability readiness, app policy, app session rules, app notification rules, app resilience rules, app observability rules, app compatibility rules, app media rules, the same source-backed surfaces, the safe deep-link contract and source references. It should be used by app clients to decide which surfaces to show, what diagnostics are allowed and which versioned features are safe to enable, not to make business decisions or mutate records.

## Mobile Surface UX Contract

App-ready screens must declare their mobile surface contract in the template. Members Works, Contractor Work Queue, Notification Centre and the GAR ask panel now mark themselves as `data-app-mobile-ready`, `data-app-source-backed` and `data-app-offline="static-shell-only"`. Full app surfaces also mark safe-area support so installed PWA and future native shells can respect phone browser chrome and not hide buttons behind device controls.

The mobile surface check verifies quick navigation, safe-area CSS, touch-friendly app navigation, source-backed GAR panels and the static-shell-only offline rule. This is a UX quality gate: app screens should remain light, scannable and touch-safe while still using the same governed source records as the desktop platform.

## App Action UX Contract

Mobile actions must be explicit, online-only and source-record governed. Members Logix app actions include creating a maintenance request, adding work order feedback and requesting a reopen. Contractor Logix app actions include accepting a work order, starting work and submitting or resubmitting completion evidence. Each action form declares `data-app-action`, requires online use, requires CSRF, disables offline queueing and identifies the source record such as a unit or work order.

This prevents a future app shell from treating operational actions like ordinary offline form drafts. Requests, feedback, reopen requests and contractor completion evidence must go through the owning governed route, with the server record remaining authoritative and GAR reading the resulting source record afterwards.

## Evidence Reference Handoff

Phase 3E evidence fields support a mixed model: online multi-file uploads where implemented, plus secure reference fields for external evidence links. The app-facing forms mark evidence inputs with `data-app-media-reference`, `data-app-media-context`, `data-app-media-source-model="MediaFile"` and `data-app-direct-upload` metadata where applicable. This keeps member request photos, member feedback evidence, reopen evidence and contractor completion evidence aligned with the `MediaFile` source model that will be introduced later.

Where upload storage is available, users can attach multiple files in one action. Where a workflow still uses reference-only evidence, users can provide secure photo, video or document links. The platform records uploaded file URLs and evidence links on the owning source record, keeps offline upload queueing disabled, and lets GAR read the evidence only through the governed source record and audit trail.

Compatibility note: the original Phase 3E contract described `evidence-reference now, MediaFile later`, no `direct binary uploads` and no `full upload storage`. That remains true for the future dedicated MediaFile service and offline/native upload queue. The current implementation adds governed online file uploads for selected workflows, but full upload storage as a platform-wide media service is still a later MediaFile build.

## How To Use On Mobile

Mobile users should start from the same authenticated LogixPM session as desktop. The app shell may load while offline, but live records, actions and GAR answers require an online server session.

Members and residents use Members Works to submit a maintenance request, track live work orders, review closed work and request a reopen when the issue is not resolved. They can upload multiple files for maintenance requests and request responses, and can add secure evidence links to new requests, feedback and reopen requests. Those actions remain linked to their unit and visible only within their permitted member/resident scope.

Contractors use the Contractor Work Queue to accept assigned work, start work, submit completion notes and resubmit returned completion evidence. GAR history is shown from source records so contractors can understand prior related work without seeing private owner/resident information outside the assigned job.

Management users use the Notification Centre and Works Command Centre to review action queues, route work, review completion evidence, return work to contractors, approve closure and monitor GAR signals. Mobile notifications should be treated as navigation into the owning record, not as a replacement for the source workflow.

GAR on mobile follows the same role-aware rules as desktop. Users can ask questions from the visible module surface, but GAR must answer from permitted source adapters and source references. If the source record is missing, GAR should show that the answer is unavailable rather than inventing an answer.

## Workflow Actions

Operational actions remain controlled by the owning modules:

- Members Logix creates maintenance requests, feedback and reopen requests.
- Contractor Logix accepts work and submits completion evidence.
- Works Logix routes, returns, approves and closes work orders.
- Notifications show attention and workflow stage but do not replace the source record.
- GAR can explain, summarise and recommend from permitted records, but GAR does not close, reopen, approve or route work by itself.

## GAR Mobile Behaviour

GAR mobile/app surfaces should follow the same rules as desktop:

- show only data allowed for the signed-in role
- answer from source-backed adapters
- keep member/resident answers scoped to their linked units
- keep contractor answers scoped to assigned jobs
- keep management answers scoped to authorised client/company records
- never expose another user's notifications or private data

## Readiness Check

The focused Phase 3E app/mobile readiness gate is checked by:

```text
.\venv\Scripts\python.exe scripts\phase3e_app_readiness_check.py
```

This runs the app feed, shell, health, home, capabilities, mobile surface and manual contracts as one app/mobile close-out suite.

The app shell readiness contract is checked by:

```text
.\venv\Scripts\python.exe scripts\app_shell_readiness_check.py
```

This verifies the install metadata, service worker route, static shell registration and the core read-only app feeds.

The app health feed contract is checked by:

```text
.\venv\Scripts\python.exe scripts\app_health_feed_contract_check.py
```

This verifies the app bootstrap status, anonymous safety, signed-in role echo, runtime rules, contract versions, GAR mode and source references.

The app mobile surface contract is checked by:

```text
.\venv\Scripts\python.exe scripts\app_mobile_surface_check.py
```

This verifies the first app-ready operational screens keep quick mobile navigation, source-backed GAR panels and consistent app surface markers across Members Logix, Contractor Logix and Notifications.

The app home feed contract is checked by:

```text
.\venv\Scripts\python.exe scripts\app_home_feed_contract_check.py
```

This verifies the role-aware app bootstrap feed preserves the signed-in user, permitted modules, governed feed links, notification summary, quick actions, app policy, priority action queue and source references.

The app capabilities feed contract is checked by:

```text
.\venv\Scripts\python.exe scripts\app_capabilities_feed_contract_check.py
```

This verifies the app capability map preserves module contracts, GAR capability readiness, app policy, source references and read-only route behaviour.
