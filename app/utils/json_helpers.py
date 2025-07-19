# app/utils/json_helpers.py

import json
from markupsafe import Markup
from datetime import datetime
from decimal import Decimal

# ✅ Safely loads a stringified JSON, returns dict or fallback
def parse_json_string(json_str, fallback=None):
    try:
        if json_str:
            return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        pass
    return fallback or {}

# ✅ Ensures any dict/obj is safely dumped into a string
def ensure_json_string(value):
    try:
        return json.dumps(value, default=_json_serializer, indent=2)
    except Exception:
        return '{}'

# ✅ Prettify JSON for readable display in HTML templates
def json_prettify(value):
    if not value:
        return Markup("<pre><code>{}</code></pre>")
    if isinstance(value, str):
        value = parse_json_string(value, fallback={})
    pretty = json.dumps(value, indent=2, ensure_ascii=False)
    return Markup(f"<pre><code>{pretty}</code></pre>")

# ✅ Default serializer for complex types
def _json_serializer(obj):
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)

# ✅ Validates if input is clean JSON
def is_valid_json(value):
    try:
        json.loads(value)
        return True
    except (json.JSONDecodeError, TypeError):
        return False

# ✅ Merges AI fields with raw extracted data (for audit/preview)
def merge_ai_fields(parsed_summary, extracted_data, gar_fields=None):
    base = {
        "summary": parsed_summary or "",
        "data": parse_json_string(extracted_data)
    }
    if gar_fields:
        base["gar_review"] = parse_json_string(gar_fields)
    return base

# ✅ Utility to flatten extracted_data keys for keyword search
def flatten_json_keys(data, parent_key='', sep='.'):
    items = []
    if isinstance(data, str):
        data = parse_json_string(data)
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json_keys(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def truncate_json(data, max_length=300):
    """Truncates a JSON string to a max length with ellipsis if needed."""
    if len(data) <= max_length:
        return data
    return data[:max_length] + '...'

def parse_and_format_json(json_string):
    """Parses a JSON string and returns pretty-formatted output."""
    try:
        data = json.loads(json_string)
        return json.dumps(data, indent=2)
    except (json.JSONDecodeError, TypeError):
        return "Invalid JSON"
