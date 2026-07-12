"""Verify Contractor Logix document templates stay inside Contractor Logix."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from scripts.seed_dashboard_review_users import REVIEW_PASSWORD


def main() -> int:
    app = create_app()
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True

    failures: list[str] = []

    with app.app_context():
        with app.test_client() as client:
            login = client.post(
                "/auth/login",
                data={
                    "identifier": "review.contractor@logixpm.test",
                    "password": REVIEW_PASSWORD,
                },
                follow_redirects=False,
            )
            if login.status_code not in {302, 303}:
                failures.append(f"contractor login failed: {login.status_code}")

            for path, marker in (
                ("/contractor/settings/document-templates", "Contractor-Owned Templates"),
                ("/contractor/settings/document-templates/job_docket/edit", "Edit Template"),
                ("/contractor/settings/document-templates/job_docket/preview", "Document Preview"),
            ):
                response = client.get(path, follow_redirects=False)
                text = response.get_data(as_text=True)
                if response.status_code != 200:
                    failures.append(f"{path}: expected 200, got {response.status_code}")
                if marker not in text:
                    failures.append(f"{path}: missing marker {marker!r}")
                if "Super Admin" in text:
                    failures.append(f"{path}: rendered Super Admin copy in Contractor Logix")

            bypass = client.get("/settings/document-templates?company_id=1", follow_redirects=False)
            location = bypass.headers.get("Location") or ""
            if bypass.status_code not in {302, 303}:
                failures.append(f"shared settings bypass expected redirect, got {bypass.status_code}")
            if "/contractor/settings/document-templates" not in location:
                failures.append(f"shared settings bypass redirected to unexpected location: {location}")

    if failures:
        print("FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASSED contractor document template boundary check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
