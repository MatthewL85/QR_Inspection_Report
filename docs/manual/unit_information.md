# Unit Information

Status: Phase 3 operating guide

Last updated: 2026-06-21

## Purpose

Unit Information is the property asset spine for a development.

Units are real database records linked to a client/development. They are not just a visual list.

Each unit can later connect to:

- Members Logix
- Works Logix
- Finance Logix
- Contractor Logix
- Director Logix
- GAR AI

## Creating Units

Units are generated from the development structure entered on the client record.

The normal flow is:

1. Create or edit the client/development.
2. Enter the development structure.
3. Save the client.
4. Open the client profile.
5. Use Generate Unit Information.
6. Review generated units in the Unit Information section.

The generate process is idempotent. Running it again should not create duplicate units.

## Unit Information Section

The client profile displays a Unit Information section with tabbed owner and resident directories.

The section should support:

- Owner's Directory and Resident's Directory tabs
- block/core filter tabs
- search by unit, owner, resident, block/core, phone or email
- the Unit Number field as the primary link to the unit record, not the Unit Code or unit label
- block and core as separate columns

The Owner's Directory shows:

- unit number
- block
- core
- owner name
- owner phone
- owner email
- Members Logix portal access indicator
- Finance Logix balance where an outstanding balance record exists
- occupancy as a compact visual status
- unit status as a compact visual status

The Resident's Directory shows:

- unit number
- block
- core
- resident or tenant name
- resident or tenant phone
- resident or tenant email
- Members/Resident Logix portal access indicator
- letting agent indicator linked to the unit letting-agent tab
- open Works Logix work order count linked to the unit Works tab
- open Members Logix request count linked to the unit Works tab

The resident directory deliberately does not show occupancy or unit status columns. It is focused on who is in occupation and whether there is any live operational activity for that unit. If a unit is owner-occupied and no separate resident record exists, the Owner's Directory details also appear in the Resident's Directory because the owner is the occupier.

The section also includes Members Logix portal invite controls:

- Generate Unit Information creates the unit records.
- Bulk Invite Members creates portal access codes for owner records with email addresses.
- Email Pending Invites sends pending portal codes to owner email addresses.
- The invite tracking table shows the latest unit, email, role, portal code, status, delivery state, expiry and action.
- Existing pending or claimed invites are not duplicated.
- Owner records already linked to a portal user are skipped.
- Delivery failures are retained against the invite so Super Admin can correct email configuration or owner data and resend.
- Pending invites can be cancelled if they were created for the wrong owner, wrong email address or wrong unit.

Bulk invites are intended for a full development launch after owner data has been added. Single unit invite creation remains available from the Unit Detail page for property sales, new owners and one-off corrections.

## Unit Detail Page

The unit detail page shows:

- owner and contact summary
- development
- block and unit number
- service charge balance placeholder
- occupancy
- sale and conveyancing status when selected
- Works summary
- detailed tabs for unit, owner, residents, letting agent, car park, service charge history, Works, documents and GAR AI

## Edit Unit Page

Core unit details are static setup information. They should only be changed by Super Admin or a highly authorised role.

Core fields include:

- client/development
- unit label
- unit number
- block
- area
- unit category
- unit type
- floor
- car park space number
- storage or locker number

Editable operational areas are separated into tabs:

- Ownership and Occupancy
- Letting Agent Details
- Current Tenant / Occupier
- Sale and Conveyancing
- Status and Financial
- Notes / Special Conditions
- AI / GAR Governance

## Connected Modules

Unit Information connects to:

- Members Logix for owners, co-owners, tenants and residents
- Works Logix for work orders and maintenance requests
- Finance Logix for service charges and balances
- GAR AI for unit context and recommendations

## Important Rule

A generated unit belongs to one client/development. The client link should not be casually reassigned from the edit unit page because other modules depend on that relationship.
