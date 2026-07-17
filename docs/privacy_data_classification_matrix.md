# Privacy and Data Classification Matrix

Status: active privacy and data handling contract

Purpose: define how LogixPM classifies personal, operational, financial, HR, contractor and AI-readable data across modules.

## Core Rule

Every field, document, media item, feed and GAR source must have a clear data classification and module owner before it is shared across a dashboard, API, export, document template, notification or AI answer.

Access to a module does not automatically mean access to every data class inside that module. Role, organisation, source record, visibility and purpose must all match.

## Data Classification Levels

| Level | Meaning | Examples | Default Handling |
| --- | --- | --- | --- |
| Public / Published | Information intentionally visible to a broad authorised audience | Published key site instructions, approved contractor access rules, published emergency procedures | Visible only through the authorised module surface |
| Internal Operational | Day-to-day business information for staff or authorised partners | Work order status, contractor routing, job docket schedule, site access notes | Visible to roles involved in the workflow |
| Personal Data | Identifies a person or their contact details | Owner names, resident names, phone numbers, email addresses, correspondence addresses | Purpose-limited and role-scoped |
| Sensitive Personal Data | Higher-risk personal or employment information | HR notes, absence, performance reviews, access needs, vulnerable resident notes | Module-owned, minimal access, audited |
| Financial Data | Money, balances, charges, invoices, payments and supplier/payment records | Service charge balance, debtor list, invoice, payment request, budget spend | Finance-owned unless explicitly surfaced by a governed feed |
| Contractor Private | Information belonging to the contractor company only | Materials used, private time logs, internal job notes, contractor labour costs | Contractor Logix only unless converted to a shared document |
| Governance / Legal | Board, director, contract, compliance, AGM or legal records | Contracts, leases, votes, compliance certificates, insurance, licences | Role-scoped, retained and audited |
| Security / Access | Physical or digital access control information | Gate codes, key safe codes, alarm information, API tokens, portal invite codes | Strictly purpose-limited, rotated when compromised |
| Derived AI Data | GAR summaries, recommendations, risk signals and answer metadata | GAR digest, previous issue summary, contractor recommendation reason | Source-backed, role-aware and never source of truth |

## Module Handling Matrix

| Module | High-Risk Data It Owns | Sharing Rule |
| --- | --- | --- |
| Core Platform | User identity, roles, sessions, organisation links, notification metadata and audit IDs | Shared only as identity and permission context |
| Property Management Logix | Client setup, contracts, key site information, team assignments and unit structure | Shared through governed role surfaces and service feeds |
| Members Logix | Owner, co-owner, resident, tenant and portal access data | Residents must not see owner-only or finance-only information |
| Works Logix | Member requests, reporter details, work order evidence, routing and reopen records | Contractors see only what is needed for assigned work |
| Contractor Logix | Contractor schedules, job dockets, completion evidence, private logs and contractor documents | Contractor private logs remain contractor-only |
| Finance Logix | Debtors, budgets, invoices, balances, payments and accounting sync data | Finance-owned; other modules receive summary/status feeds only |
| Director Logix | Director approvals, governance decisions, voting and board-visible documents | Director-visible but still client/organisation scoped |
| HR Logix | Staff personal data, leave, performance, disciplinary and employment records | HR-owned and never exposed to non-HR modules by default |
| GAR AI Layer | Source references, summaries, recommendations and answer metadata | GAR may only reveal what the user can open directly |

## Privacy Rules

- Personal data must be shown only for a clear operational purpose.
- Residents and tenants must not see owner-only information unless they are also verified owners or authorised representatives.
- Contractors may receive reporter contact details only where needed to arrange access or complete assigned work.
- Contractor private materials, time logs and internal notes must not be shown to PM, Admin, Members, Directors or Finance unless deliberately converted into a shared invoice/payment document.
- Finance data must not be copied into general dashboards as raw balances, ledgers or debtor lists without a Finance-owned feed and role check.
- HR data must stay in HR Logix unless a minimal, authorised employment identity feed is explicitly required.
- Key site security information must be scoped by role, contractor assignment and operational need.
- Portal invite codes, organisation connection tokens, API keys and OAuth credentials are security data, not ordinary text fields.
- GAR must not infer or expose personal, financial, HR or contractor-private details from free text if the current user could not access the source record.

## Export, Notification and AI Rules

- Exports must inherit the same role and organisation visibility as the source screen.
- Notifications should reveal the minimum useful detail and link back to the authorised source record.
- PDF/document templates must not include hidden sensitive fields because they are convenient.
- GAR summaries must cite or retain source references and respect data classification.
- External integrations must receive only the data class and scope needed for the integration purpose.

## Red Flags

Stop and route the work through stabilisation if any of these appear:

- a dashboard shows owner, resident, debtor, HR or contractor-private data because the user is generally logged in;
- a contractor can see unrelated owners, residents, units, financial balances or HR information;
- a resident can see owner correspondence, service charge debt, director decisions or contractor private logs without a specific authority;
- GAR answers with personal, financial, HR or contractor-private data that the user cannot open in the source module;
- an export includes more columns than the screen is authorised to show;
- key safe, gate, alarm, token or invite-code information is treated as normal operational text;
- Finance or HR data is duplicated into another module instead of exposed through a governed source-backed feed.

## Guarded By

Primary checks:

```powershell
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\gar_role_visibility_contract_check.py
.\venv\Scripts\python.exe scripts\gar_source_adapter_contract_check.py
.\venv\Scripts\python.exe scripts\notification_role_visibility_contract_check.py
.\venv\Scripts\python.exe scripts\works_access_control_check.py
.\venv\Scripts\python.exe scripts\phase3_runner_contract_check.py
```
