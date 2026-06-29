# Core Platform

Status: Phase 3 operating guide

Last updated: 2026-06-26

## Purpose

The Core Platform holds the shared identity, company, document, notification and audit foundations used by every LogixPM module.

## What It Owns

- users
- roles
- companies and organisations
- shared documents and media
- audit logs
- notifications
- shared navigation and UI shell
- organisation identity and module subscriptions
- governed organisation connection invites

## User Impact

Most users do not work directly inside the Core Platform. They experience it through login, role access, navigation, alerts, settings and shared profile data.

## Important Rule

Operational modules should link to core records by ID. They should not create separate user, company or document records for their own isolated use.

## Organisation Identity

Every company/organisation has a permanent platform identity called an organisation UID. This is used behind the scenes so LogixPM can recognise the same management company, contractor company, HR organisation or other connected business across modules.

Users should not normally need to type or remember this UID. Setup screens should show plain company names and controlled invite codes.

The Company Profile page shows the organisation UID, enabled module count and active connection count. This is the day-to-day setup surface for confirming that the organisation is ready to operate independently and connect to other Logix modules.

The same setup state is built by the Core Platform readiness service, so the Company Profile, future module onboarding screens and GAR can all use one source of setup truth instead of duplicating logic in each module.

The same readiness state is also available to authenticated app clients through the read-only `/app/company-setup/feed.json` feed. This feed is for display, onboarding and GAR context only; module subscriptions and organisation connections still change through governed setup actions.

## Module Subscriptions

Each organisation can have one or more enabled modules, such as Property Management, Contractor Logix, Members Logix, HR Logix, Finance Logix or GAR.

This lets an organisation use one module independently, then add another module later without creating a second identity.

## Connecting Organisations

When two organisations need to work together, the platform should use a controlled connection invite.

Example:

1. A contractor company buys Contractor Logix.
2. The contractor receives its own organisation identity.
3. A management company sends or accepts a connection invite.
4. Once accepted, the two organisations can share only the approved connected records, such as assigned work orders and job dockets.

Email can be used to deliver an invite, but the email address is not the permanent link. The accepted organisation connection is the controlled link.

## Super Admin: Organisation Connections

Super Admin users can open Organisation Connections from the Super Admin sidebar or dashboard.

Use this page to:

- confirm the current organisation UID
- enable module subscriptions for an organisation
- link contractor profiles to their organisation identity
- create a connection invite code
- accept a received connection invite code
- review pending invites and active organisation links

This is the controlled setup area for future independent module purchases. For example, a contractor using Contractor Logix can be connected to a management company using LogixPM without duplicating company records or using email as the source of truth.

Contractor profiles should be linked to their real organisation identity before they are used for connected Works Logix routing. When a new contractor user is created from a linked contractor profile, the user inherits that organisation link.

## Works Logix Routing Impact

When a work order is routed to a contractor, the platform now checks whether the contractor belongs to a connected organisation.

If a connection exists, the work order stores the organisation connection ID. This allows the job docket, contractor updates, completion evidence, GAR summaries and future finance links to know which two organisations are allowed to share that job information.

Legacy contractors can still be selected during this build phase, but connected contractors are marked in the routing selector and should become the preferred setup route.

## GAR Visibility Rule

GAR should only use records the logged-in user is allowed to see. If GAR answers questions across companies, that visibility must come from active module subscriptions, role permissions and accepted organisation connections.
