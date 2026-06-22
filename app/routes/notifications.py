from datetime import datetime
from urllib.parse import urlsplit

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models.core.notification import Notification
from app.services.core.notification_feed import (
    NotificationFilters,
    build_notification_context,
    notification_feed_payload,
)
from app.services.core.notification_intelligence import safe_notification_link_url


notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


def _role_dashboard_url():
    role_name = getattr(getattr(current_user, "role", None), "name", None)
    endpoint_by_role = {
        "Super Admin": "super_admin.dashboard",
        "Admin": "admin_portal.dashboard",
        "Property Manager": "property_manager.pm_dashboard",
        "Assistant": "assistant.dashboard",
        "Financial Controller": "finance.dashboard",
        "Finance": "finance.dashboard",
        "Contractor": "contractor.contractor_dashboard",
        "Admin Contractor": "contractor.contractor_dashboard",
        "Director": "director.dashboard",
        "Member": "members.dashboard",
        "Resident": "members.dashboard",
    }
    endpoint = endpoint_by_role.get(role_name, "auth.profile")
    return url_for(endpoint)


def _notification_filters_from_request() -> NotificationFilters:
    return NotificationFilters(
        status=request.args.get("status") or "unread",
        type=request.args.get("type") or "",
        priority=request.args.get("priority") or "",
        module=request.args.get("module") or "",
        stage=request.args.get("stage") or "",
        action=request.args.get("action") or "",
        search=request.args.get("search") or "",
    )


def _safe_notification_target(link_url: str | None) -> str:
    return safe_notification_link_url(link_url, _role_dashboard_url())


def _safe_return_target(candidate: str | None, fallback: str) -> str:
    if not candidate:
        return fallback

    parsed = urlsplit(candidate)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme not in {"http", "https"} or parsed.netloc != request.host:
            return fallback
        candidate = parsed.path or "/"
        if parsed.query:
            candidate = f"{candidate}?{parsed.query}"
        if parsed.fragment:
            candidate = f"{candidate}#{parsed.fragment}"

    return safe_notification_link_url(candidate, fallback)


def _mark_notification_read(notification: Notification) -> None:
    if notification.is_read:
        return
    notification.is_read = True
    notification.read_at = datetime.utcnow()


@notifications_bp.route("/", endpoint="index")
@login_required
def index():
    context = build_notification_context(
        current_user.id,
        _notification_filters_from_request(),
        limit=300,
    )
    return render_template(
        "notifications/index.html",
        notification_return_url=_safe_return_target(request.args.get("next") or request.referrer, _role_dashboard_url()),
        **context,
    )


@notifications_bp.route("/feed.json", endpoint="feed")
@login_required
def feed():
    limit = request.args.get("limit", default=100, type=int)
    context = build_notification_context(
        current_user.id,
        _notification_filters_from_request(),
        limit=limit,
    )
    return jsonify(notification_feed_payload(context))


@notifications_bp.route("/<int:notification_id>/mark-read", methods=["POST"], endpoint="mark_read")
@login_required
def mark_read(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        recipient_id=current_user.id,
    ).first_or_404()

    _mark_notification_read(notification)
    db.session.commit()

    flash("Notification marked as read.", "success")
    return redirect(_safe_return_target(
        request.form.get("next") or request.referrer,
        url_for("notifications.index"),
    ))


@notifications_bp.route("/mark-all-read", methods=["POST"], endpoint="mark_all_read")
@login_required
def mark_all_read():
    now = datetime.utcnow()
    updated = (
        Notification.query
        .filter_by(recipient_id=current_user.id, is_read=False)
        .update({"is_read": True, "read_at": now}, synchronize_session=False)
    )
    db.session.commit()

    flash(f"{updated} notification{'s' if updated != 1 else ''} marked as read.", "success")
    return redirect(_safe_return_target(
        request.form.get("next") or request.referrer,
        url_for("notifications.index"),
    ))


@notifications_bp.route("/<int:notification_id>/open", endpoint="open")
@login_required
def open_notification(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        recipient_id=current_user.id,
    ).first_or_404()

    _mark_notification_read(notification)
    db.session.commit()

    return redirect(_safe_notification_target(notification.link_url))
