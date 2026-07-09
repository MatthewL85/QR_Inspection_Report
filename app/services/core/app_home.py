from __future__ import annotations

from datetime import UTC, datetime

from flask import url_for
from werkzeug.routing import BuildError

from app.services.core.notification_feed import (
    NotificationFilters,
    build_notification_context,
    notification_feed_payload,
)
from app.services.core.notification_intelligence import notification_view_payload
from app.services.core.module_registry import module_contracts
from app.services.gar.capability_registry import build_gar_capability_registry


ROLE_DASHBOARDS = {
    "Super Admin": "super_admin.dashboard",
    "Admin": "admin_portal.dashboard",
    "Property Manager": "property_manager.pm_dashboard",
    "Assistant": "assistant.dashboard",
    "Assistant Property Manager": "assistant.dashboard",
    "Financial Controller": "finance.dashboard",
    "Finance": "finance.dashboard",
    "Director": "director.dashboard",
    "Contractor": "contractor.contractor_dashboard",
    "Admin Contractor": "contractor.contractor_dashboard",
    "Member": "members.dashboard",
    "Resident": "members.dashboard",
}

ROLE_GAR_FEEDS = {
    "Super Admin": "super_admin.gar_insights_feed",
    "Admin": "admin_portal.gar_feed",
    "Property Manager": "property_manager.gar_feed",
    "Assistant": "assistant.gar_feed",
    "Assistant Property Manager": "assistant.gar_feed",
    "Financial Controller": "finance.gar_feed",
    "Finance": "finance.gar_feed",
    "Director": "director.gar_feed",
    "Contractor": "contractor.gar_feed",
    "Admin Contractor": "contractor.gar_feed",
    "Member": "members.gar_feed",
    "Resident": "members.gar_feed",
}

ROLE_GAR_INQUIRIES = {
    "Super Admin": "super_admin.gar_inquiry",
    "Admin": "admin_portal.gar_inquiry",
    "Property Manager": "property_manager.gar_inquiry",
    "Assistant": "assistant.gar_inquiry",
    "Assistant Property Manager": "assistant.gar_inquiry",
    "Financial Controller": "finance.gar_inquiry",
    "Finance": "finance.gar_inquiry",
    "Director": "director.gar_inquiry",
    "Contractor": "contractor.gar_inquiry",
    "Admin Contractor": "contractor.gar_inquiry",
    "Member": "members.gar_inquiry",
    "Resident": "members.gar_inquiry",
}

ROLE_WORKS_SURFACES = {
    "Super Admin": ("super_admin.work_orders", "super_admin.work_orders_feed", "Works Command Centre"),
    "Admin": ("admin_portal.work_orders", "admin_portal.work_orders_feed", "Works Command Centre"),
    "Property Manager": ("property_manager.work_orders", "property_manager.work_orders_feed", "Works Command Centre"),
    "Assistant": ("assistant.work_orders", "assistant.work_orders_feed", "Assistant Works Queue"),
    "Assistant Property Manager": ("assistant.work_orders", "assistant.work_orders_feed", "Assistant Works Queue"),
    "Contractor": ("contractor.work_orders", "contractor.work_orders_feed", "Contractor Work Queue"),
    "Admin Contractor": ("contractor.work_orders", "contractor.work_orders_feed", "Contractor Work Queue"),
    "Member": ("members.works", "members.works_feed", "Members Works"),
    "Resident": ("members.works", "members.works_feed", "Members Works"),
}

MANAGEMENT_ROLES = {
    "Super Admin",
    "Admin",
    "Property Manager",
    "Assistant",
    "Assistant Property Manager",
    "Financial Controller",
    "Finance",
    "Director",
}
CONTRACTOR_ROLES = {"Contractor", "Admin Contractor"}
MEMBER_ROLES = {"Member", "Resident"}

ROLE_QUICK_ACTIONS = {
    "Super Admin": (
        ("view_notifications", "Review Notifications", "GET", "notifications.index", "Open the role-aware Notification Centre."),
        ("open_works", "Open Works", "GET", "super_admin.work_orders", "Open the Works Logix command centre."),
        ("ask_gar", "Ask GAR", "GET", "super_admin.gar_inquiry", "Ask GAR using source-backed Super Admin context."),
    ),
    "Admin": (
        ("view_notifications", "Review Notifications", "GET", "notifications.index", "Open the role-aware Notification Centre."),
        ("open_works", "Open Works", "GET", "admin_portal.work_orders", "Open the Works Logix command centre."),
        ("ask_gar", "Ask GAR", "GET", "admin_portal.gar_inquiry", "Ask GAR using source-backed Admin context."),
    ),
    "Property Manager": (
        ("view_notifications", "Review Notifications", "GET", "notifications.index", "Open the role-aware Notification Centre."),
        ("open_works", "Open Works", "GET", "property_manager.work_orders", "Open the Works Logix command centre."),
        ("ask_gar", "Ask GAR", "GET", "property_manager.gar_inquiry", "Ask GAR using source-backed PM context."),
    ),
    "Assistant": (
        ("view_notifications", "Review Notifications", "GET", "notifications.index", "Open the role-aware Notification Centre."),
        ("open_works", "Open Works", "GET", "assistant.work_orders", "Open the Assistant Works queue."),
        ("ask_gar", "Ask GAR", "GET", "assistant.gar_inquiry", "Ask GAR using source-backed Assistant context."),
    ),
    "Assistant Property Manager": (
        ("view_notifications", "Review Notifications", "GET", "notifications.index", "Open the role-aware Notification Centre."),
        ("open_works", "Open Works", "GET", "assistant.work_orders", "Open the Assistant Works queue."),
        ("ask_gar", "Ask GAR", "GET", "assistant.gar_inquiry", "Ask GAR using source-backed Assistant context."),
    ),
    "Contractor": (
        ("view_notifications", "Review Notifications", "GET", "notifications.index", "Open the role-aware Notification Centre."),
        ("open_assigned_work", "Open Assigned Work", "GET", "contractor.work_orders", "Open assigned Contractor Logix jobs."),
        ("submit_completion", "Submit Completion", "POST", "contractor.update_work_order", "Submit completion evidence through Contractor Logix."),
        ("ask_gar", "Ask GAR", "GET", "contractor.gar_inquiry", "Ask GAR using assigned-job context."),
    ),
    "Admin Contractor": (
        ("view_notifications", "Review Notifications", "GET", "notifications.index", "Open the role-aware Notification Centre."),
        ("open_assigned_work", "Open Assigned Work", "GET", "contractor.work_orders", "Open assigned Contractor Logix jobs."),
        ("submit_completion", "Submit Completion", "POST", "contractor.update_work_order", "Submit completion evidence through Contractor Logix."),
        ("ask_gar", "Ask GAR", "GET", "contractor.gar_inquiry", "Ask GAR using assigned-job context."),
    ),
    "Member": (
        ("view_notifications", "Review Notifications", "GET", "notifications.index", "Open the role-aware Notification Centre."),
        ("new_request", "New Maintenance Request", "POST", "members.create_maintenance_request", "Submit a member maintenance request through Members Logix."),
        ("request_reopen", "Request Reopen", "POST", "members.request_reopen", "Request a reopened Works Logix review."),
        ("ask_gar", "Ask GAR", "GET", "members.gar_inquiry", "Ask GAR using linked-unit context."),
    ),
    "Resident": (
        ("view_notifications", "Review Notifications", "GET", "notifications.index", "Open the role-aware Notification Centre."),
        ("new_request", "New Maintenance Request", "POST", "members.create_maintenance_request", "Submit a resident maintenance request through Members Logix."),
        ("request_reopen", "Request Reopen", "POST", "members.request_reopen", "Request a reopened Works Logix review."),
        ("ask_gar", "Ask GAR", "GET", "members.gar_inquiry", "Ask GAR using linked-unit context."),
    ),
    "Financial Controller": (
        ("view_notifications", "Review Notifications", "GET", "notifications.index", "Open the role-aware Notification Centre."),
        ("open_dashboard", "Open Finance Dashboard", "GET", "finance.dashboard", "Open Finance Logix."),
        ("ask_gar", "Ask GAR", "GET", "finance.gar_inquiry", "Ask GAR using finance-ready source context."),
    ),
    "Finance": (
        ("view_notifications", "Review Notifications", "GET", "notifications.index", "Open the role-aware Notification Centre."),
        ("open_dashboard", "Open Finance Dashboard", "GET", "finance.dashboard", "Open Finance Logix."),
        ("ask_gar", "Ask GAR", "GET", "finance.gar_inquiry", "Ask GAR using finance-ready source context."),
    ),
    "Director": (
        ("view_notifications", "Review Notifications", "GET", "notifications.index", "Open the role-aware Notification Centre."),
        ("open_dashboard", "Open Director Dashboard", "GET", "director.dashboard", "Open Director Logix."),
        ("ask_gar", "Ask GAR", "GET", "director.gar_inquiry", "Ask GAR using director-safe source context."),
    ),
}

ACTION_METADATA = {
    "notifications.index": {
        "owning_module": "core_notifications",
        "required_context_fields": [],
        "evidence_reference_supported": False,
    },
    "super_admin.work_orders": {
        "owning_module": "works_logix",
        "required_context_fields": [],
        "evidence_reference_supported": False,
    },
    "admin_portal.work_orders": {
        "owning_module": "works_logix",
        "required_context_fields": [],
        "evidence_reference_supported": False,
    },
    "property_manager.work_orders": {
        "owning_module": "works_logix",
        "required_context_fields": [],
        "evidence_reference_supported": False,
    },
    "assistant.work_orders": {
        "owning_module": "works_logix",
        "required_context_fields": [],
        "evidence_reference_supported": False,
    },
    "contractor.work_orders": {
        "owning_module": "contractor_logix",
        "required_context_fields": [],
        "evidence_reference_supported": False,
    },
    "contractor.update_work_order": {
        "owning_module": "contractor_logix",
        "required_context_fields": ["work_order_id", "action", "completion_note"],
        "evidence_reference_supported": True,
    },
    "members.create_maintenance_request": {
        "owning_module": "members_logix",
        "required_context_fields": ["unit_id", "title", "description"],
        "evidence_reference_supported": True,
    },
    "members.request_reopen": {
        "owning_module": "members_logix",
        "required_context_fields": ["work_order_id", "reason"],
        "evidence_reference_supported": True,
    },
    "finance.dashboard": {
        "owning_module": "finance_logix",
        "required_context_fields": [],
        "evidence_reference_supported": False,
    },
    "director.dashboard": {
        "owning_module": "director_logix",
        "required_context_fields": [],
        "evidence_reference_supported": False,
    },
}

APP_POLICY = {
    "contract_version": "phase3e-app-home-v1",
    "auth": {
        "requires_authenticated_session": True,
        "uses_server_session": True,
        "csrf_required_for_mutations": True,
        "role_visibility_enforced_server_side": True,
    },
    "offline": {
        "static_shell_cache_only": True,
        "business_records_cached": False,
        "offline_mutations_supported": False,
        "offline_message": "Reconnect before creating, approving, returning, closing or reopening operational records.",
    },
    "sync": {
        "feeds_are_read_only": True,
        "mutations_use_governed_post_routes": True,
        "recommended_refresh_seconds": 60,
        "priority_refresh_seconds": 20,
    },
    "media": {
        "direct_binary_uploads_enabled": False,
        "evidence_references_supported": True,
        "supported_reference_types": ["photo_link", "video_link", "document_link", "secure_url"],
    },
    "gar": {
        "source_backed_required": True,
        "role_aware": True,
        "model_only_answers_blocked_by_default": True,
    },
}


APP_MEDIA_CONTRACT = {
    "contract_version": "phase3e-app-media-v1",
    "source_model": "MediaFile",
    "upload_strategy": "evidence_reference_now_media_file_later",
    "direct_binary_uploads_enabled": False,
    "evidence_references_supported": True,
    "supported_reference_types": ["photo_link", "video_link", "document_link", "secure_url"],
    "supported_file_types": ["image", "video", "pdf", "document"],
    "contexts": [
        {
            "key": "member_maintenance_request",
            "owning_module": "members_logix",
            "action_key": "new_request",
            "related_table": "maintenance_request",
            "required_context_fields": ["unit_id", "title", "description"],
            "visibility": "management_and_linked_member",
        },
        {
            "key": "contractor_completion_evidence",
            "owning_module": "contractor_logix",
            "action_key": "submit_completion",
            "related_table": "work_order_completion",
            "required_context_fields": ["work_order_id", "action", "completion_note"],
            "visibility": "management_contractor_and_linked_member",
        },
        {
            "key": "member_work_order_feedback",
            "owning_module": "members_logix",
            "action_key": "submit_feedback",
            "related_table": "contractor_feedback",
            "required_context_fields": ["work_order_id", "rating"],
            "visibility": "management_and_linked_member",
        },
        {
            "key": "member_reopen_request",
            "owning_module": "members_logix",
            "action_key": "request_reopen",
            "related_table": "work_order_reopen_request",
            "required_context_fields": ["work_order_id", "reason"],
            "visibility": "management_and_linked_member",
        },
    ],
    "guardrails": {
        "requires_authenticated_session": True,
        "requires_csrf_for_mutation": True,
        "requires_record_context": True,
        "server_generated_media_ids": True,
        "virus_scan_required_before_visibility": True,
        "role_visibility_required": True,
        "client_generated_business_ids_allowed": False,
        "offline_upload_queue_allowed": False,
    },
    "gar_processing": {
        "enabled_after_source_record": True,
        "stores_parsed_summary": True,
        "stores_extracted_data": True,
        "classification_field": "MediaFile.ai_classification",
        "confidence_field": "MediaFile.ai_confidence_score",
        "source_backed_required": True,
    },
}


def _role_name(user) -> str:
    role = getattr(user, "role", None)
    return getattr(role, "name", None) or getattr(user, "role_name", None) or "Unassigned"


def _safe_url(endpoint: str | None, **values) -> str | None:
    if not endpoint:
        return None
    try:
        return url_for(endpoint, **values)
    except BuildError:
        return None


def _module_card(key: str, label: str, screen_url: str | None, feed_url: str | None, description: str) -> dict:
    return {
        "key": key,
        "label": label,
        "description": description,
        "screen_url": screen_url,
        "feed_url": feed_url,
        "enabled": bool(screen_url or feed_url),
    }


def _nav_item(
    key: str,
    label: str,
    icon: str,
    url: str | None,
    feed_key: str | None,
    badge_count: int = 0,
) -> dict:
    return {
        "key": key,
        "label": label,
        "icon": icon,
        "url": url,
        "feed_key": feed_key,
        "badge_count": max(int(badge_count or 0), 0),
        "enabled": bool(url or feed_key),
    }


def _app_navigation(
    dashboard_url: str | None,
    notifications_url: str | None,
    works_screen_url: str | None,
    works_label: str,
    gar_url: str | None,
    summary: dict,
) -> dict:
    primary_items = [
        _nav_item("home", "Home", "home", dashboard_url, "home"),
        _nav_item(
            "notifications",
            "Alerts",
            "notifications",
            notifications_url,
            "notifications",
            summary.get("unread_notifications", 0),
        ),
    ]
    if works_screen_url:
        primary_items.append(_nav_item(
            "works",
            works_label,
            "build",
            works_screen_url,
            "works",
            summary.get("action_notifications", 0),
        ))
    primary_items.append(_nav_item("gar", "GAR", "psychology", gar_url, "gar", summary.get("gar_notifications", 0)))

    return {
        "style": "bottom_tabs",
        "badge_source": "notification_summary",
        "primary_items": primary_items,
        "secondary_items": [
            _nav_item("capabilities", "Capabilities", "verified", None, "capabilities"),
        ],
    }


def _app_surface(
    key: str,
    label: str,
    module: str,
    url: str | None,
    feed_key: str | None,
    layout: str,
    priority: str,
    empty_state: str,
) -> dict:
    return {
        "key": key,
        "label": label,
        "module": module,
        "url": url,
        "feed_key": feed_key,
        "layout": layout,
        "priority": priority,
        "empty_state": empty_state,
        "enabled": bool(url or feed_key),
        "requires_online": True,
        "safe_area_required": True,
        "supports_pull_to_refresh": True,
        "source_backed": True,
    }


def _app_surfaces(
    dashboard_url: str | None,
    notifications_url: str | None,
    works_screen_url: str | None,
    works_label: str,
    gar_url: str | None,
) -> dict:
    items = [
        _app_surface(
            "dashboard",
            "Dashboard",
            "core",
            dashboard_url,
            "home",
            "summary_cards",
            "primary",
            "Your dashboard is ready.",
        ),
        _app_surface(
            "notifications",
            "Alerts",
            "core_notifications",
            notifications_url,
            "notifications",
            "attention_queue",
            "primary",
            "No alerts need attention.",
        ),
    ]
    if works_screen_url:
        items.append(_app_surface(
            "works",
            works_label,
            "works_logix",
            works_screen_url,
            "works",
            "operational_queue",
            "primary",
            "No work items need attention.",
        ))
    items.extend([
        _app_surface(
            "gar",
            "GAR",
            "gar_ai",
            gar_url,
            "gar",
            "assistant_panel",
            "primary",
            "GAR context is ready when source records are available.",
        ),
        _app_surface(
            "capabilities",
            "Capabilities",
            "core",
            None,
            "capabilities",
            "diagnostic_list",
            "secondary",
            "Capabilities are available when the app is online.",
        ),
    ])

    return {
        "contract_version": "phase3e-app-surfaces-v1",
        "source": "role_app_home",
        "items": items,
    }


def _deep_link_item(
    key: str,
    label: str,
    target_surface: str,
    url: str | None,
    feed_key: str | None,
) -> dict:
    return {
        "key": key,
        "label": label,
        "target_surface": target_surface,
        "url": url,
        "feed_key": feed_key,
        "allowed": bool(url or feed_key),
        "requires_authenticated_session": True,
        "requires_role_check": True,
        "source_backed": True,
        "return_target_supported": True,
    }


def _app_deep_links(
    dashboard_url: str | None,
    notifications_url: str | None,
    works_screen_url: str | None,
    gar_url: str | None,
) -> dict:
    items = [
        _deep_link_item("open_dashboard", "Open Dashboard", "dashboard", dashboard_url, "home"),
        _deep_link_item("open_notifications", "Open Alerts", "notifications", notifications_url, "notifications"),
        _deep_link_item("open_gar", "Open GAR", "gar", gar_url, "gar"),
        _deep_link_item("open_capabilities", "Open Capabilities", "capabilities", None, "capabilities"),
    ]
    if works_screen_url:
        items.insert(2, _deep_link_item("open_works", "Open Works", "works", works_screen_url, "works"))

    return {
        "contract_version": "phase3e-app-deep-links-v1",
        "source": "role_app_home",
        "allowed_schemes": ["relative_path"],
        "blocked_schemes": ["javascript", "data", "file", "external_without_allowlist"],
        "route_resolution": {
            "server_url_for_is_source": True,
            "client_must_not_guess_record_urls": True,
            "notification_links_must_use_safe_targets": True,
            "cross_role_links_blocked_server_side": True,
        },
        "notification_target_rules": {
            "source_reference_required": True,
            "return_target_supported": True,
            "mark_read_requires_post": True,
            "open_target_must_match_role_visibility": True,
        },
        "items": items,
    }


def _app_session_contract(user) -> dict:
    return {
        "contract_version": "phase3e-app-session-v1",
        "mode": "server_session_cookie",
        "authenticated": bool(user and getattr(user, "is_authenticated", False)),
        "login_url": _safe_url("auth.login"),
        "logout_url": _safe_url("auth.logout"),
        "csrf": {
            "required_for_mutations": True,
            "header_name": "X-CSRFToken",
            "form_field_name": "csrf_token",
            "token_source": "server_rendered_page_or_bootstrap_meta",
            "refresh_on_login": True,
        },
        "device": {
            "client_device_id_allowed": True,
            "server_device_record_required": False,
            "device_id_is_not_authentication": True,
            "used_for": ["push_target_future", "app_diagnostics_future"],
        },
        "expiry_handling": {
            "business_feeds_require_authenticated_session": True,
            "unauthenticated_business_feed_status": 401,
            "client_must_redirect_to_login": True,
            "client_must_clear_cached_business_state": True,
        },
        "logout": {
            "clears_server_session": True,
            "client_must_clear_app_state": True,
            "post_logout_target": _safe_url("auth.login"),
        },
        "security": {
            "role_visibility_enforced_server_side": True,
            "company_scope_enforced_server_side": True,
            "csrf_required_for_post": True,
            "offline_mutations_allowed": False,
        },
    }


def _app_notifications_contract(
    notifications_url: str | None,
    notifications_feed_url: str | None,
    summary: dict,
) -> dict:
    return {
        "contract_version": "phase3e-app-notifications-v1",
        "source_model": "Notification",
        "delivery_strategy": "in_app_feed_now_push_later",
        "centre_url": notifications_url,
        "feed_url": notifications_feed_url,
        "badge_source": "notification_summary",
        "refresh_seconds": APP_POLICY["sync"]["priority_refresh_seconds"],
        "badge_counts": {
            "unread": max(int(summary.get("unread_notifications", 0) or 0), 0),
            "action_required": max(int(summary.get("action_notifications", 0) or 0), 0),
            "gar": max(int(summary.get("gar_notifications", 0) or 0), 0),
            "high_priority": max(int(summary.get("high_priority_notifications", 0) or 0), 0),
        },
        "actions": [
            {
                "key": "open_notification",
                "method": "GET",
                "endpoint": "notifications.open",
                "requires_context_fields": ["notification_id"],
                "marks_read": True,
                "safe_target_required": True,
            },
            {
                "key": "mark_read",
                "method": "POST",
                "endpoint": "notifications.mark_read",
                "requires_context_fields": ["notification_id"],
                "requires_csrf": True,
                "return_target_supported": True,
            },
            {
                "key": "mark_all_read",
                "method": "POST",
                "endpoint": "notifications.mark_all_read",
                "url": _safe_url("notifications.mark_all_read"),
                "requires_context_fields": [],
                "requires_csrf": True,
                "return_target_supported": True,
            },
        ],
        "visibility": {
            "recipient_scoped": True,
            "role_visibility_enforced": True,
            "company_scope_enforced": True,
            "source_references_required": True,
        },
        "push_future": {
            "enabled": False,
            "requires_device_registration": True,
            "uses_app_session_device_contract": True,
            "payload_must_not_include_private_business_data": True,
        },
        "gar": {
            "gar_category_supported": True,
            "gar_notifications_are_badged": True,
            "source_backed_required": True,
        },
    }


def _app_resilience_contract() -> dict:
    return {
        "contract_version": "phase3e-app-resilience-v1",
        "offline": {
            "static_shell_available": True,
            "business_feeds_available": False,
            "mutations_allowed": False,
            "display_mode": "read_only_cached_shell",
            "retry_when_online": True,
        },
        "stale_feed": {
            "warning_seconds": 120,
            "force_refetch_after_mutation": True,
            "show_last_updated": True,
            "stale_badge_allowed": True,
        },
        "http_errors": {
            "unauthenticated": {
                "status": 401,
                "action": "redirect_to_login",
                "clear_cached_business_state": True,
            },
            "forbidden": {
                "status": 403,
                "action": "show_no_access",
                "refetch_capabilities": True,
            },
            "not_found": {
                "status": 404,
                "action": "show_record_unavailable",
                "refetch_parent_surface": True,
            },
            "validation_error": {
                "status": 400,
                "action": "keep_form_state",
                "show_field_errors": True,
            },
            "server_error": {
                "status": 500,
                "action": "show_retry",
                "include_trace_to_client": False,
            },
        },
        "mutation_failure": {
            "optimistic_updates_allowed": False,
            "client_must_refetch_source_record": True,
            "server_message_is_authoritative": True,
            "idempotency_key_future": True,
        },
        "gar_degraded": {
            "source_backed_required": True,
            "model_only_fallback_allowed": False,
            "show_unavailable_when_sources_missing": True,
            "show_source_reference_gap": True,
        },
        "user_messages": {
            "plain_language": True,
            "no_stack_traces": True,
            "preserve_context": True,
            "suggest_next_action": True,
        },
    }


def _app_observability_contract() -> dict:
    return {
        "contract_version": "phase3e-app-observability-v1",
        "source": "app_runtime_contract",
        "diagnostics": {
            "client_event_reporting_enabled": False,
            "server_side_logging_required": True,
            "correlation_id_supported_future": True,
            "device_diagnostics_allowed": True,
        },
        "allowed_client_events": [
            "app_bootstrap_loaded",
            "feed_refresh_failed",
            "mutation_failed",
            "session_expired",
            "gar_source_unavailable",
        ],
        "privacy": {
            "no_business_payloads_in_diagnostics": True,
            "no_gar_answers_in_diagnostics": True,
            "no_document_text_in_diagnostics": True,
            "no_personal_contact_details_in_diagnostics": True,
            "role_context_allowed": True,
            "contract_versions_allowed": True,
        },
        "performance": {
            "track_feed_latency_ms": True,
            "track_screen_load_ms": True,
            "track_static_shell_cache_hit": True,
            "track_mutation_round_trip_ms": True,
            "slow_feed_warning_ms": 3000,
        },
        "health": {
            "uses_health_feed": True,
            "health_feed_key": "health",
            "service_worker_status_required": True,
            "manifest_status_required": True,
        },
        "support": {
            "user_visible_reference": "support_reference",
            "include_contract_versions": True,
            "include_role_context": True,
            "include_user_id": False,
            "include_company_id": False,
        },
    }


def _app_compatibility_contract() -> dict:
    return {
        "contract_version": "phase3e-app-compatibility-v1",
        "source": "app_runtime_contract",
        "client_support": {
            "supported_client_types": [
                "responsive_web",
                "installed_pwa",
                "future_native_app",
            ],
            "minimum_contract_bundle": "phase3e",
            "current_contract_bundle": "phase3e",
            "incompatible_clients_blocked": True,
        },
        "feed_versions": {
            "health": "v1",
            "home": "v1",
            "capabilities": "v1",
            "notifications": "v1",
            "works": "v1",
            "gar": "v1",
        },
        "version_policy": {
            "server_is_authority": True,
            "clients_must_check_health_feed": True,
            "clients_must_refresh_capabilities_on_version_change": True,
            "backwards_compatible_read_fields": True,
            "remove_fields_requires_new_contract": True,
        },
        "feature_flags": {
            "source": "server_capabilities_feed",
            "client_may_hide_unavailable": True,
            "client_must_not_enable_unlisted_features": True,
            "role_visibility_server_enforced": True,
        },
        "upgrade_behaviour": {
            "soft_refresh_on_minor_change": True,
            "force_reload_on_major_contract_change": True,
            "clear_static_shell_on_service_worker_update": True,
            "show_update_available_prompt": True,
        },
        "deprecation": {
            "deprecated_contracts": [],
            "minimum_notice_days_future": 30,
            "old_clients_get_read_only_safe_state": True,
        },
        "support": {
            "include_app_version": True,
            "include_contract_bundle": True,
            "include_feed_versions": True,
            "include_role_context": True,
            "no_business_payloads": True,
        },
    }


def _app_sync_contract(feeds: dict) -> dict:
    return {
        "contract_version": "phase3e-app-sync-v1",
        "mode": "session_bound_polling",
        "read_only_feed_keys": [key for key, value in feeds.items() if value],
        "refresh_seconds": {
            "home": APP_POLICY["sync"]["recommended_refresh_seconds"],
            "capabilities": 300,
            "notifications": APP_POLICY["sync"]["priority_refresh_seconds"],
            "works": 30,
            "gar": APP_POLICY["sync"]["recommended_refresh_seconds"],
        },
        "online_required_for": [
            "create",
            "route",
            "approve",
            "return",
            "close",
            "reopen",
            "upload_evidence",
            "ask_gar",
        ],
        "cache_policy": {
            "static_shell": True,
            "business_records": False,
            "gar_answers": False,
            "notification_payloads": False,
        },
        "mutation_policy": {
            "allowed_from_feed": False,
            "requires_governed_post_route": True,
            "requires_csrf": True,
            "requires_record_context": True,
            "client_generated_business_ids_allowed": False,
        },
        "conflict_policy": {
            "server_record_wins": True,
            "client_must_refetch_after_mutation": True,
            "stale_feed_warning_seconds": 120,
        },
    }


def _member_scope(user) -> dict:
    member_ids: list[int] = []
    client_ids: set[int] = set()
    unit_ids: set[int] = set()
    try:
        memberships = list(getattr(user, "memberships", []) or [])
    except Exception:
        memberships = []

    for member in memberships:
        member_id = getattr(member, "id", None)
        if member_id:
            member_ids.append(member_id)
        client_id = getattr(member, "client_id", None)
        if client_id:
            client_ids.add(client_id)

        try:
            unit_links = member.unit_links.all() if hasattr(member.unit_links, "all") else list(member.unit_links or [])
        except Exception:
            unit_links = []
        for link in unit_links:
            unit_id = getattr(link, "unit_id", None)
            if unit_id:
                unit_ids.add(unit_id)

    return {
        "member_ids": member_ids,
        "client_ids": sorted(client_ids),
        "unit_ids": sorted(unit_ids),
        "linked_member_count": len(member_ids),
        "linked_client_count": len(client_ids),
        "linked_unit_count": len(unit_ids),
    }


def _app_scope(user, role_name: str) -> dict:
    company = getattr(user, "company", None)
    company_id = getattr(user, "company_id", None)
    member_scope = _member_scope(user)
    contractor_id = getattr(user, "contractor_id", None)

    if role_name in MEMBER_ROLES:
        boundary = "linked_member_units"
        allowed_scope_types = ["member", "client", "unit", "maintenance_request", "work_order", "notification", "gar"]
        default_client_scope = "linked_clients"
    elif role_name in CONTRACTOR_ROLES:
        boundary = "assigned_contractor_work"
        allowed_scope_types = ["contractor", "work_order", "completion_evidence", "notification", "gar"]
        default_client_scope = "assigned_jobs_only"
    elif role_name in MANAGEMENT_ROLES:
        boundary = "company"
        allowed_scope_types = ["company", "client", "unit", "work_order", "contract", "document", "notification", "gar"]
        default_client_scope = "company_clients"
    else:
        boundary = "signed_in_user"
        allowed_scope_types = ["notification", "gar"]
        default_client_scope = "none"

    return {
        "contract_version": "phase3e-app-scope-v1",
        "role": role_name,
        "role_context": _normalised_role_context(role_name),
        "company": {
            "id": company_id,
            "name": getattr(company, "name", None),
        },
        "data_boundary": boundary,
        "allowed_scope_types": allowed_scope_types,
        "client_compartment": {
            "default_scope": default_client_scope,
            "client_filter_required_for_client_screens": True,
            "cross_client_rollups_require_management_role": True,
            "server_side_filters_required": True,
        },
        "member_scope": member_scope,
        "contractor_scope": {
            "contractor_id": contractor_id,
            "assigned_work_only": role_name in CONTRACTOR_ROLES,
        },
        "gar_visibility": {
            "role_aware": True,
            "source_backed_required": True,
            "scope_required": True,
            "model_only_answers_allowed": False,
        },
        "source_of_truth": {
            "user": "User.id",
            "role": "User.role_id",
            "company": "User.company_id",
            "member_units": "Member and UnitMembership",
            "contractor": "User.contractor_id",
        },
    }


def _quick_actions_for_role(role_name: str) -> list[dict]:
    actions: list[dict] = []
    for key, label, method, endpoint, description in ROLE_QUICK_ACTIONS.get(role_name, ()):
        needs_context = "<" in endpoint or endpoint in {
            "contractor.update_work_order",
            "members.create_maintenance_request",
            "members.request_reopen",
        }
        metadata = ACTION_METADATA.get(endpoint, {
            "owning_module": "gar_ai" if endpoint.endswith(".gar_inquiry") else "core",
            "required_context_fields": [],
            "evidence_reference_supported": False,
        })
        action_url = None if needs_context else _safe_url(endpoint)
        actions.append({
            "key": key,
            "label": label,
            "method": method,
            "endpoint": endpoint,
            "url": action_url,
            "requires_context": needs_context,
            "requires_csrf": method != "GET",
            "description": description,
            "governed": True,
            "owning_module": metadata["owning_module"],
            "required_context_fields": list(metadata["required_context_fields"]),
            "requires_online": True,
            "confirmation_required": method != "GET",
            "offline_queue_allowed": False,
            "evidence_reference_supported": bool(metadata["evidence_reference_supported"]),
            "server_authoritative": True,
        })
    return actions


def _normalised_role_context(role_name: str) -> str:
    return role_name.strip().lower().replace(" ", "_").replace("-", "_")


def _module_capability(contract) -> dict:
    dashboard_url = _safe_url(contract.dashboard_endpoint)
    return {
        "key": contract.key,
        "name": contract.name,
        "status": contract.status,
        "dashboard_endpoint": contract.dashboard_endpoint,
        "dashboard_url": dashboard_url,
        "owned_data": list(contract.owned_data),
        "shared_links": list(contract.shared_links),
        "app_ready": contract.key in {
            "works",
            "members",
            "contractor",
            "assistant",
            "admin_portal",
            "gar_ai",
        },
        "source_of_truth": True,
    }


def build_app_health_payload(user=None) -> dict:
    is_authenticated = bool(user and getattr(user, "is_authenticated", False))
    role_name = _role_name(user) if is_authenticated else "Anonymous"
    company = getattr(user, "company", None) if is_authenticated else None

    return {
        "context_type": "app_health",
        "status": "operational",
        "generated_at": datetime.now(UTC).isoformat(),
        "authenticated": is_authenticated,
        "user": {
            "id": getattr(user, "id", None) if is_authenticated else None,
            "role": role_name,
            "role_context": _normalised_role_context(role_name),
            "company_id": getattr(user, "company_id", None) if is_authenticated else None,
            "company_name": getattr(company, "name", None),
        },
        "contract_versions": {
            "app_policy": APP_POLICY["contract_version"],
            "app_scope": "phase3e-app-scope-v1",
            "app_navigation": "phase3e-app-navigation-v1",
            "app_surfaces": "phase3e-app-surfaces-v1",
            "app_deep_links": "phase3e-app-deep-links-v1",
            "app_session": "phase3e-app-session-v1",
            "app_notifications": "phase3e-app-notifications-v1",
            "app_resilience": "phase3e-app-resilience-v1",
            "app_observability": "phase3e-app-observability-v1",
            "app_compatibility": "phase3e-app-compatibility-v1",
            "app_sync": "phase3e-app-sync-v1",
            "app_media": APP_MEDIA_CONTRACT["contract_version"],
            "app_capabilities": "phase3e-app-capabilities-v1",
            "module_settings": "phase3-module-settings-registry-v1",
        },
        "endpoints": {
            "health": _safe_url("app_home.health_feed"),
            "home": _safe_url("app_home.feed"),
            "capabilities": _safe_url("app_home.capabilities_feed"),
            "company_setup": _safe_url("app_home.company_setup_feed"),
            "module_settings": _safe_url("app_home.module_settings_feed"),
            "notifications": _safe_url("notifications.feed"),
            "service_worker": _safe_url("app_shell_service_worker"),
            "manifest": "/static/manifest.webmanifest",
        },
        "runtime": {
            "pwa_shell_available": True,
            "static_shell_only_offline": True,
            "read_only_feeds": True,
            "governed_mutations": True,
            "server_session_required_for_business_feeds": True,
            "csrf_required_for_mutations": True,
        },
        "gar": {
            "role_aware": True,
            "source_backed_required": True,
            "model_only_answers_allowed": False,
        },
        "source_references": [
            {
                "model": "AppPolicy",
                "record_id": None,
                "label": "Phase 3E app/mobile runtime contract",
                "fields": ["auth", "offline", "sync", "media", "gar"],
            },
            {
                "model": "User",
                "record_id": getattr(user, "id", None) if is_authenticated else None,
                "label": "Signed-in user when available",
                "fields": ["id", "role_id", "company_id", "contractor_id"],
            },
        ],
    }


def build_app_capabilities_payload(user) -> dict:
    role_name = _role_name(user)
    role_context = _normalised_role_context(role_name)
    modules = [_module_capability(contract) for contract in module_contracts()]
    gar_registry = build_gar_capability_registry(role_context=role_context)
    app_home = build_app_home_payload(user)

    return {
        "context_type": "app_capabilities",
        "contract_version": "phase3e-app-capabilities-v1",
        "user": app_home["user"],
        "app_policy": APP_POLICY,
        "app_scope": app_home["app_scope"],
        "app_navigation": app_home["app_navigation"],
        "app_surfaces": app_home["app_surfaces"],
        "app_deep_links": app_home["app_deep_links"],
        "app_session": app_home["app_session"],
        "app_notifications": app_home["app_notifications"],
        "app_resilience": app_home["app_resilience"],
        "app_observability": app_home["app_observability"],
        "app_compatibility": app_home["app_compatibility"],
        "app_sync": app_home["app_sync"],
        "app_media": APP_MEDIA_CONTRACT,
        "feeds": app_home["feeds"],
        "quick_actions": app_home["quick_actions"],
        "modules": modules,
        "gar": gar_registry,
        "readiness": {
            "module_count": len(modules),
            "app_ready_module_count": sum(1 for module in modules if module["app_ready"]),
            "read_only_feeds": True,
            "governed_mutations": True,
            "static_shell_only_offline": True,
        },
        "source_references": [
            {
                "model": "ModuleContract",
                "record_id": None,
                "label": "Core module contract registry",
                "fields": ["key", "name", "status", "owned_data", "shared_links"],
            },
            {
                "model": "GarCapability",
                "record_id": None,
                "label": "GAR capability registry",
                "fields": ["key", "status", "source_backed", "source_records", "role_visibility"],
            },
        ],
    }


def build_app_home_payload(user) -> dict:
    role_name = _role_name(user)
    notification_context = build_notification_context(
        user.id,
        NotificationFilters(status="unread"),
        limit=25,
    )
    notification_payload = notification_feed_payload(notification_context)
    notification_stats = notification_context["notification_stats"]
    action_queue = [
        notification_view_payload(item)
        for item in notification_context["action_queue_views"][:5]
    ]

    dashboard_url = _safe_url(ROLE_DASHBOARDS.get(role_name)) or _safe_url("auth.profile")
    works_screen_endpoint, works_feed_endpoint, works_label = ROLE_WORKS_SURFACES.get(role_name, (None, None, "Works"))
    gar_feed_endpoint = ROLE_GAR_FEEDS.get(role_name)
    gar_inquiry_endpoint = ROLE_GAR_INQUIRIES.get(role_name)

    works_screen_url = _safe_url(works_screen_endpoint)
    works_feed_url = _safe_url(works_feed_endpoint)
    gar_feed_url = _safe_url(gar_feed_endpoint)
    gar_inquiry_url = _safe_url(gar_inquiry_endpoint)
    notifications_url = _safe_url("notifications.index")
    notifications_feed_url = _safe_url("notifications.feed")

    modules = [
        _module_card(
            "dashboard",
            "Dashboard",
            dashboard_url,
            None,
            "Role dashboard for the current user.",
        ),
        _module_card(
            "notifications",
            "Notifications",
            notifications_url,
            notifications_feed_url,
            "Role-aware alerts and workflow action queue.",
        ),
        _module_card(
            "gar",
            "GAR AI",
            dashboard_url,
            gar_feed_url,
            "Source-backed GAR context for this role.",
        ),
    ]
    if works_screen_url or works_feed_url:
        modules.append(_module_card(
            "works",
            works_label,
            works_screen_url,
            works_feed_url,
            "Permitted Works Logix queue for this user.",
        ))

    source_references = notification_payload.get("source_references") or []
    source_references.append({
        "model": "User",
        "record_id": getattr(user, "id", None),
        "label": "Signed-in app user",
        "fields": ["id", "full_name", "email", "role_id", "company_id"],
    })

    summary = {
        "unread_notifications": notification_context["unread_count"],
        "read_notifications": notification_context["read_count"],
        "all_notifications": notification_context["all_count"],
        "action_notifications": notification_stats["action_count"],
        "gar_notifications": notification_stats["gar_count"],
        "high_priority_notifications": notification_stats["high_priority_count"],
    }
    feeds = {
        "home": _safe_url("app_home.feed"),
        "capabilities": _safe_url("app_home.capabilities_feed"),
        "company_setup": _safe_url("app_home.company_setup_feed"),
        "module_settings": _safe_url("app_home.module_settings_feed"),
        "notifications": notifications_feed_url,
        "works": works_feed_url,
        "gar": gar_feed_url,
        "gar_inquiry": gar_inquiry_url,
    }

    return {
        "context_type": "app_home",
        "user": {
            "id": getattr(user, "id", None),
            "full_name": getattr(user, "full_name", None) or getattr(user, "name", None),
            "email": getattr(user, "email", None),
            "role": role_name,
            "company_id": getattr(user, "company_id", None),
        },
        "navigation": {
            "dashboard_url": dashboard_url,
            "notifications_url": notifications_url,
            "works_url": works_screen_url,
            "gar_url": dashboard_url,
        },
        "app_scope": _app_scope(user, role_name),
        "app_navigation": _app_navigation(
            dashboard_url,
            notifications_url,
            works_screen_url,
            works_label,
            dashboard_url,
            summary,
        ),
        "app_surfaces": _app_surfaces(
            dashboard_url,
            notifications_url,
            works_screen_url,
            works_label,
            dashboard_url,
        ),
        "app_deep_links": _app_deep_links(
            dashboard_url,
            notifications_url,
            works_screen_url,
            dashboard_url,
        ),
        "app_session": _app_session_contract(user),
        "app_notifications": _app_notifications_contract(
            notifications_url,
            notifications_feed_url,
            summary,
        ),
        "app_resilience": _app_resilience_contract(),
        "app_observability": _app_observability_contract(),
        "app_compatibility": _app_compatibility_contract(),
        "app_sync": _app_sync_contract(feeds),
        "app_media": APP_MEDIA_CONTRACT,
        "feeds": feeds,
        "summary": summary,
        "modules": modules,
        "quick_actions": _quick_actions_for_role(role_name),
        "app_policy": APP_POLICY,
        "priority_actions": action_queue,
        "source_references": source_references,
    }
