# Archive Strategy

Status: active architecture policy

Purpose: keep the production codebase small, understandable and safe while preserving historical work that may still have business or technical value.

LogixPM is becoming a multi-module platform. That means old project copies, historical route files, generated previews, unused templates and legacy data files can quietly become a major delivery risk. The active production branch should show one clear way to build each module.

## Current Risk Areas

The current workspace contains obvious legacy/archive areas:

- `Old_QR/`
- `legacy_archive/`
- older root-level files and deleted historical structures already tracked in `docs/legacy_cleanup_register.md`

These areas should be treated as historical references, not active product code.

## Archive Principles

1. The production branch should contain active code, active migrations, active templates, active static assets, active scripts and current documentation only.
2. Archive folders must never be imported, registered as blueprints, used as templates, served as static assets, or referenced by live app routes.
3. New development must not happen inside archive folders.
4. Historical material should be moved or removed only after a reference check and a successful smoke test.
5. Completed, signed or audit-sensitive documents must not be deleted as part of code cleanup. They belong in governed document storage, not code archive cleanup.
6. Database migrations should be retained unless a deliberate migration squash/reset is planned for a new deployment baseline.

## Classification

| Classification | Meaning | Action |
| --- | --- | --- |
| Active | Used by the running app, migrations, current scripts, current templates or current docs | Keep in production |
| Historical reference | Old code or files that explain previous decisions but are not used at runtime | Move to `legacy_archive/` or a separate archive branch |
| Duplicate legacy | Old route/template/static copies replaced by active packages | Archive after reference checks |
| Generated artifact | PDFs, previews, caches, compiled files, pycache, old exports | Remove from production after confirming they are reproducible or retained elsewhere |
| Business record | Contracts, compliance documents, audit logs, uploaded evidence | Do not remove via code cleanup |

## Production Branch Standard

The target production branch should not contain:

- `Old_QR/`
- duplicate old route files such as `old_*`
- root-level inactive Flask app copies
- root-level legacy `templates/` or `static/` folders when the active app uses `app/templates` and `app/static`
- `__pycache__/` folders
- generated preview files
- old CSV seed exports unless used by a current seed script

Short term, existing archive folders may remain locally while the platform is still being consolidated. Long term, large historical folders should move out of the production branch into a tagged archive branch, separate archive repository, or controlled storage location.

## Archive Folder Rules

Every archive folder should have a short manifest:

```text
legacy_archive/
  ARCHIVE.md
  2026-06-18_area_name/
    ARCHIVE.md
    files...
```

Each manifest should state:

- why the files were archived
- where they came from
- when they were archived
- what checks were run
- whether they can be deleted later

## Cleanup Workflow

Use this process for every cleanup group:

1. Inventory the candidate files.
2. Search imports, route registrations, template references, static references and script references.
3. Confirm migrations and seed scripts do not depend on the candidate files.
4. Move candidates to a dated archive folder or archive branch.
5. Run architecture, template, URL and module checks.
6. Run the key local app smoke flow.
7. Update `docs/legacy_cleanup_register.md`.
8. Only delete permanently after a release cycle or explicit approval.

## Recommended Immediate Actions

1. Freeze `Old_QR/` and `legacy_archive/` as read-only historical areas.
2. Add an automated archive inventory check to make legacy references visible.
3. Ensure no live app code references `Old_QR/` or `legacy_archive/`.
4. Add `ARCHIVE.md` manifests to archive folders in a later cleanup pass.
5. Move `Old_QR/` out of production once a tagged snapshot exists and the user approves.

## Verification

Run the archive inventory check:

```text
.\venv\Scripts\python.exe scripts\archive_inventory_check.py
```

For stricter CI-style checking:

```text
.\venv\Scripts\python.exe scripts\archive_inventory_check.py --strict
```

The normal check is advisory and read-only. The strict check should fail if active app areas reference legacy roots.

## Position In The Ecosystem

This policy supports the broader modular architecture:

- Core Platform remains clean and stable.
- Works Logix, Finance Logix, Contractor Logix, Director Logix and Members Logix remain separate modules with shared source records.
- GAR AI reads current governed records, not old project copies.
- Historical context is preserved without confusing the active product.
