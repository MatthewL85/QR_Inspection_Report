"""Verify the role-aware app home feed remains stable."""

from __future__ import annotations

from datetime import UTC, datetime
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


REQUIRED_TOP_LEVEL_KEYS = (
    "context_type",
    "user",
    "navigation",
    "app_scope",
    "app_navigation",
    "app_surfaces",
    "app_deep_links",
    "app_session",
    "app_notifications",
    "app_resilience",
    "app_observability",
    "app_compatibility",
    "app_sync",
    "app_media",
    "feeds",
    "summary",
    "modules",
    "quick_actions",
    "app_policy",
    "priority_actions",
    "source_references",
)

REQUIRED_FEED_KEYS = (
    "home",
    "capabilities",
    "company_setup",
    "notifications",
    "works",
    "gar",
    "gar_inquiry",
)
REQUIRED_APP_SCOPE_KEYS = (
    "contract_version",
    "role",
    "role_context",
    "company",
    "data_boundary",
    "allowed_scope_types",
    "client_compartment",
    "member_scope",
    "contractor_scope",
    "gar_visibility",
    "source_of_truth",
)
REQUIRED_APP_NAVIGATION_KEYS = ("style", "badge_source", "primary_items", "secondary_items")
REQUIRED_APP_NAV_ITEM_KEYS = ("key", "label", "icon", "url", "feed_key", "badge_count", "enabled")
REQUIRED_APP_SURFACES_KEYS = ("contract_version", "source", "items")
REQUIRED_APP_SURFACE_ITEM_KEYS = (
    "key",
    "label",
    "module",
    "url",
    "feed_key",
    "layout",
    "priority",
    "empty_state",
    "enabled",
    "requires_online",
    "safe_area_required",
    "supports_pull_to_refresh",
    "source_backed",
)
REQUIRED_APP_DEEP_LINK_KEYS = (
    "contract_version",
    "source",
    "allowed_schemes",
    "blocked_schemes",
    "route_resolution",
    "notification_target_rules",
    "items",
)
REQUIRED_APP_DEEP_LINK_ITEM_KEYS = (
    "key",
    "label",
    "target_surface",
    "url",
    "feed_key",
    "allowed",
    "requires_authenticated_session",
    "requires_role_check",
    "source_backed",
    "return_target_supported",
)
REQUIRED_APP_SESSION_KEYS = (
    "contract_version",
    "mode",
    "authenticated",
    "login_url",
    "logout_url",
    "csrf",
    "device",
    "expiry_handling",
    "logout",
    "security",
)
REQUIRED_APP_NOTIFICATIONS_KEYS = (
    "contract_version",
    "source_model",
    "delivery_strategy",
    "centre_url",
    "feed_url",
    "badge_source",
    "refresh_seconds",
    "badge_counts",
    "actions",
    "visibility",
    "push_future",
    "gar",
)
REQUIRED_APP_RESILIENCE_KEYS = (
    "contract_version",
    "offline",
    "stale_feed",
    "http_errors",
    "mutation_failure",
    "gar_degraded",
    "user_messages",
)
REQUIRED_APP_OBSERVABILITY_KEYS = (
    "contract_version",
    "source",
    "diagnostics",
    "allowed_client_events",
    "privacy",
    "performance",
    "health",
    "support",
)
REQUIRED_APP_COMPATIBILITY_KEYS = (
    "contract_version",
    "source",
    "client_support",
    "feed_versions",
    "version_policy",
    "feature_flags",
    "upgrade_behaviour",
    "deprecation",
    "support",
)
REQUIRED_APP_NOTIFICATION_ACTION_KEYS = (
    "key",
    "method",
    "endpoint",
    "requires_context_fields",
)
REQUIRED_APP_SYNC_KEYS = (
    "contract_version",
    "mode",
    "read_only_feed_keys",
    "refresh_seconds",
    "online_required_for",
    "cache_policy",
    "mutation_policy",
    "conflict_policy",
)
REQUIRED_APP_MEDIA_KEYS = (
    "contract_version",
    "source_model",
    "upload_strategy",
    "direct_binary_uploads_enabled",
    "evidence_references_supported",
    "supported_reference_types",
    "supported_file_types",
    "contexts",
    "guardrails",
    "gar_processing",
)
REQUIRED_APP_MEDIA_CONTEXT_KEYS = (
    "key",
    "owning_module",
    "action_key",
    "related_table",
    "required_context_fields",
    "visibility",
)
REQUIRED_SUMMARY_KEYS = (
    "unread_notifications",
    "read_notifications",
    "all_notifications",
    "action_notifications",
    "gar_notifications",
    "high_priority_notifications",
)
REQUIRED_MODULE_KEYS = ("key", "label", "description", "screen_url", "feed_url", "enabled")
REQUIRED_QUICK_ACTION_KEYS = (
    "key",
    "label",
    "method",
    "endpoint",
    "url",
    "requires_context",
    "requires_csrf",
    "description",
    "governed",
    "owning_module",
    "required_context_fields",
    "requires_online",
    "confirmation_required",
    "offline_queue_allowed",
    "evidence_reference_supported",
    "server_authoritative",
)
REQUIRED_POLICY_SECTIONS = ("contract_version", "auth", "offline", "sync", "media", "gar")


def main() -> int:
    from app import create_app
    from app.extensions import db
    from app.models.core.notification import Notification
    from app.models.core.role import Role
    from app.models.core.user import User
    from app.models.onboarding.company import Company
    from app.services.core.app_home import build_app_home_payload

    app = create_app()
    failures: list[str] = []
    marker = f"APPHOME{datetime.now(UTC).strftime('%y%m%d%H%M%S')}"
    ids: dict[str, list[int]] = {"companies": [], "notifications": [], "users": []}
    created_role_ids: list[int] = []

    rule = next((item for item in app.url_map.iter_rules() if item.endpoint == "app_home.feed"), None)
    if not rule:
        failures.append("Missing app_home.feed route")
    else:
        if rule.rule != "/app/home/feed.json":
            failures.append(f"app_home.feed route changed to {rule.rule}")
        if "GET" not in (rule.methods or set()):
            failures.append("app_home.feed does not allow GET")
        if {"POST", "PUT", "PATCH", "DELETE"}.intersection(rule.methods or set()):
            failures.append("app_home.feed allows a mutating method")

    def _role(name: str) -> Role:
        existing = Role.query.filter_by(name=name).first()
        if existing:
            return existing
        item = Role(name=name, description=f"Temporary role for {marker}")
        db.session.add(item)
        db.session.flush()
        created_role_ids.append(item.id)
        return item

    def _sign_in(client, actor: User) -> None:
        role_name = actor.role.name if actor.role else "Unassigned"
        with client.session_transaction() as sess:
            sess["_user_id"] = str(actor.id)
            sess["_fresh"] = True
            sess["user_id"] = actor.id
            sess["role"] = role_name
            sess["company_id"] = actor.company_id
            sess["user"] = {
                "id": actor.id,
                "email": actor.email,
                "role": role_name,
                "company": actor.company.name if actor.company else "",
                "name": actor.full_name,
                "full_name": actor.full_name,
            }

    def _delete_by_ids(model, item_ids: list[int]) -> None:
        if item_ids:
            model.query.filter(model.id.in_(item_ids)).delete(synchronize_session=False)

    with app.app_context():
        Company.query.filter(Company.subdomain.ilike("apphome%")).delete(synchronize_session=False)
        User.query.filter(User.username.ilike("apphome%")).delete(synchronize_session=False)
        Notification.query.filter(Notification.message.ilike("APPHOME%")).delete(synchronize_session=False)
        db.session.commit()

        try:
            company = Company(
                name=f"{marker} Company",
                company_type="Property Management",
                country="Ireland",
                currency="EUR",
                subdomain=marker.lower(),
            )
            db.session.add(company)
            db.session.flush()
            ids["companies"].append(company.id)

            user = User(
                full_name=f"{marker} Super Admin",
                email=f"{marker.lower()}@example.invalid",
                username=f"{marker.lower()}_super_admin",
                password_hash="not-used",
                pin="0000",
                role_id=_role("Super Admin").id,
                company_id=company.id,
                is_active=True,
            )
            db.session.add(user)
            db.session.flush()
            ids["users"].append(user.id)

            contractor_user = User(
                full_name=f"{marker} Contractor",
                email=f"{marker.lower()}+contractor@example.invalid",
                username=f"{marker.lower()}_contractor",
                password_hash="not-used",
                pin="0000",
                role_id=_role("Contractor").id,
                company_id=company.id,
                is_active=True,
            )
            db.session.add(contractor_user)
            db.session.flush()
            ids["users"].append(contractor_user.id)

            member_user = User(
                full_name=f"{marker} Member",
                email=f"{marker.lower()}+member@example.invalid",
                username=f"{marker.lower()}_member",
                password_hash="not-used",
                pin="0000",
                role_id=_role("Member").id,
                company_id=company.id,
                is_active=True,
            )
            db.session.add(member_user)
            db.session.flush()
            ids["users"].append(member_user.id)

            notification = Notification(
                recipient_id=user.id,
                message=f"{marker} app home action",
                type="works_member_request",
                is_read=False,
                created_at=datetime.now(UTC),
                link_url="/notifications/",
                priority_level="High",
                gar_category="Works Logix",
                suggested_action="Review app home seeded action",
                extracted_data={"source_type": "work_order", "work_order_id": 77},
            )
            db.session.add(notification)
            db.session.flush()
            ids["notifications"].append(notification.id)
            db.session.commit()

            role_payloads = {}
            with app.test_client() as client:
                _sign_in(client, user)
                response = client.get("/app/home/feed.json")
                if response.status_code != 200:
                    failures.append(f"/app/home/feed.json returned HTTP {response.status_code}")
                payload = response.get_json(silent=True) or {}

            for actor, role_name in ((contractor_user, "Contractor"), (member_user, "Member")):
                db.session.refresh(actor)
                with app.test_request_context():
                    role_payloads[role_name] = build_app_home_payload(actor)

            for key in REQUIRED_TOP_LEVEL_KEYS:
                if key not in payload:
                    failures.append(f"app home payload missing: {key}")

            if payload.get("context_type") != "app_home":
                failures.append(f"Unexpected context_type: {payload.get('context_type')}")

            user_payload = payload.get("user") or {}
            if user_payload.get("role") != "Super Admin":
                failures.append("app home user role was not preserved")
            if user_payload.get("company_id") != company.id:
                failures.append("app home user company_id was not preserved")

            feeds = payload.get("feeds") or {}
            for key in REQUIRED_FEED_KEYS:
                if key not in feeds:
                    failures.append(f"app home feeds missing: {key}")
            if feeds.get("home") != "/app/home/feed.json":
                failures.append(f"app home self-feed changed: {feeds.get('home')}")
            if feeds.get("capabilities") != "/app/capabilities/feed.json":
                failures.append(f"app home capabilities feed changed: {feeds.get('capabilities')}")
            if feeds.get("company_setup") != "/app/company-setup/feed.json":
                failures.append(f"app home company setup feed changed: {feeds.get('company_setup')}")
            if feeds.get("notifications") != "/notifications/feed.json":
                failures.append("app home notifications feed missing or changed")

            summary = payload.get("summary") or {}
            for key in REQUIRED_SUMMARY_KEYS:
                if key not in summary:
                    failures.append(f"app home summary missing: {key}")
            if summary.get("unread_notifications", 0) < 1:
                failures.append("app home summary did not count unread notifications")
            if summary.get("action_notifications", 0) < 1:
                failures.append("app home summary did not count action notifications")

            app_scope = payload.get("app_scope") or {}
            for key in REQUIRED_APP_SCOPE_KEYS:
                if key not in app_scope:
                    failures.append(f"app home app_scope missing: {key}")
            if app_scope.get("contract_version") != "phase3e-app-scope-v1":
                failures.append(f"app_scope contract_version changed: {app_scope.get('contract_version')}")
            if app_scope.get("role") != "Super Admin":
                failures.append("app_scope role was not preserved")
            if app_scope.get("role_context") != "super_admin":
                failures.append(f"app_scope role_context changed: {app_scope.get('role_context')}")
            company_scope = app_scope.get("company") or {}
            if company_scope.get("id") != company.id:
                failures.append("app_scope company id was not preserved")
            if company_scope.get("name") != company.name:
                failures.append("app_scope company name was not preserved")
            if app_scope.get("data_boundary") != "company":
                failures.append(f"Super Admin app_scope data_boundary changed: {app_scope.get('data_boundary')}")
            allowed_scope_types = set(app_scope.get("allowed_scope_types") or [])
            for required_scope in ("company", "client", "unit", "work_order", "notification", "gar"):
                if required_scope not in allowed_scope_types:
                    failures.append(f"app_scope allowed_scope_types missing: {required_scope}")
            client_compartment = app_scope.get("client_compartment") or {}
            if client_compartment.get("default_scope") != "company_clients":
                failures.append("app_scope client_compartment default_scope should be company_clients")
            if not client_compartment.get("server_side_filters_required"):
                failures.append("app_scope must require server-side filters")
            if not client_compartment.get("cross_client_rollups_require_management_role"):
                failures.append("app_scope must restrict cross-client rollups to management roles")
            gar_visibility = app_scope.get("gar_visibility") or {}
            if not gar_visibility.get("source_backed_required"):
                failures.append("app_scope GAR visibility must require source-backed answers")
            if gar_visibility.get("model_only_answers_allowed"):
                failures.append("app_scope GAR visibility must block model-only answers")
            source_of_truth = app_scope.get("source_of_truth") or {}
            for required_source in ("user", "role", "company", "member_units", "contractor"):
                if required_source not in source_of_truth:
                    failures.append(f"app_scope source_of_truth missing: {required_source}")

            app_navigation = payload.get("app_navigation") or {}
            for key in REQUIRED_APP_NAVIGATION_KEYS:
                if key not in app_navigation:
                    failures.append(f"app home app_navigation missing: {key}")
            if app_navigation.get("style") != "bottom_tabs":
                failures.append(f"app_navigation style changed: {app_navigation.get('style')}")
            if app_navigation.get("badge_source") != "notification_summary":
                failures.append(f"app_navigation badge_source changed: {app_navigation.get('badge_source')}")

            primary_items = app_navigation.get("primary_items") or []
            primary_item_keys = {item.get("key") for item in primary_items if isinstance(item, dict)}
            for required_item in ("home", "notifications", "works", "gar"):
                if required_item not in primary_item_keys:
                    failures.append(f"app_navigation primary_items missing: {required_item}")
            for item in primary_items + (app_navigation.get("secondary_items") or []):
                for key in REQUIRED_APP_NAV_ITEM_KEYS:
                    if key not in item:
                        failures.append(f"app_navigation item {item.get('key')} missing: {key}")
                if item.get("badge_count", 0) < 0:
                    failures.append(f"app_navigation item {item.get('key')} has negative badge_count")
            notification_item = next((item for item in primary_items if item.get("key") == "notifications"), {})
            if notification_item.get("badge_count", 0) < 1:
                failures.append("app_navigation notifications badge did not use unread notification count")
            works_item = next((item for item in primary_items if item.get("key") == "works"), {})
            if works_item.get("badge_count", 0) < 1:
                failures.append("app_navigation works badge did not use action notification count")

            app_surfaces = payload.get("app_surfaces") or {}
            for key in REQUIRED_APP_SURFACES_KEYS:
                if key not in app_surfaces:
                    failures.append(f"app home app_surfaces missing: {key}")
            if app_surfaces.get("contract_version") != "phase3e-app-surfaces-v1":
                failures.append(f"app_surfaces contract_version changed: {app_surfaces.get('contract_version')}")
            if app_surfaces.get("source") != "role_app_home":
                failures.append(f"app_surfaces source changed: {app_surfaces.get('source')}")
            surface_items = app_surfaces.get("items") or []
            surface_keys = {item.get("key") for item in surface_items if isinstance(item, dict)}
            for required_surface in ("dashboard", "notifications", "works", "gar", "capabilities"):
                if required_surface not in surface_keys:
                    failures.append(f"app_surfaces items missing: {required_surface}")
            for item in surface_items:
                for key in REQUIRED_APP_SURFACE_ITEM_KEYS:
                    if key not in item:
                        failures.append(f"app_surfaces item {item.get('key')} missing: {key}")
                if item.get("requires_online") is not True:
                    failures.append(f"app_surfaces item {item.get('key')} must require online use")
                if item.get("safe_area_required") is not True:
                    failures.append(f"app_surfaces item {item.get('key')} must require safe-area handling")
                if item.get("supports_pull_to_refresh") is not True:
                    failures.append(f"app_surfaces item {item.get('key')} must support pull-to-refresh")
                if item.get("source_backed") is not True:
                    failures.append(f"app_surfaces item {item.get('key')} must be source-backed")

            app_deep_links = payload.get("app_deep_links") or {}
            for key in REQUIRED_APP_DEEP_LINK_KEYS:
                if key not in app_deep_links:
                    failures.append(f"app home app_deep_links missing: {key}")
            if app_deep_links.get("contract_version") != "phase3e-app-deep-links-v1":
                failures.append(f"app_deep_links contract_version changed: {app_deep_links.get('contract_version')}")
            if app_deep_links.get("source") != "role_app_home":
                failures.append(f"app_deep_links source changed: {app_deep_links.get('source')}")
            if "relative_path" not in (app_deep_links.get("allowed_schemes") or []):
                failures.append("app_deep_links must allow relative_path links")
            blocked_schemes = set(app_deep_links.get("blocked_schemes") or [])
            for blocked_scheme in ("javascript", "data", "file", "external_without_allowlist"):
                if blocked_scheme not in blocked_schemes:
                    failures.append(f"app_deep_links blocked_schemes missing: {blocked_scheme}")
            route_resolution = app_deep_links.get("route_resolution") or {}
            for required_rule in (
                "server_url_for_is_source",
                "client_must_not_guess_record_urls",
                "notification_links_must_use_safe_targets",
                "cross_role_links_blocked_server_side",
            ):
                if route_resolution.get(required_rule) is not True:
                    failures.append(f"app_deep_links route rule must be true: {required_rule}")
            notification_rules = app_deep_links.get("notification_target_rules") or {}
            for required_rule in (
                "source_reference_required",
                "return_target_supported",
                "mark_read_requires_post",
                "open_target_must_match_role_visibility",
            ):
                if notification_rules.get(required_rule) is not True:
                    failures.append(f"app_deep_links notification rule must be true: {required_rule}")
            deep_link_items = app_deep_links.get("items") or []
            deep_link_keys = {item.get("key") for item in deep_link_items if isinstance(item, dict)}
            for required_link in ("open_dashboard", "open_notifications", "open_works", "open_gar", "open_capabilities"):
                if required_link not in deep_link_keys:
                    failures.append(f"app_deep_links items missing: {required_link}")
            for item in deep_link_items:
                for key in REQUIRED_APP_DEEP_LINK_ITEM_KEYS:
                    if key not in item:
                        failures.append(f"app_deep_links item {item.get('key')} missing: {key}")
                if item.get("requires_authenticated_session") is not True:
                    failures.append(f"app_deep_links item {item.get('key')} must require auth")
                if item.get("requires_role_check") is not True:
                    failures.append(f"app_deep_links item {item.get('key')} must require role checks")
                if item.get("source_backed") is not True:
                    failures.append(f"app_deep_links item {item.get('key')} must be source-backed")
                if item.get("return_target_supported") is not True:
                    failures.append(f"app_deep_links item {item.get('key')} must support return targets")

            app_session = payload.get("app_session") or {}
            for key in REQUIRED_APP_SESSION_KEYS:
                if key not in app_session:
                    failures.append(f"app home app_session missing: {key}")
            if app_session.get("contract_version") != "phase3e-app-session-v1":
                failures.append(f"app_session contract_version changed: {app_session.get('contract_version')}")
            if app_session.get("mode") != "server_session_cookie":
                failures.append(f"app_session mode changed: {app_session.get('mode')}")
            if app_session.get("authenticated") is not True:
                failures.append("app_session must echo authenticated state for app home")
            if app_session.get("login_url") != "/auth/login":
                failures.append(f"app_session login_url changed: {app_session.get('login_url')}")
            if app_session.get("logout_url") != "/auth/logout":
                failures.append(f"app_session logout_url changed: {app_session.get('logout_url')}")
            csrf = app_session.get("csrf") or {}
            if csrf.get("required_for_mutations") is not True:
                failures.append("app_session CSRF must be required for mutations")
            if csrf.get("header_name") != "X-CSRFToken":
                failures.append("app_session CSRF header name changed")
            if csrf.get("form_field_name") != "csrf_token":
                failures.append("app_session CSRF form field changed")
            if csrf.get("refresh_on_login") is not True:
                failures.append("app_session CSRF must refresh on login")
            device = app_session.get("device") or {}
            if device.get("device_id_is_not_authentication") is not True:
                failures.append("app_session device id must not be authentication")
            if device.get("server_device_record_required") is not False:
                failures.append("app_session must not require server device records yet")
            expiry = app_session.get("expiry_handling") or {}
            if expiry.get("business_feeds_require_authenticated_session") is not True:
                failures.append("app_session must require authenticated business feeds")
            if expiry.get("unauthenticated_business_feed_status") != 401:
                failures.append("app_session unauthenticated business status should be 401")
            if expiry.get("client_must_clear_cached_business_state") is not True:
                failures.append("app_session must clear cached business state on expiry")
            logout = app_session.get("logout") or {}
            if logout.get("clears_server_session") is not True:
                failures.append("app_session logout must clear server session")
            if logout.get("client_must_clear_app_state") is not True:
                failures.append("app_session logout must clear app state")
            security = app_session.get("security") or {}
            for required_rule in (
                "role_visibility_enforced_server_side",
                "company_scope_enforced_server_side",
                "csrf_required_for_post",
            ):
                if security.get(required_rule) is not True:
                    failures.append(f"app_session security rule must be true: {required_rule}")
            if security.get("offline_mutations_allowed"):
                failures.append("app_session must not allow offline mutations")

            app_notifications = payload.get("app_notifications") or {}
            for key in REQUIRED_APP_NOTIFICATIONS_KEYS:
                if key not in app_notifications:
                    failures.append(f"app home app_notifications missing: {key}")
            if app_notifications.get("contract_version") != "phase3e-app-notifications-v1":
                failures.append(f"app_notifications contract_version changed: {app_notifications.get('contract_version')}")
            if app_notifications.get("source_model") != "Notification":
                failures.append("app_notifications source_model must be Notification")
            if app_notifications.get("delivery_strategy") != "in_app_feed_now_push_later":
                failures.append("app_notifications delivery strategy changed")
            if app_notifications.get("centre_url") != "/notifications/":
                failures.append(f"app_notifications centre_url changed: {app_notifications.get('centre_url')}")
            if app_notifications.get("feed_url") != "/notifications/feed.json":
                failures.append(f"app_notifications feed_url changed: {app_notifications.get('feed_url')}")
            if app_notifications.get("badge_source") != "notification_summary":
                failures.append("app_notifications badge_source must use notification_summary")
            if app_notifications.get("refresh_seconds") != 20:
                failures.append("app_notifications refresh should remain 20 seconds")
            badge_counts = app_notifications.get("badge_counts") or {}
            expected_badges = {
                "unread": summary.get("unread_notifications", 0),
                "action_required": summary.get("action_notifications", 0),
                "gar": summary.get("gar_notifications", 0),
                "high_priority": summary.get("high_priority_notifications", 0),
            }
            for key, expected_value in expected_badges.items():
                if badge_counts.get(key) != expected_value:
                    failures.append(f"app_notifications badge {key} did not match summary")
            notification_actions = app_notifications.get("actions") or []
            notification_action_keys = {item.get("key") for item in notification_actions if isinstance(item, dict)}
            for required_action in ("open_notification", "mark_read", "mark_all_read"):
                if required_action not in notification_action_keys:
                    failures.append(f"app_notifications actions missing: {required_action}")
            for action in notification_actions:
                for key in REQUIRED_APP_NOTIFICATION_ACTION_KEYS:
                    if key not in action:
                        failures.append(f"app_notifications action {action.get('key')} missing: {key}")
                if action.get("key") in {"mark_read", "mark_all_read"}:
                    if action.get("method") != "POST":
                        failures.append(f"app_notifications action {action.get('key')} must be POST")
                    if action.get("requires_csrf") is not True:
                        failures.append(f"app_notifications action {action.get('key')} must require CSRF")
                if action.get("key") == "open_notification":
                    if action.get("method") != "GET":
                        failures.append("open_notification should remain GET")
                    if action.get("marks_read") is not True:
                        failures.append("open_notification should mark notification read")
                    if action.get("safe_target_required") is not True:
                        failures.append("open_notification must require safe target")
            visibility = app_notifications.get("visibility") or {}
            for required_rule in (
                "recipient_scoped",
                "role_visibility_enforced",
                "company_scope_enforced",
                "source_references_required",
            ):
                if visibility.get(required_rule) is not True:
                    failures.append(f"app_notifications visibility rule must be true: {required_rule}")
            push_future = app_notifications.get("push_future") or {}
            if push_future.get("enabled"):
                failures.append("app_notifications push must remain disabled in Phase 3E")
            if push_future.get("requires_device_registration") is not True:
                failures.append("app_notifications future push must require device registration")
            if push_future.get("payload_must_not_include_private_business_data") is not True:
                failures.append("app_notifications push payload must avoid private business data")
            notification_gar = app_notifications.get("gar") or {}
            if notification_gar.get("source_backed_required") is not True:
                failures.append("app_notifications GAR handling must be source-backed")

            app_resilience = payload.get("app_resilience") or {}
            for key in REQUIRED_APP_RESILIENCE_KEYS:
                if key not in app_resilience:
                    failures.append(f"app home app_resilience missing: {key}")
            if app_resilience.get("contract_version") != "phase3e-app-resilience-v1":
                failures.append(f"app_resilience contract_version changed: {app_resilience.get('contract_version')}")
            offline = app_resilience.get("offline") or {}
            if offline.get("static_shell_available") is not True:
                failures.append("app_resilience offline must allow static shell")
            if offline.get("business_feeds_available"):
                failures.append("app_resilience offline must not expose business feeds")
            if offline.get("mutations_allowed"):
                failures.append("app_resilience offline must not allow mutations")
            if offline.get("display_mode") != "read_only_cached_shell":
                failures.append("app_resilience offline display mode changed")
            stale_feed = app_resilience.get("stale_feed") or {}
            if stale_feed.get("warning_seconds") != 120:
                failures.append("app_resilience stale warning should remain 120 seconds")
            if stale_feed.get("force_refetch_after_mutation") is not True:
                failures.append("app_resilience must force refetch after mutation")
            http_errors = app_resilience.get("http_errors") or {}
            expected_error_actions = {
                "unauthenticated": (401, "redirect_to_login"),
                "forbidden": (403, "show_no_access"),
                "not_found": (404, "show_record_unavailable"),
                "validation_error": (400, "keep_form_state"),
                "server_error": (500, "show_retry"),
            }
            for key, (status_code, action) in expected_error_actions.items():
                error_rule = http_errors.get(key) or {}
                if error_rule.get("status") != status_code:
                    failures.append(f"app_resilience {key} status changed")
                if error_rule.get("action") != action:
                    failures.append(f"app_resilience {key} action changed")
            if (http_errors.get("server_error") or {}).get("include_trace_to_client"):
                failures.append("app_resilience must not expose server traces to clients")
            mutation_failure = app_resilience.get("mutation_failure") or {}
            if mutation_failure.get("optimistic_updates_allowed"):
                failures.append("app_resilience must not allow optimistic updates yet")
            if mutation_failure.get("client_must_refetch_source_record") is not True:
                failures.append("app_resilience must refetch source record after mutation failure")
            gar_degraded = app_resilience.get("gar_degraded") or {}
            if gar_degraded.get("source_backed_required") is not True:
                failures.append("app_resilience GAR degraded mode must remain source-backed")
            if gar_degraded.get("model_only_fallback_allowed"):
                failures.append("app_resilience must not allow model-only GAR fallback")
            user_messages = app_resilience.get("user_messages") or {}
            if user_messages.get("plain_language") is not True:
                failures.append("app_resilience user messages should be plain language")
            if user_messages.get("no_stack_traces") is not True:
                failures.append("app_resilience user messages must hide stack traces")

            app_observability = payload.get("app_observability") or {}
            for key in REQUIRED_APP_OBSERVABILITY_KEYS:
                if key not in app_observability:
                    failures.append(f"app home app_observability missing: {key}")
            if app_observability.get("contract_version") != "phase3e-app-observability-v1":
                failures.append(
                    f"app_observability contract_version changed: {app_observability.get('contract_version')}"
                )
            diagnostics = app_observability.get("diagnostics") or {}
            if diagnostics.get("client_event_reporting_enabled"):
                failures.append("app_observability must not enable client event reporting yet")
            if diagnostics.get("server_side_logging_required") is not True:
                failures.append("app_observability must require server-side logging")
            if diagnostics.get("device_diagnostics_allowed") is not True:
                failures.append("app_observability must allow device diagnostics metadata")
            allowed_events = set(app_observability.get("allowed_client_events") or [])
            for event_key in (
                "app_bootstrap_loaded",
                "feed_refresh_failed",
                "mutation_failed",
                "session_expired",
                "gar_source_unavailable",
            ):
                if event_key not in allowed_events:
                    failures.append(f"app_observability allowed event missing: {event_key}")
            privacy = app_observability.get("privacy") or {}
            for privacy_rule in (
                "no_business_payloads_in_diagnostics",
                "no_gar_answers_in_diagnostics",
                "no_document_text_in_diagnostics",
                "no_personal_contact_details_in_diagnostics",
                "role_context_allowed",
                "contract_versions_allowed",
            ):
                if privacy.get(privacy_rule) is not True:
                    failures.append(f"app_observability privacy rule must be true: {privacy_rule}")
            performance = app_observability.get("performance") or {}
            for perf_rule in (
                "track_feed_latency_ms",
                "track_screen_load_ms",
                "track_static_shell_cache_hit",
                "track_mutation_round_trip_ms",
            ):
                if performance.get(perf_rule) is not True:
                    failures.append(f"app_observability performance rule must be true: {perf_rule}")
            if performance.get("slow_feed_warning_ms") != 3000:
                failures.append("app_observability slow feed warning should remain 3000ms")
            health = app_observability.get("health") or {}
            if health.get("uses_health_feed") is not True or health.get("health_feed_key") != "health":
                failures.append("app_observability must use the app health feed")
            if health.get("service_worker_status_required") is not True:
                failures.append("app_observability must require service worker status")
            if health.get("manifest_status_required") is not True:
                failures.append("app_observability must require manifest status")
            support = app_observability.get("support") or {}
            if support.get("include_contract_versions") is not True:
                failures.append("app_observability support must include contract versions")
            if support.get("include_role_context") is not True:
                failures.append("app_observability support must include role context")
            if support.get("include_user_id") or support.get("include_company_id"):
                failures.append("app_observability support must not include raw user/company ids")

            app_compatibility = payload.get("app_compatibility") or {}
            for key in REQUIRED_APP_COMPATIBILITY_KEYS:
                if key not in app_compatibility:
                    failures.append(f"app home app_compatibility missing: {key}")
            if app_compatibility.get("contract_version") != "phase3e-app-compatibility-v1":
                failures.append(
                    f"app_compatibility contract_version changed: {app_compatibility.get('contract_version')}"
                )
            client_support = app_compatibility.get("client_support") or {}
            supported_clients = set(client_support.get("supported_client_types") or [])
            for client_type in ("responsive_web", "installed_pwa", "future_native_app"):
                if client_type not in supported_clients:
                    failures.append(f"app_compatibility supported client missing: {client_type}")
            if client_support.get("minimum_contract_bundle") != "phase3e":
                failures.append("app_compatibility minimum bundle must remain phase3e")
            if client_support.get("incompatible_clients_blocked") is not True:
                failures.append("app_compatibility must block incompatible clients")
            feed_versions = app_compatibility.get("feed_versions") or {}
            for feed_key in ("health", "home", "capabilities", "notifications", "works", "gar"):
                if feed_versions.get(feed_key) != "v1":
                    failures.append(f"app_compatibility feed version changed or missing: {feed_key}")
            version_policy = app_compatibility.get("version_policy") or {}
            for version_rule in (
                "server_is_authority",
                "clients_must_check_health_feed",
                "clients_must_refresh_capabilities_on_version_change",
                "backwards_compatible_read_fields",
                "remove_fields_requires_new_contract",
            ):
                if version_policy.get(version_rule) is not True:
                    failures.append(f"app_compatibility version rule must be true: {version_rule}")
            feature_flags = app_compatibility.get("feature_flags") or {}
            if feature_flags.get("source") != "server_capabilities_feed":
                failures.append("app_compatibility feature flags must come from capabilities feed")
            if feature_flags.get("client_must_not_enable_unlisted_features") is not True:
                failures.append("app_compatibility must block unlisted client features")
            if feature_flags.get("role_visibility_server_enforced") is not True:
                failures.append("app_compatibility must keep role visibility server-side")
            upgrade_behaviour = app_compatibility.get("upgrade_behaviour") or {}
            for upgrade_rule in (
                "soft_refresh_on_minor_change",
                "force_reload_on_major_contract_change",
                "clear_static_shell_on_service_worker_update",
                "show_update_available_prompt",
            ):
                if upgrade_behaviour.get(upgrade_rule) is not True:
                    failures.append(f"app_compatibility upgrade rule must be true: {upgrade_rule}")
            deprecation = app_compatibility.get("deprecation") or {}
            if deprecation.get("minimum_notice_days_future") != 30:
                failures.append("app_compatibility future deprecation notice should remain 30 days")
            if deprecation.get("old_clients_get_read_only_safe_state") is not True:
                failures.append("app_compatibility must put old clients into a safe read-only state")
            compatibility_support = app_compatibility.get("support") or {}
            if compatibility_support.get("no_business_payloads") is not True:
                failures.append("app_compatibility support must avoid business payloads")

            app_sync = payload.get("app_sync") or {}
            for key in REQUIRED_APP_SYNC_KEYS:
                if key not in app_sync:
                    failures.append(f"app home app_sync missing: {key}")
            if app_sync.get("contract_version") != "phase3e-app-sync-v1":
                failures.append(f"app_sync contract_version changed: {app_sync.get('contract_version')}")
            if app_sync.get("mode") != "session_bound_polling":
                failures.append(f"app_sync mode changed: {app_sync.get('mode')}")
            read_only_feed_keys = set(app_sync.get("read_only_feed_keys") or [])
            for required_feed in ("home", "capabilities", "company_setup", "notifications", "works", "gar"):
                if required_feed not in read_only_feed_keys:
                    failures.append(f"app_sync read_only_feed_keys missing: {required_feed}")
            refresh_seconds = app_sync.get("refresh_seconds") or {}
            if refresh_seconds.get("notifications") != 20:
                failures.append("app_sync notifications refresh should remain 20 seconds")
            if refresh_seconds.get("capabilities", 0) < 300:
                failures.append("app_sync capabilities refresh should be slow-moving")
            online_required = set(app_sync.get("online_required_for") or [])
            for required_action in ("create", "route", "approve", "return", "close", "reopen", "upload_evidence", "ask_gar"):
                if required_action not in online_required:
                    failures.append(f"app_sync online_required_for missing: {required_action}")
            cache_policy = app_sync.get("cache_policy") or {}
            if not cache_policy.get("static_shell"):
                failures.append("app_sync must allow static shell cache")
            for blocked_cache in ("business_records", "gar_answers", "notification_payloads"):
                if cache_policy.get(blocked_cache):
                    failures.append(f"app_sync must not cache {blocked_cache}")
            mutation_policy = app_sync.get("mutation_policy") or {}
            if mutation_policy.get("allowed_from_feed"):
                failures.append("app_sync must not allow mutations from feeds")
            if not mutation_policy.get("requires_governed_post_route"):
                failures.append("app_sync mutations must require governed POST routes")
            if not mutation_policy.get("requires_csrf"):
                failures.append("app_sync mutations must require CSRF")
            if not mutation_policy.get("requires_record_context"):
                failures.append("app_sync mutations must require record context")
            if mutation_policy.get("client_generated_business_ids_allowed"):
                failures.append("app_sync must not allow client-generated business IDs")
            conflict_policy = app_sync.get("conflict_policy") or {}
            if not conflict_policy.get("server_record_wins"):
                failures.append("app_sync conflict policy must keep server record as source of truth")
            if not conflict_policy.get("client_must_refetch_after_mutation"):
                failures.append("app_sync must require refetch after mutation")

            app_media = payload.get("app_media") or {}
            for key in REQUIRED_APP_MEDIA_KEYS:
                if key not in app_media:
                    failures.append(f"app home app_media missing: {key}")
            if app_media.get("contract_version") != "phase3e-app-media-v1":
                failures.append(f"app_media contract_version changed: {app_media.get('contract_version')}")
            if app_media.get("source_model") != "MediaFile":
                failures.append(f"app_media source_model changed: {app_media.get('source_model')}")
            if app_media.get("direct_binary_uploads_enabled"):
                failures.append("app_media must not enable direct binary uploads yet")
            if not app_media.get("evidence_references_supported"):
                failures.append("app_media must support evidence references")
            media_contexts = app_media.get("contexts") or []
            media_context_keys = {item.get("key") for item in media_contexts if isinstance(item, dict)}
            for required_context in (
                "member_maintenance_request",
                "contractor_completion_evidence",
                "member_work_order_feedback",
                "member_reopen_request",
            ):
                if required_context not in media_context_keys:
                    failures.append(f"app_media contexts missing: {required_context}")
            for context in media_contexts:
                for key in REQUIRED_APP_MEDIA_CONTEXT_KEYS:
                    if key not in context:
                        failures.append(f"app_media context {context.get('key')} missing: {key}")
                if not context.get("required_context_fields"):
                    failures.append(f"app_media context {context.get('key')} is missing required context fields")
            media_guardrails = app_media.get("guardrails") or {}
            for required_guardrail in (
                "requires_authenticated_session",
                "requires_csrf_for_mutation",
                "requires_record_context",
                "server_generated_media_ids",
                "virus_scan_required_before_visibility",
                "role_visibility_required",
            ):
                if media_guardrails.get(required_guardrail) is not True:
                    failures.append(f"app_media guardrail must be true: {required_guardrail}")
            if media_guardrails.get("offline_upload_queue_allowed"):
                failures.append("app_media must not allow offline upload queueing")
            if media_guardrails.get("client_generated_business_ids_allowed"):
                failures.append("app_media must not allow client-generated business IDs")
            media_gar = app_media.get("gar_processing") or {}
            if not media_gar.get("enabled_after_source_record"):
                failures.append("app_media GAR processing must wait for a source record")
            if not media_gar.get("source_backed_required"):
                failures.append("app_media GAR processing must remain source-backed")

            modules = payload.get("modules") or []
            module_keys = {item.get("key") for item in modules if isinstance(item, dict)}
            for required_module in ("dashboard", "notifications", "gar", "works"):
                if required_module not in module_keys:
                    failures.append(f"app home modules missing: {required_module}")
            for module in modules:
                for key in REQUIRED_MODULE_KEYS:
                    if key not in module:
                        failures.append(f"app home module {module.get('key')} missing: {key}")

            quick_actions = payload.get("quick_actions") or []
            quick_action_keys = {item.get("key") for item in quick_actions if isinstance(item, dict)}
            for required_action in ("view_notifications", "open_works", "ask_gar"):
                if required_action not in quick_action_keys:
                    failures.append(f"app home quick_actions missing: {required_action}")
            for action in quick_actions:
                for key in REQUIRED_QUICK_ACTION_KEYS:
                    if key not in action:
                        failures.append(f"app home quick action {action.get('key')} missing: {key}")
                if not action.get("governed"):
                    failures.append(f"app home quick action {action.get('key')} is not marked governed")
                if not action.get("owning_module"):
                    failures.append(f"app home quick action {action.get('key')} is missing owning_module")
                if action.get("requires_online") is not True:
                    failures.append(f"app home quick action {action.get('key')} must require online use")
                if action.get("offline_queue_allowed"):
                    failures.append(f"app home quick action {action.get('key')} must not allow offline queueing")
                if action.get("server_authoritative") is not True:
                    failures.append(f"app home quick action {action.get('key')} must be server authoritative")
                if action.get("method") == "POST":
                    if not action.get("requires_csrf"):
                        failures.append(f"POST quick action {action.get('key')} is not CSRF marked")
                    if not action.get("requires_context"):
                        failures.append(f"POST quick action {action.get('key')} should require context")
                    if not action.get("confirmation_required"):
                        failures.append(f"POST quick action {action.get('key')} should require confirmation")
                    if not action.get("required_context_fields"):
                        failures.append(f"POST quick action {action.get('key')} is missing required_context_fields")
                else:
                    if action.get("confirmation_required"):
                        failures.append(f"GET quick action {action.get('key')} should not require confirmation")

            quick_actions_by_key = {item.get("key"): item for item in quick_actions if isinstance(item, dict)}
            submit_completion = quick_actions_by_key.get("submit_completion")
            if submit_completion:
                if submit_completion.get("owning_module") != "contractor_logix":
                    failures.append("submit_completion should belong to Contractor Logix")
                for field in ("work_order_id", "action", "completion_note"):
                    if field not in (submit_completion.get("required_context_fields") or []):
                        failures.append(f"submit_completion missing context field: {field}")
                if not submit_completion.get("evidence_reference_supported"):
                    failures.append("submit_completion should support evidence references")

            contractor_actions = {
                item.get("key"): item
                for item in (role_payloads.get("Contractor", {}).get("quick_actions") or [])
                if isinstance(item, dict)
            }
            submit_completion = contractor_actions.get("submit_completion")
            if not submit_completion:
                failures.append("Contractor app home quick_actions missing: submit_completion")
            else:
                if submit_completion.get("method") != "POST":
                    failures.append("submit_completion should be POST")
                if submit_completion.get("owning_module") != "contractor_logix":
                    failures.append("submit_completion should belong to Contractor Logix")
                if not submit_completion.get("requires_context"):
                    failures.append("submit_completion should require work-order context")
                for field in ("work_order_id", "action", "completion_note"):
                    if field not in (submit_completion.get("required_context_fields") or []):
                        failures.append(f"submit_completion missing context field: {field}")
                if not submit_completion.get("evidence_reference_supported"):
                    failures.append("submit_completion should support evidence references")

            member_actions = {
                item.get("key"): item
                for item in (role_payloads.get("Member", {}).get("quick_actions") or [])
                if isinstance(item, dict)
            }
            for action_key, required_fields in {
                "new_request": ("unit_id", "title", "description"),
                "request_reopen": ("work_order_id", "reason"),
            }.items():
                member_action = member_actions.get(action_key)
                if not member_action:
                    failures.append(f"Member app home quick_actions missing: {action_key}")
                    continue
                if member_action.get("owning_module") != "members_logix":
                    failures.append(f"{action_key} should belong to Members Logix")
                if member_action.get("method") != "POST":
                    failures.append(f"{action_key} should be POST")
                if not member_action.get("requires_context"):
                    failures.append(f"{action_key} should require record context")
                for field in required_fields:
                    if field not in (member_action.get("required_context_fields") or []):
                        failures.append(f"{action_key} missing context field: {field}")
                if not member_action.get("evidence_reference_supported"):
                    failures.append(f"{action_key} should support evidence references")

            app_policy = payload.get("app_policy") or {}
            for key in REQUIRED_POLICY_SECTIONS:
                if key not in app_policy:
                    failures.append(f"app home app_policy missing: {key}")
            if app_policy.get("contract_version") != "phase3e-app-home-v1":
                failures.append(f"app policy contract_version changed: {app_policy.get('contract_version')}")

            auth_policy = app_policy.get("auth") or {}
            if not auth_policy.get("requires_authenticated_session"):
                failures.append("app policy must require an authenticated session")
            if not auth_policy.get("csrf_required_for_mutations"):
                failures.append("app policy must require CSRF for mutations")
            if not auth_policy.get("role_visibility_enforced_server_side"):
                failures.append("app policy must enforce role visibility server-side")

            offline_policy = app_policy.get("offline") or {}
            if not offline_policy.get("static_shell_cache_only"):
                failures.append("app policy must keep offline caching to the static shell only")
            if offline_policy.get("business_records_cached"):
                failures.append("app policy must not cache business records offline")
            if offline_policy.get("offline_mutations_supported"):
                failures.append("app policy must not support offline mutations yet")

            sync_policy = app_policy.get("sync") or {}
            if not sync_policy.get("feeds_are_read_only"):
                failures.append("app policy must declare feeds as read-only")
            if not sync_policy.get("mutations_use_governed_post_routes"):
                failures.append("app policy must route mutations through governed POST routes")

            media_policy = app_policy.get("media") or {}
            if media_policy.get("direct_binary_uploads_enabled"):
                failures.append("app policy should not expose direct binary uploads yet")
            if not media_policy.get("evidence_references_supported"):
                failures.append("app policy should support evidence references")

            gar_policy = app_policy.get("gar") or {}
            if not gar_policy.get("source_backed_required"):
                failures.append("app policy must require source-backed GAR")
            if not gar_policy.get("role_aware"):
                failures.append("app policy must mark GAR as role-aware")

            priority_actions = payload.get("priority_actions") or []
            if not priority_actions:
                failures.append("app home priority_actions did not include seeded action")
            elif not priority_actions[0].get("source_reference"):
                failures.append("app home priority action lost source_reference")

            sources = payload.get("source_references") or []
            if not any(source.get("model") == "User" and source.get("record_id") == user.id for source in sources):
                failures.append("app home source_references missing signed-in User")
            if not any(source.get("model") == "Notification" for source in sources):
                failures.append("app home source_references missing Notification queue")

        finally:
            db.session.rollback()
            _delete_by_ids(Notification, ids["notifications"])
            _delete_by_ids(User, ids["users"])
            _delete_by_ids(Company, ids["companies"])
            if created_role_ids:
                Role.query.filter(Role.id.in_(created_role_ids)).delete(synchronize_session=False)
            db.session.commit()

    print("App home feed contract check")
    print("- Route checked: /app/home/feed.json")
    print(f"- Payload keys checked: {len(REQUIRED_TOP_LEVEL_KEYS)}")
    print("- App scope contract checked: role, company and source boundaries")
    print("- Role-aware module registry checked: yes")
    print("- App navigation contract checked: bottom tabs and badges")
    print("- App deep-link contract checked: safe role-aware targets")
    print("- App session contract checked: auth, CSRF, device and logout")
    print("- App notifications contract checked: badges, actions and push readiness")
    print("- App resilience contract checked: offline, stale, error and GAR states")
    print("- App observability contract checked: privacy-safe diagnostics")
    print("- App compatibility contract checked: client versions and feature gates")
    print("- App sync contract checked: refresh, cache, mutation and conflict policy")
    print("- App media contract checked: source, evidence and GAR processing")
    print("- Governed quick actions checked: yes")
    print("- App policy checked: auth, offline, sync, media, GAR")
    print("- Notification and source references checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
