from __future__ import annotations
from typing import Any, Dict, List, Tuple

def changed_keys(before: Dict[str, Any] | None, after: Dict[str, Any] | None) -> List[str]:
    """
    Returns a sorted list of top-level keys that changed between before and after.
    Only compares first-level keys (that's enough for concise UI badges).
    """
    before = before or {}
    after = after or {}
    keys = set(before.keys()) | set(after.keys())
    diffs: List[str] = []
    for k in keys:
        if before.get(k) != after.get(k):
            diffs.append(k)
    return sorted(diffs)
