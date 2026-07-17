"""Smoke-check seeded dashboard review logins and role dashboard rendering."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from scripts.seed_dashboard_review_users import ACCOUNTS, REVIEW_PASSWORD


OPERATIONAL_PAGES_BY_EMAIL = {
    "review.superadmin@logixpm.test": (
        "/super-admin/work-orders",
        "/super-admin/clients",
        "/super-admin/users",
    ),
    "review.admin@logixpm.test": ("/admin-portal/work-orders",),
    "review.pm@logixpm.test": ("/pm/work-orders",),
    "review.assistant@logixpm.test": ("/assistant/work-orders",),
    "review.assistant.manager@logixpm.test": ("/assistant/work-orders",),
    "review.contractor@logixpm.test": (
        "/contractor/work-orders",
        "/contractor/calendar",
        "/contractor/settings",
    ),
    "review.member@logixpm.test": ("/members/works",),
    "review.resident@logixpm.test": ("/members/works",),
}


def _assert_rendered_page(
    response,
    *,
    label: str,
    path: str,
    failures: list[str],
) -> bool:
    page_text = response.get_data(as_text=True)
    if response.status_code != 200:
        failures.append(f"{label}: {path} should render 200, got {response.status_code}")
        return False
    if "Internal Server Error" in page_text:
        failures.append(f"{label}: {path} rendered an internal error body")
        return False
    if "<html" not in page_text.lower() or "</html>" not in page_text.lower():
        failures.append(f"{label}: {path} did not render a complete HTML page")
        return False
    if "dashboard" not in page_text.lower() and "logix" not in page_text.lower():
        failures.append(f"{label}: {path} rendered without dashboard/module identity text")
        return False
    return True


def main() -> int:
    app = create_app()
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True

    failures: list[str] = []

    with app.app_context():
        print("Dashboard review login/render check")
        print(f"- Accounts checked: {len(ACCOUNTS)}")
        print(
            "- Operational pages checked: "
            f"{sum(len(paths) for paths in OPERATIONAL_PAGES_BY_EMAIL.values())}"
        )

        for account in ACCOUNTS:
            with app.test_client() as client:
                response = client.post(
                    "/auth/login",
                    data={
                        "identifier": account.email,
                        "password": REVIEW_PASSWORD,
                    },
                    follow_redirects=False,
                )

                location = response.headers.get("Location", "")
                if response.status_code not in {302, 303}:
                    failures.append(
                        f"{account.label}: expected redirect after login, got {response.status_code}"
                    )
                    continue
                if account.dashboard not in location:
                    failures.append(
                        f"{account.label}: expected {account.dashboard}, got {location or 'no location'}"
                    )
                    continue

                dashboard = client.get(account.dashboard, follow_redirects=False)
                if not _assert_rendered_page(
                    dashboard,
                    label=account.label,
                    path=account.dashboard,
                    failures=failures,
                ):
                    continue

                for page_path in OPERATIONAL_PAGES_BY_EMAIL.get(account.email, ()):
                    page = client.get(page_path, follow_redirects=False)
                    if not _assert_rendered_page(
                        page,
                        label=account.label,
                        path=page_path,
                        failures=failures,
                    ):
                        continue

                print(f"  - {account.label}: {account.email} -> {account.dashboard}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
