# app/services/branding.py
from __future__ import annotations
from typing import Dict, Any
from flask import request, url_for
from flask_login import current_user
from app.models.onboarding.company import Company

def _resolve_company_for_branding() -> Company | None:
    # 1) explicit ?company_id or ?id
    cid = request.args.get("company_id", type=int) or request.args.get("id", type=int)
    if cid:
        obj = Company.query.get(cid)
        if obj:
            return obj

    # 2) logged-in user's company
    if getattr(current_user, "is_authenticated", False):
        if hasattr(current_user, "company_id") and current_user.company_id:
            obj = Company.query.get(current_user.company_id)
            if obj:
                return obj
        # 3) last created by me (if that column exists)
        if hasattr(Company, "created_by_id"):
            obj = (Company.query
                   .filter_by(created_by_id=getattr(current_user, "id", None))
                   .order_by(Company.id.desc())
                   .first())
            if obj:
                return obj

    return None

def brand_context() -> Dict[str, Any]:
    c = _resolve_company_for_branding()
    # Defaults that look fine with Material Dashboard
    primary   = (c.brand_primary_color   if c and getattr(c, "brand_primary_color", None)   else "#344767")
    secondary = (c.brand_secondary_color if c and getattr(c, "brand_secondary_color", None) else "#17c1e8")
    accent    = (c.brand_color           if c and getattr(c, "brand_color", None)           else "#e91e63")
    logo_url  = (c.logo_path             if c and getattr(c, "logo_path", None)             else url_for("static", filename="img/logo.png"))
    name      = (c.name                  if c and getattr(c, "name", None)                  else "LogixPM")

    return {
        "BRAND_COMPANY_NAME":   name,
        "BRAND_LOGO_URL":       logo_url,          # used already in your sidebar
        "BRAND_PRIMARY_COLOR":  primary,
        "BRAND_SECONDARY_COLOR":secondary,
        "BRAND_ACCENT_COLOR":   accent,
    }
