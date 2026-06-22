"""Verify the app capabilities feed remains a safe app/PWA contract."""

from __future__ import annotations

from datetime import UTC, datetime
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


REQUIRED_TOP_LEVEL_KEYS = (
    "context_type",
    "contract_version",
    "user",
    "app_policy",
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
    "quick_actions",
    "modules",
    "gar",
    "readiness",
    "source_references",
)

REQUIRED_MODULE_KEYS = (
    "key",
    "name",
    "status",
    "dashboard_endpoint",
    "dashboard_url",
    "owned_data",
    "shared_links",
    "app_ready",
    "source_of_truth",
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


def main() -> int:
    from app import create_app
    from app.extensions import db
    from app.models.core.role import Role
    from app.models.core.user import User
    from app.models.onboarding.company import Company

    app = create_app()
    failures: list[str] = []
    marker = f"APPCAP{datetime.now(UTC).strftime('%y%m%d%H%M%S')}"
    ids: dict[str, list[int]] = {"companies": [], "users": []}
    created_role_ids: list[int] = []

    rule = next((item for item in app.url_map.iter_rules() if item.endpoint == "app_home.capabilities_feed"), None)
    if not rule:
        failures.append("Missing app_home.capabilities_feed route")
    else:
        if rule.rule != "/app/capabilities/feed.json":
            failures.append(f"app_home.capabilities_feed route changed to {rule.rule}")
        if "GET" not in (rule.methods or set()):
            failures.append("app_home.capabilities_feed does not allow GET")
        if {"POST", "PUT", "PATCH", "DELETE"}.intersection(rule.methods or set()):
            failures.append("app_home.capabilities_feed allows a mutating method")

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
        Company.query.filter(Company.subdomain.ilike("appcap%")).delete(synchronize_session=False)
        User.query.filter(User.username.ilike("appcap%")).delete(synchronize_session=False)
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
            db.session.commit()

            with app.test_client() as client:
                _sign_in(client, user)
                response = client.get("/app/capabilities/feed.json")
                if response.status_code != 200:
                    failures.append(f"/app/capabilities/feed.json returned HTTP {response.status_code}")
                payload = response.get_json(silent=True) or {}

            for key in REQUIRED_TOP_LEVEL_KEYS:
                if key not in payload:
                    failures.append(f"app capabilities payload missing: {key}")
            if payload.get("context_type") != "app_capabilities":
                failures.append(f"Unexpected context_type: {payload.get('context_type')}")
            if payload.get("contract_version") != "phase3e-app-capabilities-v1":
                failures.append(f"Unexpected contract_version: {payload.get('contract_version')}")

            feeds = payload.get("feeds") or {}
            if feeds.get("home") != "/app/home/feed.json":
                failures.append("capabilities feed lost home feed link")
            if feeds.get("capabilities") != "/app/capabilities/feed.json":
                failures.append("capabilities feed lost self link")

            policy = payload.get("app_policy") or {}
            if not (policy.get("offline") or {}).get("static_shell_cache_only"):
                failures.append("capabilities feed lost static-shell-only offline policy")
            if not (policy.get("sync") or {}).get("feeds_are_read_only"):
                failures.append("capabilities feed lost read-only feed policy")
            if not (policy.get("gar") or {}).get("source_backed_required"):
                failures.append("capabilities feed lost source-backed GAR policy")

            app_scope = payload.get("app_scope") or {}
            for key in REQUIRED_APP_SCOPE_KEYS:
                if key not in app_scope:
                    failures.append(f"capabilities app_scope missing: {key}")
            if app_scope.get("contract_version") != "phase3e-app-scope-v1":
                failures.append(f"capabilities app_scope contract_version changed: {app_scope.get('contract_version')}")
            if app_scope.get("data_boundary") != "company":
                failures.append(f"capabilities app_scope data_boundary changed: {app_scope.get('data_boundary')}")
            if app_scope.get("role_context") != "super_admin":
                failures.append(f"capabilities app_scope role_context changed: {app_scope.get('role_context')}")
            client_compartment = app_scope.get("client_compartment") or {}
            if not client_compartment.get("server_side_filters_required"):
                failures.append("capabilities app_scope lost server-side filter requirement")
            gar_visibility = app_scope.get("gar_visibility") or {}
            if not gar_visibility.get("source_backed_required") or gar_visibility.get("model_only_answers_allowed"):
                failures.append("capabilities app_scope lost source-backed GAR visibility rule")

            app_navigation = payload.get("app_navigation") or {}
            for key in REQUIRED_APP_NAVIGATION_KEYS:
                if key not in app_navigation:
                    failures.append(f"capabilities app_navigation missing: {key}")
            if app_navigation.get("style") != "bottom_tabs":
                failures.append(f"capabilities app_navigation style changed: {app_navigation.get('style')}")
            primary_items = app_navigation.get("primary_items") or []
            if len(primary_items) < 3:
                failures.append("capabilities app_navigation has too few primary items")
            primary_item_keys = {item.get("key") for item in primary_items if isinstance(item, dict)}
            for required_item in ("home", "notifications", "gar"):
                if required_item not in primary_item_keys:
                    failures.append(f"capabilities app_navigation primary_items missing: {required_item}")
            for item in primary_items + (app_navigation.get("secondary_items") or []):
                for key in REQUIRED_APP_NAV_ITEM_KEYS:
                    if key not in item:
                        failures.append(f"capabilities app_navigation item {item.get('key')} missing: {key}")

            app_surfaces = payload.get("app_surfaces") or {}
            for key in REQUIRED_APP_SURFACES_KEYS:
                if key not in app_surfaces:
                    failures.append(f"capabilities app_surfaces missing: {key}")
            if app_surfaces.get("contract_version") != "phase3e-app-surfaces-v1":
                failures.append(f"capabilities app_surfaces contract_version changed: {app_surfaces.get('contract_version')}")
            surface_items = app_surfaces.get("items") or []
            surface_keys = {item.get("key") for item in surface_items if isinstance(item, dict)}
            for required_surface in ("dashboard", "notifications", "gar", "capabilities"):
                if required_surface not in surface_keys:
                    failures.append(f"capabilities app_surfaces items missing: {required_surface}")
            for item in surface_items:
                for key in REQUIRED_APP_SURFACE_ITEM_KEYS:
                    if key not in item:
                        failures.append(f"capabilities app_surfaces item {item.get('key')} missing: {key}")
                if item.get("safe_area_required") is not True:
                    failures.append(f"capabilities app_surfaces item {item.get('key')} lost safe-area rule")
                if item.get("supports_pull_to_refresh") is not True:
                    failures.append(f"capabilities app_surfaces item {item.get('key')} lost pull-to-refresh rule")
                if item.get("source_backed") is not True:
                    failures.append(f"capabilities app_surfaces item {item.get('key')} is not source-backed")

            app_deep_links = payload.get("app_deep_links") or {}
            for key in REQUIRED_APP_DEEP_LINK_KEYS:
                if key not in app_deep_links:
                    failures.append(f"capabilities app_deep_links missing: {key}")
            if app_deep_links.get("contract_version") != "phase3e-app-deep-links-v1":
                failures.append(f"capabilities app_deep_links contract_version changed: {app_deep_links.get('contract_version')}")
            if "relative_path" not in (app_deep_links.get("allowed_schemes") or []):
                failures.append("capabilities app_deep_links must allow relative_path links")
            blocked_schemes = set(app_deep_links.get("blocked_schemes") or [])
            for blocked_scheme in ("javascript", "data", "file", "external_without_allowlist"):
                if blocked_scheme not in blocked_schemes:
                    failures.append(f"capabilities app_deep_links blocked_schemes missing: {blocked_scheme}")
            route_resolution = app_deep_links.get("route_resolution") or {}
            if not route_resolution.get("server_url_for_is_source"):
                failures.append("capabilities app_deep_links must use server url_for as source")
            if not route_resolution.get("client_must_not_guess_record_urls"):
                failures.append("capabilities app_deep_links must block client-guessed record URLs")
            notification_rules = app_deep_links.get("notification_target_rules") or {}
            if not notification_rules.get("source_reference_required"):
                failures.append("capabilities app_deep_links must require notification source references")
            if not notification_rules.get("mark_read_requires_post"):
                failures.append("capabilities app_deep_links must keep mark-read as POST")
            deep_link_items = app_deep_links.get("items") or []
            deep_link_keys = {item.get("key") for item in deep_link_items if isinstance(item, dict)}
            for required_link in ("open_dashboard", "open_notifications", "open_gar", "open_capabilities"):
                if required_link not in deep_link_keys:
                    failures.append(f"capabilities app_deep_links items missing: {required_link}")
            for item in deep_link_items:
                for key in REQUIRED_APP_DEEP_LINK_ITEM_KEYS:
                    if key not in item:
                        failures.append(f"capabilities app_deep_links item {item.get('key')} missing: {key}")
                if item.get("requires_role_check") is not True:
                    failures.append(f"capabilities app_deep_links item {item.get('key')} must require role checks")
                if item.get("source_backed") is not True:
                    failures.append(f"capabilities app_deep_links item {item.get('key')} must be source-backed")

            app_session = payload.get("app_session") or {}
            for key in REQUIRED_APP_SESSION_KEYS:
                if key not in app_session:
                    failures.append(f"capabilities app_session missing: {key}")
            if app_session.get("contract_version") != "phase3e-app-session-v1":
                failures.append(f"capabilities app_session contract_version changed: {app_session.get('contract_version')}")
            if app_session.get("mode") != "server_session_cookie":
                failures.append("capabilities app_session must use server session cookie mode")
            if app_session.get("authenticated") is not True:
                failures.append("capabilities app_session must echo authenticated state")
            csrf = app_session.get("csrf") or {}
            if not csrf.get("required_for_mutations"):
                failures.append("capabilities app_session must require CSRF for mutations")
            if csrf.get("header_name") != "X-CSRFToken":
                failures.append("capabilities app_session CSRF header changed")
            device = app_session.get("device") or {}
            if not device.get("device_id_is_not_authentication"):
                failures.append("capabilities app_session device id must not authenticate users")
            expiry = app_session.get("expiry_handling") or {}
            if not expiry.get("client_must_redirect_to_login"):
                failures.append("capabilities app_session must redirect to login on expiry")
            if not expiry.get("client_must_clear_cached_business_state"):
                failures.append("capabilities app_session must clear business state on expiry")
            security = app_session.get("security") or {}
            if not security.get("role_visibility_enforced_server_side"):
                failures.append("capabilities app_session must enforce role visibility server-side")
            if security.get("offline_mutations_allowed"):
                failures.append("capabilities app_session must not allow offline mutations")

            app_notifications = payload.get("app_notifications") or {}
            for key in REQUIRED_APP_NOTIFICATIONS_KEYS:
                if key not in app_notifications:
                    failures.append(f"capabilities app_notifications missing: {key}")
            if app_notifications.get("contract_version") != "phase3e-app-notifications-v1":
                failures.append(f"capabilities app_notifications contract_version changed: {app_notifications.get('contract_version')}")
            if app_notifications.get("source_model") != "Notification":
                failures.append("capabilities app_notifications source_model must be Notification")
            if app_notifications.get("delivery_strategy") != "in_app_feed_now_push_later":
                failures.append("capabilities app_notifications delivery strategy changed")
            if app_notifications.get("feed_url") != "/notifications/feed.json":
                failures.append("capabilities app_notifications feed_url changed")
            if app_notifications.get("badge_source") != "notification_summary":
                failures.append("capabilities app_notifications badge source changed")
            notification_action_keys = {
                item.get("key")
                for item in (app_notifications.get("actions") or [])
                if isinstance(item, dict)
            }
            for required_action in ("open_notification", "mark_read", "mark_all_read"):
                if required_action not in notification_action_keys:
                    failures.append(f"capabilities app_notifications actions missing: {required_action}")
            visibility = app_notifications.get("visibility") or {}
            if not visibility.get("recipient_scoped"):
                failures.append("capabilities app_notifications must remain recipient-scoped")
            if not visibility.get("source_references_required"):
                failures.append("capabilities app_notifications must require source references")
            push_future = app_notifications.get("push_future") or {}
            if push_future.get("enabled"):
                failures.append("capabilities app_notifications push must remain disabled in Phase 3E")
            if not push_future.get("uses_app_session_device_contract"):
                failures.append("capabilities app_notifications push must use app session device contract")
            notification_gar = app_notifications.get("gar") or {}
            if not notification_gar.get("source_backed_required"):
                failures.append("capabilities app_notifications GAR handling must be source-backed")

            app_resilience = payload.get("app_resilience") or {}
            for key in REQUIRED_APP_RESILIENCE_KEYS:
                if key not in app_resilience:
                    failures.append(f"capabilities app_resilience missing: {key}")
            if app_resilience.get("contract_version") != "phase3e-app-resilience-v1":
                failures.append(f"capabilities app_resilience contract_version changed: {app_resilience.get('contract_version')}")
            offline = app_resilience.get("offline") or {}
            if not offline.get("static_shell_available"):
                failures.append("capabilities app_resilience offline must allow static shell")
            if offline.get("business_feeds_available"):
                failures.append("capabilities app_resilience offline must not expose business feeds")
            if offline.get("mutations_allowed"):
                failures.append("capabilities app_resilience offline must not allow mutations")
            stale_feed = app_resilience.get("stale_feed") or {}
            if stale_feed.get("warning_seconds") != 120:
                failures.append("capabilities app_resilience stale warning changed")
            http_errors = app_resilience.get("http_errors") or {}
            if (http_errors.get("unauthenticated") or {}).get("action") != "redirect_to_login":
                failures.append("capabilities app_resilience unauthenticated action changed")
            if (http_errors.get("server_error") or {}).get("include_trace_to_client"):
                failures.append("capabilities app_resilience must not expose server traces")
            mutation_failure = app_resilience.get("mutation_failure") or {}
            if mutation_failure.get("optimistic_updates_allowed"):
                failures.append("capabilities app_resilience must not allow optimistic updates")
            gar_degraded = app_resilience.get("gar_degraded") or {}
            if gar_degraded.get("model_only_fallback_allowed"):
                failures.append("capabilities app_resilience must not allow model-only GAR fallback")
            user_messages = app_resilience.get("user_messages") or {}
            if not user_messages.get("plain_language") or not user_messages.get("no_stack_traces"):
                failures.append("capabilities app_resilience user messages must be plain and hide stack traces")

            app_observability = payload.get("app_observability") or {}
            for key in REQUIRED_APP_OBSERVABILITY_KEYS:
                if key not in app_observability:
                    failures.append(f"capabilities app_observability missing: {key}")
            if app_observability.get("contract_version") != "phase3e-app-observability-v1":
                failures.append(
                    "capabilities app_observability contract_version changed: "
                    f"{app_observability.get('contract_version')}"
                )
            diagnostics = app_observability.get("diagnostics") or {}
            if diagnostics.get("client_event_reporting_enabled"):
                failures.append("capabilities app_observability must not enable client event reporting yet")
            if not diagnostics.get("server_side_logging_required"):
                failures.append("capabilities app_observability must require server-side logging")
            privacy = app_observability.get("privacy") or {}
            for privacy_rule in (
                "no_business_payloads_in_diagnostics",
                "no_gar_answers_in_diagnostics",
                "no_document_text_in_diagnostics",
                "no_personal_contact_details_in_diagnostics",
            ):
                if privacy.get(privacy_rule) is not True:
                    failures.append(f"capabilities app_observability privacy rule missing: {privacy_rule}")
            performance = app_observability.get("performance") or {}
            if performance.get("slow_feed_warning_ms") != 3000:
                failures.append("capabilities app_observability slow feed warning changed")
            if not performance.get("track_feed_latency_ms") or not performance.get("track_screen_load_ms"):
                failures.append("capabilities app_observability must track feed and screen timings")
            health = app_observability.get("health") or {}
            if health.get("uses_health_feed") is not True:
                failures.append("capabilities app_observability must use health feed")
            support = app_observability.get("support") or {}
            if support.get("include_user_id") or support.get("include_company_id"):
                failures.append("capabilities app_observability must not expose raw user/company ids")

            app_compatibility = payload.get("app_compatibility") or {}
            for key in REQUIRED_APP_COMPATIBILITY_KEYS:
                if key not in app_compatibility:
                    failures.append(f"capabilities app_compatibility missing: {key}")
            if app_compatibility.get("contract_version") != "phase3e-app-compatibility-v1":
                failures.append(
                    "capabilities app_compatibility contract_version changed: "
                    f"{app_compatibility.get('contract_version')}"
                )
            client_support = app_compatibility.get("client_support") or {}
            if client_support.get("current_contract_bundle") != "phase3e":
                failures.append("capabilities app_compatibility current bundle changed")
            if client_support.get("incompatible_clients_blocked") is not True:
                failures.append("capabilities app_compatibility must block incompatible clients")
            feed_versions = app_compatibility.get("feed_versions") or {}
            if feed_versions.get("home") != "v1" or feed_versions.get("capabilities") != "v1":
                failures.append("capabilities app_compatibility feed versions changed")
            version_policy = app_compatibility.get("version_policy") or {}
            if version_policy.get("server_is_authority") is not True:
                failures.append("capabilities app_compatibility must keep server as authority")
            if version_policy.get("clients_must_refresh_capabilities_on_version_change") is not True:
                failures.append("capabilities app_compatibility must refresh capabilities on version change")
            feature_flags = app_compatibility.get("feature_flags") or {}
            if feature_flags.get("source") != "server_capabilities_feed":
                failures.append("capabilities app_compatibility feature flags must come from this feed")
            if feature_flags.get("client_must_not_enable_unlisted_features") is not True:
                failures.append("capabilities app_compatibility must block unlisted features")
            upgrade_behaviour = app_compatibility.get("upgrade_behaviour") or {}
            if upgrade_behaviour.get("force_reload_on_major_contract_change") is not True:
                failures.append("capabilities app_compatibility must force reload on major contract changes")
            deprecation = app_compatibility.get("deprecation") or {}
            if deprecation.get("old_clients_get_read_only_safe_state") is not True:
                failures.append("capabilities app_compatibility must keep old clients read-only")

            app_sync = payload.get("app_sync") or {}
            for key in REQUIRED_APP_SYNC_KEYS:
                if key not in app_sync:
                    failures.append(f"capabilities app_sync missing: {key}")
            if app_sync.get("contract_version") != "phase3e-app-sync-v1":
                failures.append(f"capabilities app_sync contract_version changed: {app_sync.get('contract_version')}")
            cache_policy = app_sync.get("cache_policy") or {}
            if cache_policy.get("business_records") or cache_policy.get("gar_answers"):
                failures.append("capabilities app_sync must not cache business records or GAR answers")
            mutation_policy = app_sync.get("mutation_policy") or {}
            if mutation_policy.get("allowed_from_feed"):
                failures.append("capabilities app_sync must not allow feed mutations")
            if not mutation_policy.get("requires_governed_post_route"):
                failures.append("capabilities app_sync lost governed POST requirement")

            app_media = payload.get("app_media") or {}
            for key in REQUIRED_APP_MEDIA_KEYS:
                if key not in app_media:
                    failures.append(f"capabilities app_media missing: {key}")
            if app_media.get("contract_version") != "phase3e-app-media-v1":
                failures.append(f"capabilities app_media contract_version changed: {app_media.get('contract_version')}")
            if app_media.get("source_model") != "MediaFile":
                failures.append("capabilities app_media lost MediaFile source model")
            if app_media.get("direct_binary_uploads_enabled"):
                failures.append("capabilities app_media must not enable direct binary uploads yet")
            media_context_keys = {
                item.get("key")
                for item in (app_media.get("contexts") or [])
                if isinstance(item, dict)
            }
            for required_context in (
                "member_maintenance_request",
                "contractor_completion_evidence",
                "member_work_order_feedback",
                "member_reopen_request",
            ):
                if required_context not in media_context_keys:
                    failures.append(f"capabilities app_media contexts missing: {required_context}")
            media_guardrails = app_media.get("guardrails") or {}
            if media_guardrails.get("offline_upload_queue_allowed"):
                failures.append("capabilities app_media must not allow offline upload queueing")
            if not media_guardrails.get("virus_scan_required_before_visibility"):
                failures.append("capabilities app_media must require virus scan before visibility")
            media_gar = app_media.get("gar_processing") or {}
            if not media_gar.get("source_backed_required"):
                failures.append("capabilities app_media GAR processing must remain source-backed")

            modules = payload.get("modules") or []
            module_keys = {module.get("key") for module in modules if isinstance(module, dict)}
            for required_module in ("core", "works", "members", "contractor", "gar_ai"):
                if required_module not in module_keys:
                    failures.append(f"capabilities modules missing: {required_module}")
            for module in modules:
                for key in REQUIRED_MODULE_KEYS:
                    if key not in module:
                        failures.append(f"capabilities module {module.get('key')} missing: {key}")
                if not module.get("source_of_truth"):
                    failures.append(f"capabilities module {module.get('key')} is not marked source_of_truth")

            gar = payload.get("gar") or {}
            if gar.get("context_type") != "gar_capability_registry":
                failures.append("capabilities feed did not include GAR capability registry")
            if not (gar.get("capabilities") or []):
                failures.append("GAR capability registry is empty")
            if gar.get("role_context") != "super_admin":
                failures.append(f"GAR capability role_context changed: {gar.get('role_context')}")

            readiness = payload.get("readiness") or {}
            if readiness.get("module_count", 0) < 10:
                failures.append("capabilities readiness module_count is unexpectedly low")
            if not readiness.get("read_only_feeds"):
                failures.append("capabilities readiness lost read_only_feeds flag")
            if not readiness.get("governed_mutations"):
                failures.append("capabilities readiness lost governed_mutations flag")

            sources = payload.get("source_references") or []
            if not any(source.get("model") == "ModuleContract" for source in sources):
                failures.append("capabilities source_references missing ModuleContract")
            if not any(source.get("model") == "GarCapability" for source in sources):
                failures.append("capabilities source_references missing GarCapability")

        finally:
            db.session.rollback()
            _delete_by_ids(User, ids["users"])
            _delete_by_ids(Company, ids["companies"])
            if created_role_ids:
                Role.query.filter(Role.id.in_(created_role_ids)).delete(synchronize_session=False)
            db.session.commit()

    print("App capabilities feed contract check")
    print("- Route checked: /app/capabilities/feed.json")
    print("- Module registry checked: yes")
    print("- GAR capability registry checked: yes")
    print("- App scope contract checked: yes")
    print("- App navigation contract checked: yes")
    print("- App surfaces contract checked: yes")
    print("- App deep-link contract checked: yes")
    print("- App session contract checked: yes")
    print("- App notifications contract checked: yes")
    print("- App resilience contract checked: yes")
    print("- App observability contract checked: yes")
    print("- App compatibility contract checked: yes")
    print("- App sync contract checked: yes")
    print("- App media contract checked: yes")
    print("- App policy and source references checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
