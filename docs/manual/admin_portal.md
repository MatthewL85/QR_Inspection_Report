# Admin Portal

Status: Phase 3 operating guide

Last updated: 2026-05-28

## Purpose

The Admin Portal is for operational admin users who need a practical working view without full Super Admin control.

## Current Scope

Admin users may need to:

- review assigned client support items
- assist with Works Logix queues
- support documents and communications
- view permitted client and unit information
- help maintain operational records

The Admin dashboard now shows the same source-backed Works Attention Queue used by Super Admin, Property Manager and Assistant dashboards. Admin users can open the Admin Works Logix command centre, review company member requests, convert valid requests into work orders and assign contractors through governed POST-only actions.

Admin users also have a dedicated repeated-returns view for contractor completion returns that need management review.

## Visibility Rule

Admin Portal access should be company-aware and role-aware. It should support operations without exposing unrestricted platform configuration.

Admin Portal routes are restricted to Admin users. Other management roles such as Super Admin, Property Manager and Assistant have their own role-specific workspaces and should not use Admin Portal as a bypass.

This access rule is protected by:

```text
.\venv\Scripts\python.exe scripts\admin_portal_access_contract_check.py
```

## Connected Modules

Admin Portal connects to:

- Client Manager
- Unit Information
- Works Logix
- Notifications
- GAR AI where permitted

## Works Logix

Admin Portal exposes:

- Works command centre: `/admin-portal/work-orders`
- Works feed: `/admin-portal/work-orders/feed.json`
- Repeated Returns review: `/admin-portal/work-orders/repeated-returns`

The feed is read-only and uses the same command-centre payload shape as the Super Admin, Property Manager and Assistant feeds. Actions such as converting member requests and assigning contractors remain POST-only.

Admin activity should carry the `admin` access context so lifecycle history, audit review and GAR can distinguish it from Super Admin, PM and Assistant actions.

## GAR Feed

Admin users have a read-only GAR operational feed at `/admin-portal/gar/feed.json`.

The feed is company-scoped and preserves the `admin` role context. It is intended for operational support, not full Super Admin configuration control.

The Admin dashboard also includes Ask GAR. It uses the standard source-backed inquiry contract and should answer only from permitted company records such as clients, units, works, documents, notifications and team support data. It should not expose Super Admin configuration control.
