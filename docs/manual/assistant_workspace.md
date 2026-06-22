# Assistant Workspace

Status: Phase 3 operating guide

Last updated: 2026-05-28

## Purpose

The Assistant Workspace supports operational follow-up, member request triage and contractor routing.

It is designed for:

- assigned assistants
- assistant property managers
- assistant managers
- master assistants
- senior assistant cover roles

## Normal Assistant View

In the normal view, an assistant sees developments where they are assigned as assistant or where they are acting for an assigned PM relationship.

They can:

- view assigned clients
- open the Works Logix queue
- review member maintenance requests
- convert valid requests into work orders
- route work orders to contractors
- monitor attention queues

## Cover Mode

Assistant Manager, Master Assistant, Assistant Lead and Senior Assistant roles can use company-wide cover mode.

Cover mode exists so urgent work does not stop when the assigned PM and assistant are unavailable at the same time.

In cover mode, the assistant can:

- see all company developments
- filter by client/development
- convert member requests
- route work orders
- review reopen queues through the Works flow

## Audit and GAR Context

When cover mode is used, routing actions are recorded with the access context:

```text
assistant_manager_cover
```

This means GAR, audits and later management reports can distinguish normal assigned routing from operational cover routing.

Assistant users also have a read-only GAR digest feed at `/assistant/gar/feed.json`.

Assigned assistants see only their assigned developments. Assistant Manager / Master Assistant cover users receive the wider company digest so they can route requests when local PM/assistant cover is unavailable.

Works Logix also sends operational management notifications to active Assistant Manager, Master Assistant, Assistant Lead and Senior Assistant users in the same company. This means new member requests, reopen requests, completion reviews and repeated-return quality reviews can still be seen by a cover user if the assigned PM and assigned assistant are unavailable.

Cover notifications use the same source-backed Notification Centre contract as ordinary PM/Admin notifications. They should be treated as continuity alerts, not a change of development ownership.

Cover notifications are included in the Phase 3D notification role visibility contract. The check proves Assistant Manager, Master Assistant, Assistant Lead and Senior Assistant users receive operational Works management alerts while ordinary unassigned assistants do not.

## Best Practice

Use cover mode for continuity, urgent items and holiday cover. Routine day-to-day work should stay with the assigned PM or assigned assistant where possible.

## Connected Modules

Assistant Workspace connects to:

- Client Manager for assigned developments
- Works Logix for queues and work order routing
- Members Logix for source maintenance requests
- Contractor Logix for contractor handoff
- GAR AI for operational context and audit explanation
