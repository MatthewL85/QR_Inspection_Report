"""Smoke-check seeded dashboard review logins."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from scripts.seed_dashboard_review_users import ACCOUNTS, REVIEW_PASSWORD


def main() -> int:
    app = create_app()
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True

    failures: list[str] = []

    with app.app_context():
        print("Dashboard review login check")
        print(f"- Accounts checked: {len(ACCOUNTS)}")

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
                if dashboard.status_code >= 400:
                    failures.append(
                        f"{account.label}: dashboard {account.dashboard} returned {dashboard.status_code}"
                    )

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
