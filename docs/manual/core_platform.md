# Core Platform

Status: Phase 3 operating guide

Last updated: 2026-07-11

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

The company setup feed also lists the governed setup action contract. These actions show where Super Admin users can enable modules, link contractor profiles to organisation identities, create connection invites and accept connection invites. The feed itself remains read-only: every setup change must use the listed POST route, CSRF protection and Super Admin permission checks.

## Module Subscriptions

Each organisation can have one or more enabled modules, such as Property Management, Contractor Logix, Members Logix, HR Logix, Finance Logix or GAR.

This lets an organisation use one module independently, then add another module later without creating a second identity.

## Module Settings Registry

The platform now has a Module Settings Registry at `Settings -> Module Settings`, plus a governed connection surface at `Settings -> Connections`.

This registry defines how settings should be split across the ecosystem:

- Core Platform owns shared foundations such as users, roles, companies, organisation identity, module subscriptions, organisation connections, document template engine, notifications and audit logs.
- Each module owns its own operational settings. Contractor Logix owns contractor job docket, calendar, engineer/team and payment request settings. Finance Logix owns finance, invoice and ledger settings. Members Logix owns portal and member/resident access settings. HR Logix owns staff and HR document settings.
- If modules are purchased or used separately, each module can expose only its own settings.
- If modules are connected, the user should see one Settings Centre grouped by module, with the Core Platform providing the shared identity and connection layer.
- Document templates are grouped by the module that creates the document, even when another module reviews or receives it.

This prevents settings from becoming tangled together while still making the connected platform feel like one system.

The same registry is available to authenticated app clients and future GAR setup surfaces through the read-only `/app/module-settings/feed.json` feed. The feed exposes module ownership, standalone/connected readiness, shared links, document template ownership and the settings mutation policy.

Important: this feed is discovery only. It does not change settings. Module settings changes must go through the owning module's governed route, with authentication and CSRF protection.

The registry also applies role-aware settings visibility. Super Admin and Admin users can see the full combined registry. Property management company users see management-side settings only and do not get Contractor Logix operational settings. Contractor users see Contractor Logix settings and shared Core/GAR context only. Members, residents and directors see only the module context relevant to their portal/governance role. This keeps standalone module setup independent while still allowing a connected Settings Centre for authorised management users.

Each standalone module should expose a reciprocal connections area inside its own settings. The Core Platform still owns the underlying organisation UID, module subscription and organisation connection records, but the user experience should sit where the user expects it.

Current module-local connection surfaces:

- Contractor Logix: `/contractor/settings/connections`
- Finance Logix: `/finance/settings/connections`
- HR Logix: future `/hr/settings/connections` when HR Logix moves beyond the foundation shell

Contractor Logix settings should show the contractor organisation UID, active management-company links, pending connection codes and the ability to enter a received code. Finance Logix should show native Logix finance links and future accounting/payment adapter readiness. HR Logix should later show HR module links and future HR/payroll adapter readiness.

`Settings -> Connections` is the shared setup surface for connected organisations. It lets authorised management users enable native Logix modules for the selected organisation, generate one-time connection codes, accept received codes and see future external connector readiness. Standalone module settings can reuse the same connection controls, but they should only show the actions relevant to that module.

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

Management users can also open the lighter settings-owned view from `Settings -> Connections`.

Use this page to:

- confirm the current organisation UID
- enable module subscriptions for an organisation
- link contractor profiles to their organisation identity
- create a connection invite code
- accept a received connection invite code
- review pending invites and active organisation links

This is the controlled setup area for future independent module purchases. For example, a contractor using Contractor Logix can be connected to a management company using LogixPM without duplicating company records or using email as the source of truth.

Contractor profiles should be linked to their real organisation identity before they are used for connected Works Logix routing. When a new contractor user is created from a linked contractor profile, the user inherits that organisation link.

## External Connectors

External systems such as Sage, Xero, QuickBooks, HR Manager, Microsoft 365, Google Workspace or other cloud HR/finance systems should not be treated as native Logix modules.

The recommended structure is:

1. Native Logix modules connect through organisation UID, module subscriptions and organisation connections.
2. External products connect through a module-owned integration adapter.
3. The adapter stores only the controlled connection metadata, credentials/token reference, sync direction, mapping rules and audit state.
4. GAR can read connector status and mapped source records when permissions allow, but GAR should not hold the credential or become the source of truth.

For example, if a company later adds Finance Logix, that module is enabled as a native module subscription. If the same company wants Sage, Finance Logix should own a Sage connector under Finance settings. If a company later adds HR Logix, that module is enabled as a native module subscription. If it wants HR Manager, HR Logix should own the HR Manager connector under HR settings.

## Works Logix Routing Impact

When a work order is routed to a contractor, the platform now checks whether the contractor belongs to a connected organisation.

If a connection exists, the work order stores the organisation connection ID. This allows the job docket, contractor updates, completion evidence, GAR summaries and future finance links to know which two organisations are allowed to share that job information.

Legacy contractors can still be selected during this build phase, but connected contractors are marked in the routing selector and should become the preferred setup route.

## GAR Visibility Rule

GAR should only use records the logged-in user is allowed to see. If GAR answers questions across companies, that visibility must come from active module subscriptions, role permissions and accepted organisation connections.
