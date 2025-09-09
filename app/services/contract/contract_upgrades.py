# app/services/contract_upgrades.py
from __future__ import annotations
import json
import difflib
from typing import Dict, Any, List, Tuple

def _safe_json_load(s: str | None, fallback: dict = None) -> dict:
    if not s:
        return fallback or {}
    try:
        return json.loads(s)
    except Exception:
        return fallback or {}

def _flatten_fields(schema_sec: dict) -> List[dict]:
    """Return list of fields in a section; tolerate 'fields' and 'tables'."""
    out: List[dict] = []
    for f in schema_sec.get("fields", []) or []:
        out.append(f)
    # tables are arrays with columns; we treat them separately (append table meta)
    for t in schema_sec.get("tables", []) or []:
        out.append({"__table__": True, **t})
    return out

def diff_form_schema(old_schema: dict, new_schema: dict) -> dict:
    """
    Return a structured delta grouped by section.key:
      { section_key: {added:[], removed:[], changed_type:[], tables_added:[], tables_removed:[] } }
    """
    old_secs = {s.get("key"): s for s in (old_schema.get("sections") or [])}
    new_secs = {s.get("key"): s for s in (new_schema.get("sections") or [])}
    all_keys = set(old_secs.keys()) | set(new_secs.keys())

    delta: Dict[str, Any] = {}
    for k in sorted(all_keys):
        o = old_secs.get(k) or {}
        n = new_secs.get(k) or {}
        entry = {"added": [], "removed": [], "changed_type": [], "tables_added": [], "tables_removed": []}

        # fields by 'path'
        ofields = {f.get("path"): f for f in (o.get("fields") or []) if isinstance(f, dict) and f.get("path")}
        nfields = {f.get("path"): f for f in (n.get("fields") or []) if isinstance(f, dict) and f.get("path")}
        for path in nfields.keys() - ofields.keys():
            entry["added"].append({"path": path, "type": nfields[path].get("type"), "label": nfields[path].get("label")})
        for path in ofields.keys() - nfields.keys():
            entry["removed"].append({"path": path, "type": ofields[path].get("type"), "label": ofields[path].get("label")})
        for path in (nfields.keys() & ofields.keys()):
            ot = ofields[path].get("type")
            nt = nfields[path].get("type")
            if ot != nt:
                entry["changed_type"].append({"path": path, "old": ot, "new": nt})

        # tables by 'path'
        otabs = {t.get("path"): t for t in (o.get("tables") or []) if isinstance(t, dict) and t.get("path")}
        ntabs = {t.get("path"): t for t in (n.get("tables") or []) if isinstance(t, dict) and t.get("path")}
        for path in ntabs.keys() - otabs.keys():
            entry["tables_added"].append({"path": path, "title": ntabs[path].get("title")})
        for path in otabs.keys() - ntabs.keys():
            entry["tables_removed"].append({"path": path, "title": otabs[path].get("title")})

        # include only if any changes or section was added/removed entirely
        if any(entry.values()) or (k in new_secs and k not in old_secs) or (k in old_secs and k not in new_secs):
            delta[k] = entry

    return delta

def diff_html(old_html: str, new_html: str, context: int = 2) -> List[str]:
    """
    Return a small unified diff list for display.
    """
    old_lines = (old_html or "").splitlines()
    new_lines = (new_html or "").splitlines()
    return list(difflib.unified_diff(old_lines, new_lines, fromfile="current.html", tofile="latest.html", n=context))

def _set_by_path(root: dict, dotted: str, value: Any) -> None:
    cur = root
    parts = dotted.split(".")
    for k in parts[:-1]:
        cur = cur.setdefault(k, {})
    cur[parts[-1]] = value

def _build_defaults_for_section(section: dict) -> dict:
    """
    Build a minimal dict of defaults for a section based on field 'default' values.
    (If no default present, skip → we won't override existing values.)
    """
    out: dict = {}
    for f in section.get("fields", []) or []:
        path = f.get("path")
        if not path:
            continue
        if "default" in f:
            _set_by_path(out, path, f.get("default"))
    # Tables: create empty arrays by default if developer set default: []
    for t in section.get("tables", []) or []:
        path = t.get("path")
        if not path:
            continue
        default_rows = t.get("default")
        if isinstance(default_rows, list):
            _set_by_path(out, path, default_rows)
    return out

def build_upgrade_preview(old_schema_str: str | None, new_schema_str: str | None,
                          old_html: str, new_html: str) -> dict:
    old_schema = _safe_json_load(old_schema_str, {"sections": []})
    new_schema = _safe_json_load(new_schema_str, {"sections": []})
    schema_delta = diff_form_schema(old_schema, new_schema)
    html_delta = diff_html(old_html or "", new_html or "")
    # map section defaults for quick merging when accepted
    section_defaults = {s.get("key"): _build_defaults_for_section(s) for s in (new_schema.get("sections") or []) if s.get("key")}
    return {
        "schema_delta": schema_delta,
        "html_delta": html_delta,
        "section_defaults": section_defaults,
        "new_schema": new_schema,
    }

def apply_upgrade(contract_data: dict,
                  new_schema: dict,
                  section_defaults: dict,
                  accepted_sections: List[str],
                  archive_removed: List[str] | None,
                  removed_field_paths: List[str] | None) -> dict:
    """
    Merge defaults for accepted sections into contract_data (only where fields are missing).
    Archive optionally removed field paths into _deprecated.
    """
    out = contract_data.copy() if isinstance(contract_data, dict) else {}
    # Merge accepted section defaults (sparse, only defaulted fields)
    for key in (accepted_sections or []):
        defaults = section_defaults.get(key) or {}
        for dotted, value in _iter_flat(defaults):
            # only set if missing
            try:
                _get_by_path(out, dotted)
                exists = True
            except KeyError:
                exists = False
            if not exists:
                _set_by_path(out, dotted, value)

    # Archive removed fields if requested
    if archive_removed and removed_field_paths:
        bucket = out.setdefault("_deprecated", {})
        for dotted in removed_field_paths:
            try:
                val = _get_by_path(out, dotted)
                bucket[dotted] = val
                _delete_by_path(out, dotted)
            except KeyError:
                continue

    return out

# ----- tiny helpers for walking dotted paths -----
def _get_by_path(root: dict, dotted: str):
    cur = root
    for p in dotted.split("."):
        if p not in cur:
            raise KeyError(dotted)
        cur = cur[p]
    return cur

def _delete_by_path(root: dict, dotted: str):
    parts = dotted.split(".")
    cur = root
    for p in parts[:-1]:
        if p not in cur:
            raise KeyError(dotted)
        cur = cur[p]
    if parts[-1] in cur:
        del cur[parts[-1]]

def _iter_flat(d: dict, prefix: str = "") -> List[Tuple[str, Any]]:
    out: List[Tuple[str, Any]] = []
    for k, v in d.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.extend(_iter_flat(v, path))
        else:
            out.append((path, v))
    return out
