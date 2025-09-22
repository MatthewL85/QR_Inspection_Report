# app/routes/api/dashboard.py
from __future__ import annotations
from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from app.decorators import super_admin_required
from app.services.dashboard.metrics import get_dashboard_metrics

api_dashboard_bp = Blueprint("api_dashboard", __name__, url_prefix="/api/super-admin")

@api_dashboard_bp.get("/dashboard-metrics")
@super_admin_required
@login_required
def dashboard_metrics():
    """
    Returns the current tenant-scoped dashboard metrics as JSON.
    """
    company_id = getattr(current_user, "company_id", None)
    data = get_dashboard_metrics(company_id=company_id)
    return jsonify(data), 200
