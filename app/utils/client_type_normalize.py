# -*- coding: utf-8 -*-
"""
Client type normaliser:
- Maps legacy/variant labels to a canonical set used in jurisdictions.json.
- Provides a helper to build deduped (value, label) choice lists.
"""

from __future__ import annotations
import re
from typing import Iterable, List, Tuple

# Canonical labels you actually want to store/display
CANON = {
    # IE
    "omc": "OMC",
    "commercial management company": "Commercial Management Company",
    "mixed-use": "Mixed-Use",

    # GB (E&W)
    "rmc": "RMC",
    "rtm company": "RTM Company",
    "commonhold association": "Commonhold Association",

    # US
    "hoa": "HOA",
    "condo association": "Condo Association",
    "co-op board": "Co-op Board",

    # CA
    "condo corp.": "Condo Corp.",
    "strata": "Strata",

    # AU/NZ
    "owners corporation": "Owners Corporation",
    "community association": "Community Association",
    "body corporate": "Body Corporate",
    "manager": "Manager",  # NZ fallback

    # SG/HK/UAE
    "mcst": "MCST",
    "owners’ corporation": "Owners’ Corporation",
    "owners' corporation": "Owners’ Corporation",
    "owners association": "Owners Association",
    "master community": "Master Community",

    # Generic EU/EEA fallback
    "owners’ association": "Owners’ Association",
    "owners' association": "Owners’ Association",
    "management company": "Management Company",
}

# Known legacy/variant labels -> canonical
ALIASES = {
    # IE variants
    "owners’ management company (omc)": "OMC",
    "owners' management company (omc)": "OMC",
    "owner management company (omc)": "OMC",
    "omc": "OMC",
    "commercial mc": "Commercial Management Company",
    "commercial m.c.": "Commercial Management Company",
    "commercial management co": "Commercial Management Company",
    "mixed use": "Mixed-Use",
    "mixed-use": "Mixed-Use",
    "mixed use (res/com)": "Mixed-Use",

    # GB/E&W variants
    "residents’ management company (rmc)": "RMC",
    "residents' management company (rmc)": "RMC",
    "residents management company (rmc)": "RMC",
    "right to manage (rtm)": "RTM Company",
    "rtm": "RTM Company",
    "right to manage company": "RTM Company",
    "commonhold": "Commonhold Association",

    # US variants
    "homeowners association": "HOA",
    "homeowners' association": "HOA",
    "homeowner association": "HOA",
    "condominium association": "Condo Association",
    "cooperative board": "Co-op Board",
    "co-op": "Co-op Board",

    # CA variants
    "condominium corporation": "Condo Corp.",
    "strata corporation": "Strata",

    # AU/NZ variants
    "owners corp": "Owners Corporation",
    "owners' corporation": "Owners Corporation",
    "community assoc.": "Community Association",
    "body corp": "Body Corporate",

    # SG/HK/UAE variants
    "management corporation strata title": "MCST",
    "owners corp": "Owners’ Corporation",
    "owners corporation": "Owners’ Corporation",
    "oa": "Owners Association",
    "master community association": "Master Community",

    # Generic
    "owners association": "Owners’ Association",  # if used generically in EU context
    "owners assoc.": "Owners’ Association",
    "mgmt company": "Management Company",
}

def _canon_key(s: str) -> str:
    if s is None:
        return ""
    # unify fancy quotes/dashes, collapse whitespace, lowercase
    s = s.strip()
    s = s.replace("’", "'")
    s = re.sub(r"[\u2013\u2014−–—]", "-", s)  # en/em dashes to simple hyphen
    s = re.sub(r"\s+", " ", s)
    return s.lower()

def normalize_client_type(value: str) -> str:
    """
    Map any legacy/variant label to the canonical label.
    If unknown, return input unchanged (safe fallback).
    """
    key = _canon_key(value)
    return ALIASES.get(key, CANON.get(key, value))

def normalized_choice_list(options: Iterable[str]) -> List[Tuple[str, str]]:
    """
    Given a list of raw client type strings, return deduped (value,label) pairs
    using canonical labels, preserving the order of first appearance.
    """
    seen = set()
    normalized: List[Tuple[str, str]] = []
    for opt in options:
        lab = normalize_client_type(opt)
        if lab not in seen:
            normalized.append((lab, lab))
            seen.add(lab)
    return normalized

__all__ = [
    "normalize_client_type",
    "normalized_choice_list",
]
