# Role Dashboard Surface Standard

Status: active UX architecture note

Purpose: keep every role dashboard aligned with the same LogixPM ecosystem feel while allowing each module to show role-specific work.

## Rule

Every primary dashboard should:

- use the shared `base.html` shell;
- show a clear module identity in the first panel;
- include the shared Notification Action Queue;
- include GAR where the role has a source-backed GAR context;
- provide one obvious path into the role's main work queue;
- avoid long duplicated lists when tile-driven queue pages are available.

## Current Role Surfaces

| Role | Main dashboard | Primary operational focus |
| --- | --- | --- |
| Super Admin | `/super-admin/dashboard` | Portfolio control, contracts, clients, Works, GAR |
| Admin | `/admin-portal/dashboard` | Admin operations and company Works queue |
| Property Manager | `/pm/dashboard` | Assigned developments, Works, notifications |
| Assistant | `/assistant/dashboard` | Assigned and cover queues |
| Finance | `/finance/dashboard` | Finance-visible clients, GAR finance readiness |
| Director | `/director/dashboard` | Governance, CAPEX, documents and GAR |
| Contractor | `/contractor/dashboard` | Job queue, calendar, dockets, quotes and invoice readiness |
| Members | `/members/dashboard` | Linked units, maintenance requests, member-visible GAR |

## Verification

Run:

```powershell
.\venv\Scripts\python.exe scripts\role_dashboard_surface_check.py
.\venv\Scripts\python.exe scripts\dashboard_review_login_check.py
.\venv\Scripts\python.exe scripts\operational_surface_render_check.py
.\venv\Scripts\python.exe scripts\key_site_info_contract_check.py
.\venv\Scripts\python.exe scripts\contractor_evidence_propagation_check.py
.\venv\Scripts\python.exe scripts\queue_surface_contract_check.py
```

The surface check is intentionally small. It confirms that dashboards stay on the shared shell and retain the key notification, GAR and operational entry points.

The login/render smoke check uses the seeded review accounts to confirm each role can log in, lands on the expected dashboard, and receives a complete `200` HTML page instead of a redirect or server error. It also opens the main operational pages behind those dashboards, including Works queues, Contractor calendar/queue pages, Client Manager, Team Manager and Members Works.

The operational surface render check goes one level deeper and opens representative record-backed pages: client profile, client unit/site tabs, key site information, unit detail, management work-order review, contractor pack, contractor job docket and member request detail.

The contractor evidence propagation check protects the media path from Members Logix into Works Logix and Contractor Logix. Member photos, videos and documents must become visible, clickable evidence in the contractor pack and job docket, while completion evidence remains openable for later review.

The Key Site Information contract protects the shared rich-text rules for access notes, safety instructions, contractor-facing guidance and embedded media. It checks that formatting is preserved, unsafe content is stripped, modals remain scrollable and editor changes are synced before saving.

The queue surface contract protects the operational queue pattern. Works Logix and Contractor Logix should use top-level tiles as focused queue entry points, keep filters compact, and avoid stacking every list on one long page.
