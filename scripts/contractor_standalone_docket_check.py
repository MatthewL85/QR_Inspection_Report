"""Smoke-check standalone Contractor Logix job docket creation and scheduling."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from app import create_app
    from app.extensions import db
    from app.models.contractor.contractor_calendar_entry import ContractorCalendarEntry
    from app.models.contractor.job_docket import JobDocket

    app = create_app()
    app.config["WTF_CSRF_ENABLED"] = False
    failures: list[str] = []
    marker = "Codex Standalone Smoke"
    external_reference = "EXT-WO-8842"

    with app.app_context():
        with app.test_client() as client:
            login = client.post(
                "/auth/login",
                data={
                    "identifier": "review.contractor@logixpm.test",
                    "password": "review2026",
                },
            )
            if login.status_code not in {302, 303}:
                failures.append(f"Contractor review login failed: HTTP {login.status_code}")

            form_response = client.get("/contractor/job-dockets/new")
            if form_response.status_code != 200:
                failures.append(f"Standalone docket form failed: HTTP {form_response.status_code}")

            create_response = client.post(
                "/contractor/job-dockets/new",
                data={
                    "client_name": marker,
                    "property_name": "Standalone Site",
                    "external_work_order_reference": external_reference,
                    "address_line_1": "1 Test Street",
                    "town_city": "Dublin",
                    "postal_code": "D01TEST",
                    "unit_number": "Apt 1",
                    "required_trade": "Electrical",
                    "priority": "Urgent",
                    "scope_of_works": "Standalone smoke test job",
                    "contact_name": "Test Contact",
                    "contact_phone": "010000000",
                    "contact_email": "test@example.invalid",
                },
            )
            if create_response.status_code not in {302, 303}:
                failures.append(f"Standalone docket create failed: HTTP {create_response.status_code}")

            docket = (
                JobDocket.query
                .filter_by(standalone_client_name=marker)
                .order_by(JobDocket.id.desc())
                .first()
            )
            if not docket:
                failures.append("Standalone docket was not created")
            elif docket.work_order_id is not None:
                failures.append("Standalone docket should not require a Works Logix work order")
            elif not docket.docket_number:
                failures.append("Standalone docket did not receive a docket number")
            elif docket.external_work_order_reference != external_reference:
                failures.append("Standalone docket did not preserve the external work order reference")

            if docket:
                detail_response = client.get(f"/contractor/job-dockets/{docket.id}")
                if detail_response.status_code != 200:
                    failures.append(f"Standalone docket detail failed: HTTP {detail_response.status_code}")

                schedule_response = client.post(
                    f"/contractor/job-dockets/{docket.id}/schedule",
                    data={
                        "scheduled_date": (date.today() + timedelta(days=1)).isoformat(),
                        "start_time": "09:00",
                        "estimated_duration_minutes": "60",
                        "return_to": "docket",
                    },
                )
                if schedule_response.status_code not in {302, 303}:
                    failures.append(f"Standalone docket schedule failed: HTTP {schedule_response.status_code}")

                db.session.refresh(docket)
                entry = ContractorCalendarEntry.query.filter_by(job_docket_id=docket.id).first()
                if not entry:
                    failures.append("Standalone docket did not create a calendar entry")
                elif entry.work_order_id is not None:
                    failures.append("Standalone calendar entry should not require a work order")
                elif not entry.location:
                    failures.append("Standalone calendar entry did not store a location")

                ContractorCalendarEntry.query.filter_by(job_docket_id=docket.id).delete(synchronize_session=False)
                db.session.delete(docket)
                db.session.commit()

    print("Contractor standalone docket check")
    print("- Manual creation route checked: yes")
    print("- Detail route checked: yes")
    print("- Scheduling route checked: yes")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
