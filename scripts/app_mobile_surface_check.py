"""Verify Phase 3E app-ready operational surfaces stay aligned."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


SURFACE_TEMPLATES = {
    "app/templates/members/works.html": (
        "app-ready-surface--members",
        'data-app-mobile-ready="true"',
        'data-app-safe-area="required"',
        'data-app-source-backed="true"',
        'data-app-offline="static-shell-only"',
        'data-app-surface="members-works"',
        "#submit-request",
        "#my-requests",
        "#open-work-orders",
        "#closed-work-orders",
        "#reopen-requests",
        "gar/_ask_panel.html",
    ),
    "app/templates/contractor/work_orders.html": (
        "app-ready-surface--contractor",
        'data-app-mobile-ready="true"',
        'data-app-safe-area="required"',
        'data-app-source-backed="true"',
        'data-app-offline="static-shell-only"',
        'data-app-surface="contractor-work-queue"',
        "#assigned-work",
        "#returned-work",
        "#submitted-work",
        "#active-work",
        "#completed-work",
        "GAR history",
    ),
    "app/templates/notifications/index.html": (
        "app-ready-surface--notifications",
        'data-app-mobile-ready="true"',
        'data-app-safe-area="required"',
        'data-app-source-backed="true"',
        'data-app-offline="static-shell-only"',
        'data-app-surface="notification-centre"',
        "#notification-filters",
        "#notification-list",
        "Needs Action",
        "GAR Related",
    ),
    "app/templates/gar/_ask_panel.html": (
        "app-ready-gar-panel",
        'data-app-mobile-ready="true"',
        'data-app-source-backed="true"',
        'data-app-offline="static-shell-only"',
        "Source-backed summary",
        "source_references",
    ),
}

CSS_TOKENS = (
    ".app-ready-surface",
    "env(safe-area-inset-bottom)",
    ".app-surface-nav",
    "touch-action: manipulation",
    ".app-ready-gar-panel",
    "env(safe-area-inset-top)",
    "@media (max-width: 575.98px)",
)

APP_ACTIONS = {
    "app/templates/members/works.html": (
        "member-maintenance-request",
        "member-work-order-feedback",
        "member-reopen-request",
    ),
    "app/templates/contractor/work_orders.html": (
        "contractor-accept-work-order",
        "contractor-start-work-order",
        "contractor-submit-completion",
    ),
}

APP_ACTION_CONTRACT_TOKENS = (
    'data-app-requires-online="true"',
    'data-app-requires-csrf="true"',
    'data-app-offline-queue="false"',
    'data-app-source-record=',
    'name="csrf_token"',
)

APP_MEDIA_REFERENCES = {
    "app/templates/members/works.html": (
        "member_maintenance_request",
        "member_work_order_feedback",
        "member_reopen_request",
    ),
    "app/templates/contractor/work_orders.html": (
        "contractor_completion_evidence",
    ),
}

APP_MEDIA_REFERENCE_TOKENS = (
    'data-app-media-reference="true"',
    'data-app-media-source-model="MediaFile"',
    'data-app-direct-upload="false"',
)


def main() -> int:
    failures: list[str] = []

    for template_name, tokens in SURFACE_TEMPLATES.items():
        template_path = PROJECT_ROOT / template_name
        if not template_path.exists():
            failures.append(f"Missing app-ready template: {template_name}")
            continue
        content = template_path.read_text(encoding="utf-8", errors="replace")
        for token in tokens:
            if token not in content:
                failures.append(f"{template_name} is missing app-ready token: {token}")
        for action_key in APP_ACTIONS.get(template_name, ()):
            action_token = f'data-app-action="{action_key}"'
            if action_token not in content:
                failures.append(f"{template_name} is missing app action token: {action_key}")

    for template_name, action_keys in APP_ACTIONS.items():
        template_path = PROJECT_ROOT / template_name
        if not template_path.exists():
            continue
        content = template_path.read_text(encoding="utf-8", errors="replace")
        for action_key in action_keys:
            action_token = f'data-app-action="{action_key}"'
            action_index = content.find(action_token)
            if action_index == -1:
                continue
            form_start = content.rfind("<form", 0, action_index)
            form_end = content.find("</form>", action_index)
            form_chunk = content[form_start:form_end] if form_start != -1 and form_end != -1 else ""
            for token in APP_ACTION_CONTRACT_TOKENS:
                if token not in form_chunk:
                    failures.append(f"{template_name} action {action_key} is missing contract token: {token}")
        for media_context in APP_MEDIA_REFERENCES.get(template_name, ()):
            context_token = f'data-app-media-context="{media_context}"'
            if context_token not in content:
                failures.append(f"{template_name} is missing media reference context: {media_context}")
        if template_name in APP_MEDIA_REFERENCES:
            for token in APP_MEDIA_REFERENCE_TOKENS:
                if token not in content:
                    failures.append(f"{template_name} is missing media reference token: {token}")

    css_path = PROJECT_ROOT / "app/static/styles.css"
    if not css_path.exists():
        failures.append("Missing app/static/styles.css")
    else:
        css = css_path.read_text(encoding="utf-8", errors="replace")
        for token in CSS_TOKENS:
            if token not in css:
                failures.append(f"styles.css is missing app-ready CSS token: {token}")

    print("App mobile surface check")
    print(f"- Operational templates checked: {len(SURFACE_TEMPLATES)}")
    print(f"- CSS surface tokens checked: {len(CSS_TOKENS)}")
    print(f"- App action contracts checked: {sum(len(actions) for actions in APP_ACTIONS.values())}")
    print(f"- App media reference contexts checked: {sum(len(contexts) for contexts in APP_MEDIA_REFERENCES.values())}")
    print("- Mobile quick navigation checked: yes")
    print("- GAR app panel checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
