# app/services/validation.py
from __future__ import annotations
import json, re
from typing import Dict, Any, Tuple

def load_schema(schema_text: str | None) -> Dict[str, Any]:
    try:
        return json.loads(schema_text) if schema_text else {"sections": []}
    except Exception:
        return {"sections": []}

def _rules_for_path(schema: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Flatten schema to {path: {type, required, min, max, regex, ...}}.
    Also supports tables: columns appear as "<table_path>.__col__.<col_path>".
    """
    out: Dict[str, Dict[str, Any]] = {}
    for sec in schema.get("sections", []):
        for f in sec.get("fields", []) or []:
            if isinstance(f, dict) and f.get("path"):
                out[f["path"]] = f
        for t in sec.get("tables", []) or []:
            if not t.get("path"): continue
            for c in t.get("columns", []) or []:
                if c.get("path"):
                    out[f"{t['path']}.__col__.{c['path']}"] = c
    return out

def _is_empty(val: Any) -> bool:
    return val is None or (isinstance(val, str) and val.strip() == "")

def validate_against_schema(data_json: Dict[str, Any], schema_text: str | None) -> Dict[str, str]:
    """
    Validate values in data_json according to form_schema rules.
    Supports: required, min, max (numeric), regex (string).
    Returns {path: "error message"} for any violations.
    """
    schema = load_schema(schema_text)
    rules = _rules_for_path(schema)
    errors: Dict[str, str] = {}

    # direct fields
    for path, field in rules.items():
        # read value
        if ".__col__." in path:
            # table column rules will be validated below in the table loop
            continue
        val = _get_by_path_or_none(data_json, path)

        # required
        if field.get("required") and _is_empty(val):
            errors[path] = "This field is required."
            continue

        # numeric bounds
        ftype = (field.get("type") or "").lower()
        if not _is_empty(val) and ftype in ("number", "money"):
            try:
                num = float(val)
                if "min" in field and num < float(field["min"]):
                    errors[path] = f"Must be ≥ {field['min']}."
                if "max" in field and num > float(field["max"]):
                    errors[path] = f"Must be ≤ {field['max']}."
            except Exception:
                errors[path] = "Must be a number."

        # regex
        pattern = field.get("regex")
        if pattern and not _is_empty(val):
            try:
                if not re.fullmatch(pattern, str(val)):
                    errors[path] = "Invalid format."
            except re.error:
                # ignore invalid regex in schema
                pass

    # table validations: walk each row and apply column rules
    for sec in schema.get("sections", []):
        for t in sec.get("tables", []) or []:
            tpath = t.get("path")
            if not tpath: continue
            rows = _get_by_path_or_none(data_json, tpath)
            if not isinstance(rows, list): continue

            for idx, row in enumerate(rows):
                if not isinstance(row, dict): continue
                for col in t.get("columns", []) or []:
                    cpath = col.get("path")
                    if not cpath: continue
                    fullpath = f"{tpath}[{idx}].{cpath}"
                    val = row.get(cpath)

                    if col.get("required") and _is_empty(val):
                        errors[fullpath] = "This field is required."
                        continue

                    ctype = (col.get("type") or "").lower()
                    if not _is_empty(val) and ctype in ("number", "money"):
                        try:
                            num = float(val)
                            if "min" in col and num < float(col["min"]):
                                errors[fullpath] = f"Must be ≥ {col['min']}."
                            if "max" in col and num > float(col["max"]):
                                errors[fullpath] = f"Must be ≤ {col['max']}."
                        except Exception:
                            errors[fullpath] = "Must be a number."

                    pattern = col.get("regex")
                    if pattern and not _is_empty(val):
                        try:
                            if not re.fullmatch(pattern, str(val)):
                                errors[fullpath] = "Invalid format."
                        except re.error:
                            pass

    return errors

# --- helpers ---
def _get_by_path_or_none(root: Dict[str, Any], dotted: str):
    cur = root
    try:
        for p in dotted.split("."):
            cur = cur[p]
        return cur
    except Exception:
        return None
