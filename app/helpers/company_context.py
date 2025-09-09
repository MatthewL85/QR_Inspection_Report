# app/utils/company_context.py
from flask_login import current_user
from flask import session

def get_active_company_id():
    # Future: allow an override via org switcher
    return session.get("company_ctx_id") or current_user.company_id
