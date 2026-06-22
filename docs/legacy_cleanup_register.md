# Legacy Cleanup Register

Status: Phase 1 architecture control document

Purpose: list files and areas that appear legacy, duplicate or confusing so they can be reviewed safely before removal or refactor.

No files should be deleted from this register without confirming they are not imported, not linked in templates, and not needed by migrations or historical scripts.

## Review Before Removing

| Area | File or folder | Reason for review | Risk |
| --- | --- | --- | --- |
| Root app | `app.py` | Archived to `legacy_archive/phase2_root_legacy_2026-05-25/app.py`. Current import resolves to `app/__init__.py`; current `Procfile` uses `run:app`. | Verified smoke pass after archive |
| Root app | `old_run.py` | Archived to `legacy_archive/phase2_routes_2026-05-24/old_run.py`. Current `Procfile` uses `run:app`. | Verified smoke pass after archive |
| Routes | `app/routes/super_admin.py` | Archived to `legacy_archive/phase2_route_overlap_2026-05-24/super_admin.py`. Active package origin verified as `app/routes/super_admin/__init__.py`. | Verified smoke pass after archive |
| Routes | `app/routes/_super_admin.py` | Archived to `legacy_archive/phase2_routes_2026-05-24/_super_admin.py`. Exact duplicate hash of `app/routes/super_admin.py`. | Verified smoke pass after archive |
| Routes | `app/routes/old_admin.py` | Archived to `legacy_archive/phase2_routes_2026-05-24/old_admin.py`. Exact duplicate hash of `app/routes/admin.py`. | Verified smoke pass after archive |
| Routes | `app/routes/old_auth.py` | Archived to `legacy_archive/phase2_routes_2026-05-24/old_auth.py`. Old monolithic auth file. | Verified smoke pass after archive |
| Routes | `app/routes/admin.py` | Archived to `legacy_archive/phase2_route_overlap_2026-05-24/admin.py`. Defines `admin_bp`; current app factory does not register the `admin` blueprint. | Verified smoke pass after archive |
| Routes | `app/routes/auth.py` | Archived to `legacy_archive/phase2_route_overlap_2026-05-24/auth.py`. Active package origin verified as `app/routes/auth/__init__.py`. | Verified smoke pass after archive |
| Routes | `app/routes/members.py` | Archived to `legacy_archive/phase2_inactive_drafts_2026-05-25/members.py`. It contained route snippets but no active registered blueprint. A new package blueprint now lives at `app/routes/members/__init__.py`. | Verified smoke pass after archive |
| Routes | `app/routes/__init__.py` | Simplified to a side-effect-free package marker. Removed stale `register_routes(app)` helper. | Verified smoke pass after cleanup |
| Helpers | `app/helpers/__init__.py` | Simplified to a side-effect-free package marker. Removed inactive helper `create_app()`. | Verified smoke pass after cleanup |
| Models | `app/models/models_temp.py` | Archived to `legacy_archive/phase2_model_temp_2026-05-24/models_temp.py`. No code references found outside docs. | Verified smoke pass after archive |
| Controllers | `app/controllers/` | Archived to `legacy_archive/phase2_inactive_drafts_2026-05-25/controllers/`. Active unit routes live in `app/routes/unit.py`; no imports found for `app.controllers`. | Verified smoke pass after archive |
| Static/templates root | `templates/` | Archived to `legacy_archive/phase2_root_legacy_2026-05-25/templates/`. Active app explicitly uses `app/templates`. | Verified smoke pass after archive |
| Static/templates root | `static/` root folder | Archived to `legacy_archive/phase2_root_legacy_2026-05-25/static/`. Active app explicitly uses `app/static`; no active root static references found. | Verified smoke pass after archive |
| Root config | `config.py` | Archived to `legacy_archive/phase2_root_legacy_2026-05-25/config.py`. Active factory loads `app.config.ProductionConfig`. | Verified smoke pass after archive |
| Data files | Root CSV seed files and `data/` | Archived to `legacy_archive/phase2_root_loose_files_2026-05-25/`. Active app is database-backed; no active file references found. | Verified smoke pass after archive |
| Generated previews | `contract_*_preview.html`, `contract_tv3.html` | Archived to `legacy_archive/phase2_root_loose_files_2026-05-25/`. These were generated root previews, not active templates. | Verified smoke pass after archive |
| Root helper scripts | `hash_passwords.py`, `seed_super_admin.py`, `seed_user.py` | Archived to `legacy_archive/phase2_root_loose_files_2026-05-25/`. Active seed scripts live under `migrations/scripts/` or `scripts/`. | Verified smoke pass after archive |
| Root generated docs | `structure.txt`, `test.pdf` | Archived to `legacy_archive/phase2_root_loose_files_2026-05-25/`. Historical/generated root artifacts. | Verified smoke pass after archive |
| Templates | `app/templates/old_*`, `app/templates/super_admin/old_*`, `app/templates/super_admin/client/old_*`, `app/templates/super_admin/_edit_client.html` | Archived to `legacy_archive/phase2_old_templates_2026-05-25/`. No active references found. | Verified smoke pass after archive |
| Template references | Active `render_template()` calls | Added `scripts/template_reference_check.py` and fixed active missing template references. | Verified template check pass |
| URL references | Active `url_for()` calls | Added `scripts/url_for_reference_check.py`; fixed active missing route links and replaced the old Admin sidebar fallback. | Verified URL reference check pass |
| Module contracts | `app/services/core/module_registry.py` and `scripts/module_contract_check.py` | Added a registry to distinguish active, partial, shell and foundation modules. | Verified module contract check pass |
| Old project folder | `Old_QR/` | Historical nested project folder with its own `.git` and `venv`. No active references found, but leave for a separate archive/removal decision because it is large and repository-like. | Pending deliberate archive decision |
| Contract routes | `renew_legacy_route` in `app/routes/super_admin/contracts/contracts.py` | Duplicate malformed URL unregistered and inactive function body removed. Canonical route remains active. | Verified smoke pass after cleanup |
| Archive governance | `docs/architecture/archive_strategy.md`, `scripts/archive_inventory_check.py`, `legacy_archive/ARCHIVE.md` | Formalised the archive strategy and added a read-only inventory check so legacy roots remain visible without deleting material prematurely. | Strict archive check pass |
| Old project folder | `Old_QR/` parent gitlink | Parent repo should stop tracking the nested historical project. The local folder is retained on disk and ignored so it can be reviewed or moved to external storage later. Nested repo snapshot observed at `fe2ff7f`. | Strict archive check pass; pending commit |
| Old static data | `app/static/data/old_jurisdictions.json` | Superseded by active `app/static/data/jurisdictions.json`. Active templates and JavaScript reference `jurisdictions.json`, not the old file. | Strict archive check pass; pending commit |

## Cleanup Method

Use this order for each item:

1. Search imports and references with `rg`.
2. Check blueprint registration and app factory imports.
3. Check template links and `url_for` endpoint names.
4. Check migration or seed script dependencies.
5. Move to an archive folder only after confirmation.
6. Run route loading smoke test.
7. Run key user flows.

## Do Not Remove Yet

These files should not be removed during Phase 1:

- Any model file imported by `app/models/__init__.py`
- Any active route file registered by the app factory
- Any template currently used by active routes
- Any migration
- Any service used by active route handlers

## Target

After review, the codebase should have one clear active route location per module and no duplicate-looking route files that confuse future development.
