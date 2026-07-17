# Active Route Inventory

Status: Phase 2 architecture control document

Purpose: record which route groups are active in the current app-factory build before any legacy route files are archived or removed.

Generated/check command:

```text
.\venv\Scripts\python.exe scripts\architecture_route_inventory.py
```

## Active Blueprint Groups

The current app factory registers these active blueprint groups:

| Blueprint | Role |
| --- | --- |
| `auth` | Login, logout, profile, email verification, password reset and security flows |
| `settings` | Company profile, branding, bank, insurance, emergency and license settings |
| `super_admin` | Super Admin dashboard, client manager, team manager, compliance, AGMs, GAR insights and audits |
| `property_manager` | Property Manager dashboard area |
| `contractor` | Contractor dashboard, settings, compliance upload and safe placeholder destinations |
| `director` | Director dashboard, settings and safe placeholder destinations |
| `finance` | Finance Logix shell, dashboard and client manager |
| `assistant` | Assistant workspace shell and assigned client manager |
| `admin_portal` | Admin role shell and support client manager |
| `members` | Members Logix shell and linked unit dashboard |
| `equipment` | Equipment route placeholder/current endpoint |
| `capex` | CAPEX response review and decision endpoint |
| `tenant` | Tenant/onboarding route area |
| `unit_bp` | Unit list, unit detail, unit edit, work order/reopen views |
| `client_key_info` | Client key site information workflow |
| `super_admin_contracts` | Contract Manager overview, renewals, archive and alert sync |
| `super_admin_simple_contracts` | New/edit contract workflow |
| `devtools` | Development tooling endpoint |

## Critical Active Endpoints

These endpoints are protected by `scripts/architecture_smoke_check.py`:

| Endpoint | Why it matters |
| --- | --- |
| `auth.login` | User access starts here |
| `auth.logout` | User session exit |
| `super_admin.dashboard` | Main Super Admin dashboard |
| `super_admin.manage_clients` | Client Manager |
| `super_admin.view_client` | Client profile |
| `super_admin.generate_client_units` | Unit generation from client/development structure |
| `super_admin.manage_users` | Team Manager |
| `super_admin_contracts.contracts_overview` | Contract Manager overview |
| `super_admin.work_orders` | Works Logix command centre |
| `super_admin.gar_inquiry` | Super Admin source-backed GAR inquiry endpoint |
| `admin_portal.gar_inquiry` | Admin source-backed GAR inquiry endpoint |
| `property_manager.gar_inquiry` | Property Manager assigned-development GAR inquiry endpoint |
| `assistant.gar_inquiry` | Assistant assigned/cover-scope GAR inquiry endpoint |
| `finance.gar_inquiry` | Finance role-aware GAR inquiry endpoint with finance readiness gates |
| `director.gar_inquiry` | Director governance GAR inquiry endpoint |
| `contractor.gar_inquiry` | Contractor queue-scoped GAR inquiry endpoint |
| `members.gar_inquiry` | Member/resident linked-unit GAR inquiry endpoint |
| `super_admin.convert_member_request_to_work_order` | Members Logix request to Works Logix hand-off |
| `super_admin.assign_work_order_contractor` | Works Logix contractor routing |
| `unit_bp.list` | Unit directory/list |
| `unit_bp.view` | Unit detail/dashboard |
| `unit_bp.edit` | Unit setup/edit |
| `unit_bp.work_order_review` | Unit-level work order review and GAR snapshot |
| `unit_bp.work_order_completion_review` | PM/Admin completion approval or return |
| `unit_bp.reopen_request_approve` | PM/Admin reopen approval |
| `unit_bp.reopen_request_reject` | PM/Admin reopen rejection |
| `assistant.work_orders` | Assistant Works Logix view scoped to assigned developments, or company cover queue for Assistant Manager |
| `assistant.convert_member_request` | Assistant conversion of assigned or cover-access member requests |
| `assistant.assign_work_order_contractor` | Assistant contractor routing for assigned or cover-access developments |
| `property_manager.work_orders` | Property Manager Works Logix view scoped to assigned developments |
| `property_manager.convert_member_request` | Property Manager conversion of assigned member requests |
| `property_manager.assign_work_order_contractor` | Property Manager contractor routing for assigned developments |
| `members.works` | Member/resident works and request view |
| `members.create_maintenance_request` | Member/resident maintenance request creation |
| `members.request_reopen` | Member/resident reopen request |
| `members.submit_work_order_feedback` | Member/resident feedback after completion |
| `contractor.work_orders` | Contractor assigned work queue |
| `contractor.update_work_order` | Contractor status and completion updates |

Phase 3 note:

The Works lifecycle flow is now protected by the smoke check:

```text
Members request -> Works triage by PM/Admin/Assistant/Assistant Manager cover -> Contractor update/completion -> Member feedback/reopen -> PM/Admin review -> GAR context
```

The lifecycle source-of-truth is `app/models/works/work_order_lifecycle_event.py`.

## Legacy Blueprint Groups Not Active

The smoke check confirms these are not currently registered:

| Blueprint | Notes |
| --- | --- |
| `admin` | Old Admin blueprint exists in legacy-looking route files but is not active |

Note: `members` is now an active package blueprint at `app/routes/members/__init__.py`.
The archived legacy item was the old flat file `app/routes/members.py`.

## Cleanup Rule

Before archiving any route file, confirm:

1. The file is not required to register one of the active blueprint groups above.
2. The route inventory still runs.
3. The architecture smoke check still passes.
4. The core browser flows still work after the move.

## Next Safe Archive Candidates

Start with files that do not overlap active package names:

```text
app/routes/_super_admin.py
app/routes/old_admin.py
app/routes/old_auth.py
old_run.py
```

Status: archived to `legacy_archive/phase2_routes_2026-05-24/` and verified with the smoke check.

Files that need extra care because their names overlap active packages:

```text
app/routes/super_admin.py
app/routes/auth.py
app/routes/admin.py
app/routes/__init__.py
app/helpers/__init__.py
```

Status:

```text
app/routes/super_admin.py -> archived to legacy_archive/phase2_route_overlap_2026-05-24/
app/routes/auth.py -> archived to legacy_archive/phase2_route_overlap_2026-05-24/
app/routes/admin.py -> archived to legacy_archive/phase2_route_overlap_2026-05-24/
```

The remaining files in this group should be reviewed separately because they are package/helper files rather than standalone legacy routes.

Resolved on 2026-05-24:

```text
app/routes/__init__.py -> simplified package marker
app/helpers/__init__.py -> simplified package marker
```

Contract Manager note:

```text
Removed duplicate malformed renewal URL from active route map.
Current route count: 161.
Canonical renewal route remains /super-admin/contracts/renew/<client_id>.
```

Root app note:

```text
Archived root-level legacy app.py, config.py, static/ and templates/ after confirming
the active import resolves to app/__init__.py, deployment uses run:app, and Flask uses
app/config.py, app/templates and app/static.
Current route count remains 161.
```

Inactive draft note:

```text
Archived app/controllers/ and app/routes/members.py after confirming active unit
routes live in app/routes/unit.py. A new Members Logix package blueprint was
added later at app/routes/members/__init__.py.
```

Template cleanup note:

```text
Archived explicit old_* backup templates after confirming no active references.
Current route count remains 161.
```

Template reference note:

```text
Added scripts/template_reference_check.py and repaired active missing template
references. Active literal render_template calls now pass.
```
