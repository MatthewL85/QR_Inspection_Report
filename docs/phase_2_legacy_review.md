# Phase 2 Legacy Review

Status: safe review only. No runtime files changed.

Purpose: identify legacy or duplicate files that should be cleaned later, without breaking the current working platform.

## Verification Performed

The current active app entrypoint is:

```text
Procfile -> gunicorn run:app
run.py -> create_app()
app/__init__.py -> create_app()
```

The app factory currently registers these active blueprint groups:

```text
auth
settings
super_admin
property_manager
contractor
director
equipment
capex
tenant
unit_bp
super_admin_contracts
super_admin_simple_contracts
client_key_info
devtools
finance
assistant
members
```

Route loading smoke check:

```text
create_app() loaded successfully
129 URL rules registered
admin blueprint not registered
legacy flat members route not registered
```

## High Confidence Legacy / Duplicate Candidates

These files appear duplicated, stale, or not registered by the current app factory.

| File | Finding | Recommendation |
| --- | --- | --- |
| `app/routes/super_admin.py` | Same file hash as `app/routes/_super_admin.py`. It is a flat old-style Super Admin route file. The active import resolves to the `app/routes/super_admin/` package. | Mark as legacy candidate. Do not delete yet because the name overlaps with the active package and should be handled carefully. |
| `app/routes/_super_admin.py` | Exact duplicate of `app/routes/super_admin.py`. | Mark as duplicate legacy candidate. |
| `app/routes/admin.py` | Same file hash as `app/routes/old_admin.py`. Defines an `admin_bp`, but the current app factory does not register it. | Mark as legacy candidate. Confirm no production links depend on `/admin`. |
| `app/routes/old_admin.py` | Exact duplicate of `app/routes/admin.py`. | Mark as duplicate legacy candidate. |
| `app/routes/old_auth.py` | Similar old monolithic auth route file. Current app uses the `app/routes/auth/` package and `register_auth_routes(app)`. | Mark as legacy candidate. |
| `app/routes/auth.py` | Old monolithic auth route file exists alongside the active `app/routes/auth/` package. Current active import resolves to the package. | Mark as legacy candidate, but review carefully because the name overlaps with active auth package. |
| `app/routes/members.py` | Contains route decorators but no visible blueprint definition/imports in the file. This was the old flat Members draft and has since been archived. | Treat as incomplete/stale Members Logix route draft. The active Members shell is now the package `app/routes/members/__init__.py`. |
| `app/routes/__init__.py` | Contains a `register_routes(app)` function referencing `super_admin_users_bp`, which is not defined in that file. It is not used by current `create_app()`. | Mark as stale registration helper. |
| `app/helpers/__init__.py` | Contains an old app factory helper that registers older blueprints. It is not the current app factory. | Mark as legacy helper; do not call. |
| `app/models/models_temp.py` | Large temporary metadata/reflection file. Also references names that may not match current models. | Mark as legacy/temp candidate; check migrations before removal. |
| `old_run.py` | Old entrypoint. Current `Procfile` uses `run:app`. | Mark as legacy candidate. |
| `app.py` | Large root-level legacy QR/inspection Flask app with direct `app = Flask(__name__)` and many `@app.route` handlers. Current Python import resolves to the `app/` package, not this file. | Archive after confirming `run.py` and `Procfile` use the app factory. |

## Active Files To Protect

These are active and should not be touched during cleanup unless intentionally refactoring:

```text
run.py
app/__init__.py
app/routes/auth/
app/routes/super_admin/
app/routes/settings/
app/routes/unit.py
app/routes/property_manager.py
app/routes/contractor.py
app/routes/director.py
app/routes/client/key_info/
app/routes/super_admin/contracts/
```

## Important Finding

The codebase has two styles at once:

1. The newer app-factory/package style used by the running platform.
2. Older flat route files from the earlier build.

This is exactly the kind of thing that can make a platform feel messy internally even when the UI is improving. It does not mean the app is broken, but it does mean future changes are more risky because a developer could edit the wrong file.

## Recommended Cleanup Strategy

Do not delete anything immediately.

Use a controlled three-step process:

1. Create a `legacy_archive` branch or commit point.
2. Move only confirmed inactive files into a clearly named archive folder.
3. Run smoke tests after each small cleanup group.

Suggested first cleanup group:

```text
app/routes/_super_admin.py
app/routes/old_admin.py
app/routes/old_auth.py
old_run.py
```

Archived on 2026-05-24 to:

```text
legacy_archive/phase2_routes_2026-05-24/
```

Archived files:

```text
legacy_archive/phase2_routes_2026-05-24/_super_admin.py
legacy_archive/phase2_routes_2026-05-24/old_admin.py
legacy_archive/phase2_routes_2026-05-24/old_auth.py
legacy_archive/phase2_routes_2026-05-24/old_run.py
```

Post-archive verification:

```text
Architecture smoke check: PASSED
Blueprints registered: 15
URL rules registered: 129
```

Suggested second cleanup group, only after extra import testing:

```text
app/routes/super_admin.py
app/routes/auth.py
app/routes/admin.py
app/routes/__init__.py
app/helpers/__init__.py
app/models/models_temp.py
```

Partial second-group archive completed on 2026-05-24 after package-origin checks confirmed:

```text
app.routes.auth -> app/routes/auth/__init__.py
app.routes.super_admin -> app/routes/super_admin/__init__.py
```

Archived to:

```text
legacy_archive/phase2_route_overlap_2026-05-24/
```

Archived files:

```text
legacy_archive/phase2_route_overlap_2026-05-24/admin.py
legacy_archive/phase2_route_overlap_2026-05-24/auth.py
legacy_archive/phase2_route_overlap_2026-05-24/super_admin.py
```

Post-archive verification:

```text
Architecture smoke check: PASSED
Blueprints registered: 15
URL rules registered: 129
Package origins checked: 2
```

Still pending from second group:

```text
app/routes/__init__.py
app/helpers/__init__.py
```

Archived separately after reference check:

```text
legacy_archive/phase2_model_temp_2026-05-24/models_temp.py
```

Post-archive verification:

```text
Architecture smoke check: PASSED
Blueprints registered: 15
URL rules registered: 129
Package origins checked: 2
```

Still pending:

```text
app/routes/__init__.py
app/helpers/__init__.py
```

Resolved on 2026-05-24 by simplifying both files into side-effect-free package markers:

```text
app/routes/__init__.py
app/helpers/__init__.py
```

The stale `register_routes(app)` helper and inactive helper `create_app()` were removed from those package initializers. The active app factory remains:

```text
app/__init__.py -> create_app()
```

Post-cleanup verification:

```text
Architecture smoke check: PASSED
Blueprints registered: 15
URL rules registered: 129
Package origins checked: 2
```

## Recommendation

The next safe technical step is to add an automated architecture smoke test that confirms:

- The app factory loads.
- Expected blueprints are registered.
- Known legacy blueprints are not registered.
- Key routes still resolve.

That gives us a safety net before moving or deleting legacy files.

## Safety Net Added

Added:

```text
scripts/architecture_smoke_check.py
```

Purpose:

- Load `create_app()`.
- Confirm core blueprints are registered.
- Confirm the legacy `admin` blueprint is not accidentally registered.
- Confirm the active Members Logix package endpoint is registered.
- Confirm critical endpoints still exist.

Run command:

```text
.\venv\Scripts\python.exe scripts\architecture_smoke_check.py
```

Verified result:

```text
Architecture smoke check
- Blueprints registered: 15
- URL rules registered: 129
- Critical endpoints checked: 11

PASSED
```

## Active Route Inventory Added

Added:

```text
scripts/architecture_route_inventory.py
docs/active_route_inventory.md
```

Purpose:

- Print the live route inventory from the app factory.
- Group routes by blueprint.
- Give the cleanup work a clear active-route reference before any old files are archived.

Run command:

```text
.\venv\Scripts\python.exe scripts\architecture_route_inventory.py
```

## Legacy Contract Route Cleanup

The route inventory exposed an odd active URL:

```text
/super-admin/contracts/super-admin/contracts/renew/<int:client_id>
```

Finding:

- The canonical Contract Manager renewal route is `/super-admin/contracts/renew/<int:client_id>`.
- Templates and services point to the canonical route.
- The odd route came from a redirect shim named `renew_legacy_route`.

Action:

- Removed the route decorators from `renew_legacy_route`, so the duplicate URL is no longer registered.
- Removed the now-inactive `renew_legacy_route` function body in a follow-up tidy pass.

Post-cleanup verification:

```text
Architecture smoke check: PASSED
Blueprints registered: 15
URL rules registered: 128
Package origins checked: 2
```

## Root Legacy App Cleanup

The root-level `app.py` was reviewed after the active app import path was confirmed:

```text
import app -> app/__init__.py
hasattr(app, "create_app") -> True
Procfile -> gunicorn run:app
run.py -> create_app()
```

Finding:

- `app.py` was a standalone legacy QR/inspection Flask app.
- It defined its own `app = Flask(__name__)`.
- It contained many direct `@app.route` handlers unrelated to the current modular platform.
- It was not the active deployment entrypoint.

Action:

```text
app.py -> legacy_archive/phase2_root_legacy_2026-05-25/app.py
config.py -> legacy_archive/phase2_root_legacy_2026-05-25/config.py
static/ -> legacy_archive/phase2_root_legacy_2026-05-25/static/
templates/ -> legacy_archive/phase2_root_legacy_2026-05-25/templates/
```

Post-archive verification:

```text
Architecture smoke check: PASSED
Blueprints registered: 15
URL rules registered: 128
Package origins checked: 2
```

## Active Template Reference Check

Added:

```text
scripts/template_reference_check.py
```

Purpose:

- Load the active Flask app.
- Inspect registered view function modules.
- Find literal `render_template()` calls.
- Fail if an active route points at a missing template.

Initial finding:

- The app factory loaded, but several active view modules referenced moved or missing templates.
- These were repaired by pointing routes at the current template locations or adding lightweight missing templates.

Fixed active references included:

```text
auth/resend_verification.html
auth/onboard.html
auth/security/setup_two_factor.html
auth/two_factor_verify.html
contractor/settings.html
add_task.html
super_admin/client/assign_pm.html
super_admin/client/assign_fc.html
super_admin/compliance_documents/client/*
super_admin/compliance_documents/contractor/compliance_documents.html
super_admin/users/*
```

Verified result:

```text
Template reference check: PASSED
Literal render_template calls checked: 93
```

## Active URL Reference Check

Added:

```text
scripts/url_for_reference_check.py
```

Purpose:

- Load the active Flask app.
- Inspect active registered view modules for literal `url_for()` calls.
- Inspect active rendered templates and their direct layout/include dependencies.
- Fail if a current Python route or active template links to a missing endpoint.
- Skip dynamic, relative blueprint and explicitly guarded optional-module links.

Initial findings:

- Several active route redirects pointed at old endpoint names.
- The old Admin sidebar was still used as the generic `base.html` fallback even though the legacy `admin` blueprint is not registered.
- Director and Contractor sidebars used old flat endpoint names instead of blueprint endpoint names.
- CAPEX response review had a missing route and older model-field assumptions.

Actions:

```text
Added scripts/url_for_reference_check.py
Fixed active redirects in auth onboarding, Director settings and client compliance routes
Added CAPEX response review route and corrected CAPEX decision redirects
Corrected Director and Contractor sidebar endpoint names
Added safe placeholder redirects for unfinished Director/Contractor sections
Added Super Admin work-order placeholder endpoint
Added Super Admin audit-log list endpoint
Replaced the old Admin sidebar fallback with sidebar_default.html
```

Verified result:

```text
URL reference check: PASSED
Active endpoints registered: 137
Template url_for calls checked: 305
Active rendered templates checked: 100
Guarded optional references skipped: 11
```

## Module Shells Added

Added lightweight package-style module shells:

```text
app/routes/finance.py
app/routes/assistant.py
app/routes/members/__init__.py
```

Purpose:

- Give Finance Logix, Assistant workspace and Members Logix real blueprint entry points.
- Keep each module independently routable.
- Avoid fake feature depth while giving future builds a clean home.
- Keep shared data linked to the same core records: users, clients, units and contracts.

Added templates:

```text
app/templates/finance/dashboard.html
app/templates/finance/manage_clients.html
app/templates/finance/sidebar_finance.html
app/templates/assistant/dashboard.html
app/templates/assistant/manage_clients.html
app/templates/assistant/sidebar_assistant.html
app/templates/members/dashboard.html
app/templates/members/sidebar_member.html
```

Verification:

```text
Architecture smoke check: PASSED
Template reference check: PASSED
URL reference check: PASSED
Blueprints registered: 19
URL rules registered: 145
```

## Module Contract Registry Added

Added:

```text
app/services/core/module_registry.py
scripts/module_contract_check.py
docs/module_contracts.md
```

Purpose:

- Declare each module's current status, entry endpoint, owned data and shared platform links.
- Validate that user-facing module entry points exist.
- Keep shells honest: Finance, Members, Assistant and Admin Portal are clean foundations, not pretend-complete systems.

Verified result:

```text
Module contract check: PASSED
Module contracts declared: 12
Dashboard endpoints checked: 11
```

## GAR Context Service Added

Added:

```text
app/services/gar/context.py
app/services/gar/__init__.py
scripts/gar_context_check.py
```

Purpose:

- Give GAR a central read-only context builder.
- Build portfolio, client and unit context from source records.
- Include source references and visibility rules so GAR answers remain explainable.
- Stop individual pages from creating disconnected AI summaries.

The Super Admin GAR AI Centre now uses the portfolio context service.

Verified result:

```text
GAR context check: PASSED
Portfolio context checked: yes
Client context checked: yes
Unit context checked: yes
```

## Old_QR Folder Review

Reviewed:

```text
Old_QR/
```

Finding:

- No active references were found outside the cleanup documentation.
- It is approximately 92 MB.
- It contains its own `.git` folder and `venv`.
- It appears to be a historical nested copy/project, not part of the active app factory.

Decision:

- Do not move it during routine cleanup.
- Handle it as a separate repository/archive decision so we do not accidentally disturb nested history or environment files.

## Old Template Cleanup

Reviewed explicit backup templates:

```text
app/templates/old_*
app/templates/super_admin/old_*
app/templates/super_admin/client/old_*
app/templates/super_admin/_edit_client.html
```

Finding:

- No active `render_template()` references were found for these files.
- The current client, contract and team manager pages use the newer templates under their module folders.
- `base.html` and the `admin/` template folder were not archived in this pass because older active/non-super-admin screens still extend `base.html`.

Action:

```text
Old backup templates -> legacy_archive/phase2_old_templates_2026-05-25/
```

Post-archive verification:

```text
Architecture smoke check: PASSED
Blueprints registered: 15
URL rules registered: 128
Package origins checked: 2
```

The active app uses `app/config.py`, `app/templates` and `app/static`. The root `config.py`, root `templates/` and root `static/` belonged to the old single-file app structure and were archived together after reference checks.

## Inactive Draft Cleanup

Reviewed:

```text
app/controllers/unit_controller.py
app/routes/members.py
```

Finding:

- Active unit routes are implemented in `app/routes/unit.py`.
- No imports were found for `app.controllers` or `unit_controller`.
- `app/routes/members.py` contained route snippets but no imports or active `members_bp` definition.
- This old flat file was archived. The new active Members Logix shell now lives in `app/routes/members/__init__.py`.

Action:

```text
app/controllers/ -> legacy_archive/phase2_inactive_drafts_2026-05-25/controllers/
app/routes/members.py -> legacy_archive/phase2_inactive_drafts_2026-05-25/members.py
```

Post-archive verification:

```text
Architecture smoke check: PASSED
Blueprints registered: 15
URL rules registered: 128
Package origins checked: 2
```

## Root Loose File Cleanup

Reviewed loose root files from the old CSV/prototype era:

```text
assignments.csv
capex_requests.csv
clients.csv
inspection_logs.csv
maintenance_schedule.csv
manual_tasks.csv
old_users.csv
users.csv
contract_1_preview.html
contract_4_preview.html
contract_tv3.html
hash_passwords.py
seed_super_admin.py
seed_user.py
structure.txt
test.pdf
data/
```

Finding:

- The active platform is using SQLAlchemy models and migrations, not root CSV storage.
- Root contract preview files were generated artifacts, not active templates.
- Active seed scripts live under `migrations/scripts/` or `scripts/`.
- No active references were found outside the archive, apart from a dynamic export filename named `users.csv`.

Action:

```text
Root loose files -> legacy_archive/phase2_root_loose_files_2026-05-25/
```

Post-archive verification:

```text
Architecture smoke check: PASSED
Blueprints registered: 15
URL rules registered: 128
Package origins checked: 2
```
