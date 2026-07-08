"""Validate the Phase 3 operating manual covers the cross-module workflow."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANUAL_DIR = PROJECT_ROOT / "docs" / "manual"


REQUIRED_SECTIONS = {
    "works_logix.md": (
        "Members Logix requests",
        "Contractor Logix job queues",
        "member/resident feedback",
        "reopen requests",
        "assistant_manager_cover",
        "Evidence and Audit Pack",
        "GAR Relevant History",
        "GAR does not close, reopen or return work orders by itself",
    ),
    "members_logix.md": (
        "mobile-first and app-ready",
        "submit a maintenance request",
        "provide feedback",
        "request a reopen",
        "evidence_reference",
        "GAR must not answer from company-wide Works Logix records",
    ),
    "contractor_logix.md": (
        "mobile-first and app-ready",
        "accept assigned work",
        "submit completion notes",
        "resubmit returned completion work",
        "standalone job dockets",
        "Materials Used & Time Log",
        "visible only to the contracting company",
        "GAR must not use the management Works command centre",
        "GAR Relevant History on Jobs",
    ),
    "assistant_workspace.md": (
        "company-wide cover mode",
        "assistant_manager_cover",
        "urgent work does not stop",
        "route work orders",
        "Cover notifications",
        "GAR AI for operational context",
    ),
    "finance_logix.md": (
        "foundation_present_not_query_ready",
        "Tell me the debtors in Matthew Lavery",
        "validated, role-gated query services",
        "Finance Logix should own ledgers",
    ),
    "gar_ai.md": (
        "not a basic chatbot",
        "source-backed",
        "allow_model_only_answer",
        "Finance Logix questions",
        "role-aware",
        "Contractor and Members Logix dashboards now include Ask GAR panels too",
    ),
    "notifications.md": (
        "action queue",
        "workflow stage",
        "works_quality_review",
        "recipient-scoped",
        "Role Visibility Matrix",
        "Finance users",
        "notification_role_visibility_contract_check.py",
        "GAR should not expose another user's notifications",
    ),
    "app_mobile_readiness.md": (
        "same database",
        "read-only display contracts",
        "governed POST routes",
        "/app/health/feed.json",
        "lightweight bootstrap check",
        "app_health_feed_contract_check.py",
        "phase3e_app_readiness_check.py",
        "app/mobile close-out suite",
        "/app/home/feed.json",
        "service worker caches static shell files only",
        "GAR app surfaces must be role-aware and source-backed",
        "app_shell_readiness_check.py",
        "app_mobile_surface_check.py",
        "app_home_feed_contract_check.py",
        "role-aware quick actions",
        "owning module",
        "required context fields",
        "evidence-reference support",
        "must never be queued offline",
        "POST actions are metadata only",
        "app_policy",
        "/app/capabilities/feed.json",
        "app_capabilities_feed_contract_check.py",
        "module contracts",
        "offline caching to the static shell only",
        "GAR source-backed and role-aware",
        "Members Logix, Contractor Logix and Notifications",
        "app_scope",
        "signed-in user's data boundary contract",
        "Management roles operate inside their company/client portfolio",
        "contractors operate inside assigned Contractor Logix work",
        "members/residents operate inside linked member units",
        "app_navigation",
        "bottom-tab contract",
        "badge counts",
        "app_surfaces",
        "role-aware screen registry",
        "safe-area requirement",
        "pull-to-refresh support",
        "source-backed surfaces",
        "app_deep_links",
        "safe app routing contract",
        "relative-path links",
        "Unsafe schemes",
        "Notification targets",
        "mark-read actions on governed POST routes",
        "app_session",
        "app session contract",
        "server-session cookie authentication",
        "CSRF handling",
        "device identity",
        "clear cached business state",
        "app_notifications",
        "app notification contract",
        "in-app notification feed delivery now and push later",
        "Badge counts",
        "recipient-scoped",
        "POST-only CSRF-protected actions",
        "app_resilience",
        "app resilience contract",
        "offline display",
        "stale feed warnings",
        "HTTP error handling",
        "mutation failure",
        "GAR degraded mode",
        "server stack traces must never be shown",
        "app_observability",
        "privacy-safe diagnostics",
        "business payloads",
        "GAR answers",
        "document text",
        "personal contact details",
        "feed latency",
        "support references",
        "app_compatibility",
        "app compatibility and version governance contract",
        "responsive web",
        "installed PWA",
        "future native app clients",
        "health feed",
        "contract versions change",
        "read-only safe state",
        "server capabilities feed",
        "Mobile Surface UX Contract",
        "data-app-mobile-ready",
        "data-app-source-backed",
        "static-shell-only",
        "safe-area support",
        "touch-friendly app navigation",
        "UX quality gate",
        "App Action UX Contract",
        "Mobile actions",
        "online-only",
        "source-record governed",
        "data-app-action",
        "requires CSRF",
        "disables offline queueing",
        "server record remaining authoritative",
        "Evidence Reference Handoff",
        "secure reference fields",
        "data-app-media-reference",
        "data-app-media-context",
        "data-app-media-source-model",
        "data-app-direct-upload",
        "full upload storage",
        "governed source record and audit trail",
        "How To Use On Mobile",
        "same authenticated LogixPM session",
        "Members Works",
        "track live work orders",
        "Contractor Work Queue",
        "submit completion notes",
        "Management users",
        "Notification Centre",
        "Works Command Centre",
        "Mobile notifications",
        "GAR on mobile",
        "permitted source adapters",
        "app_sync",
        "session-bound polling",
        "cache only the static shell",
        "refetch from the server after governed mutations",
        "app_media",
        "mobile evidence contract",
        "direct binary uploads",
        "offline upload queueing",
        "evidence-reference now, MediaFile later",
        "member maintenance request evidence",
        "contractor completion evidence",
        "member work order feedback evidence",
        "member reopen request evidence",
    ),
}


def main() -> int:
    failures: list[str] = []
    pages_checked = 0
    phrases_checked = 0

    for page_name, phrases in REQUIRED_SECTIONS.items():
        page_path = MANUAL_DIR / page_name
        if not page_path.exists():
            failures.append(f"Missing manual page: docs/manual/{page_name}")
            continue

        pages_checked += 1
        content = page_path.read_text(encoding="utf-8")
        for phrase in phrases:
            phrases_checked += 1
            if phrase not in content:
                failures.append(f"docs/manual/{page_name} is missing: {phrase}")

    print("Phase 3 manual contract check")
    print(f"- Manual pages checked: {pages_checked}")
    print(f"- Required operating phrases checked: {phrases_checked}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
