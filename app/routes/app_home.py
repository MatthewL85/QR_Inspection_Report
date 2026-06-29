from __future__ import annotations

from flask import Blueprint, jsonify, session
from flask_login import current_user, login_required

from app.models.core.user import User
from app.models.onboarding.company import Company
from app.services.core.app_home import (
    build_app_capabilities_payload,
    build_app_health_payload,
    build_app_home_payload,
)
from app.services.core.company_setup_readiness import company_setup_readiness_feed_payload


app_home_bp = Blueprint("app_home", __name__, url_prefix="/app")


@app_home_bp.route("/health/feed.json", endpoint="health_feed")
def health_feed():
    actor = current_user if current_user.is_authenticated else None
    if actor is None and session.get("_user_id"):
        actor = User.query.get(session["_user_id"])
    return jsonify(build_app_health_payload(actor))


@app_home_bp.route("/home/feed.json", endpoint="feed")
@login_required
def feed():
    return jsonify(build_app_home_payload(current_user))


@app_home_bp.route("/capabilities/feed.json", endpoint="capabilities_feed")
@login_required
def capabilities_feed():
    return jsonify(build_app_capabilities_payload(current_user))


@app_home_bp.route("/company-setup/feed.json", endpoint="company_setup_feed")
@login_required
def company_setup_feed():
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return jsonify({"error": "company_context_missing"}), 403

    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": "company_context_missing"}), 403

    return jsonify(company_setup_readiness_feed_payload(company))
