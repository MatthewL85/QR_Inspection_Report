"""Smoke-check representative deep operational pages across modules.

This complements the dashboard render smoke check. Dashboards can be healthy
while the pages behind them fail because of record-specific context, permissions
or template drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from scripts.seed_dashboard_review_users import REVIEW_PASSWORD


@dataclass(frozen=True)
class PageCheck:
    label: str
    email: str
    path: str


def _login(client, email: str) -> str | None:
    response = client.post(
        "/auth/login",
        data={"identifier": email, "password": REVIEW_PASSWORD},
        follow_redirects=False,
    )
    if response.status_code not in {302, 303}:
        return f"login for {email} returned {response.status_code}"
    return None


def _assert_page(response, *, label: str, path: str) -> str | None:
    text = response.get_data(as_text=True)
    lowered = text.lower()
    if response.status_code != 200:
        return f"{label}: {path} should render 200, got {response.status_code}"
    if "internal server error" in lowered:
        return f"{label}: {path} rendered an internal error body"
    if "<html" not in lowered or "</html>" not in lowered:
        return f"{label}: {path} did not render a complete HTML page"
    if "logix" not in lowered and "client" not in lowered and "work" not in lowered:
        return f"{label}: {path} rendered without expected platform identity text"
    return None


def _build_page_checks() -> tuple[list[PageCheck], list[str]]:
    from app.models.client.client import Client
    from app.models.contractor.contractor import Contractor
    from app.models.contractor.job_docket import JobDocket
    from app.models.core.user import User
    from app.models.maintenance.maintenance_request import MaintenanceRequest
    from app.models.members.unit import Unit
    from app.models.members.unit_membership import UnitMembership
    from app.models.works.work_order import WorkOrder

    warnings: list[str] = []
    checks: list[PageCheck] = []

    client = (
        Client.query.filter(Client.name == "Matthew Lavery").first()
        or Client.query.order_by(Client.id.desc()).first()
    )
    if client:
        checks.extend(
            [
                PageCheck("Super Admin client profile", "review.superadmin@logixpm.test", f"/super-admin/clients/{client.id}"),
                PageCheck("Super Admin client unit tab", "review.superadmin@logixpm.test", f"/super-admin/clients/{client.id}?tab=units"),
                PageCheck("Super Admin key site tab", "review.superadmin@logixpm.test", f"/super-admin/clients/{client.id}?tab=site"),
                PageCheck("Advanced key site information", "review.superadmin@logixpm.test", f"/clients/{client.id}/key-info"),
            ]
        )
    else:
        warnings.append("No client record found for client profile/key site checks")

    unit_query = Unit.query
    if client:
        unit_query = unit_query.filter(Unit.client_id == client.id)
    unit = unit_query.order_by(Unit.id.asc()).first()
    if unit:
        checks.append(PageCheck("Unit detail", "review.superadmin@logixpm.test", f"/units/{unit.id}"))
    else:
        warnings.append("No unit record found for unit detail check")

    work_order = WorkOrder.query.filter(WorkOrder.unit_id.isnot(None)).order_by(WorkOrder.id.desc()).first()
    if work_order and work_order.unit_id:
        checks.append(
            PageCheck(
                "Management work order review",
                "review.superadmin@logixpm.test",
                f"/units/{work_order.unit_id}/work-orders/{work_order.id}",
            )
        )
    else:
        warnings.append("No unit-linked work order found for management review check")

    contractor_user = User.query.filter_by(email="review.contractor@logixpm.test").first()
    contractor = Contractor.query.filter_by(email="review.contractor@logixpm.test").first()
    contractor_id = getattr(contractor, "id", None)

    contractor_work_order = None
    if contractor_user or contractor_id:
        contractor_work_order = (
            WorkOrder.query.filter(
                (WorkOrder.accepted_contractor_id == getattr(contractor_user, "id", None))
                | (WorkOrder.preferred_contractor_id == getattr(contractor_user, "id", None))
                | (WorkOrder.second_preferred_contractor_id == getattr(contractor_user, "id", None))
                | (WorkOrder.contractor_id == contractor_id)
            )
            .order_by(WorkOrder.id.desc())
            .first()
        )
    contractor_work_order = contractor_work_order or WorkOrder.query.order_by(WorkOrder.id.desc()).first()
    if contractor_work_order:
        checks.append(
            PageCheck(
                "Contractor work order pack",
                "review.contractor@logixpm.test",
                f"/contractor/work-orders/{contractor_work_order.id}",
            )
        )
    else:
        warnings.append("No work order found for contractor pack check")

    docket = None
    if contractor_id:
        docket = JobDocket.query.filter_by(contractor_id=contractor_id).order_by(JobDocket.id.desc()).first()
    docket = docket or JobDocket.query.order_by(JobDocket.id.desc()).first()
    if docket:
        checks.append(
            PageCheck(
                "Contractor job docket",
                "review.contractor@logixpm.test",
                f"/contractor/job-dockets/{docket.id}",
            )
        )
    else:
        warnings.append("No job docket found for contractor docket check")

    member_user = User.query.filter_by(email="review.member@logixpm.test").first()
    member_request = None
    if member_user:
        member_links = UnitMembership.query.filter_by(user_id=member_user.id).all()
        member_ids = [link.member_id for link in member_links]
        unit_ids = [link.unit_id for link in member_links]
        member_request = (
            MaintenanceRequest.query.filter(
                (MaintenanceRequest.requested_by_id == member_user.id)
                | (MaintenanceRequest.member_id.in_(member_ids or [0]))
                | (MaintenanceRequest.unit_id.in_(unit_ids or [0]))
            )
            .order_by(MaintenanceRequest.id.desc())
            .first()
        )
    member_request = member_request or MaintenanceRequest.query.order_by(MaintenanceRequest.id.desc()).first()
    if member_request:
        checks.append(
            PageCheck(
                "Member maintenance request detail",
                "review.member@logixpm.test",
                f"/members/works/requests/{member_request.id}",
            )
        )
    else:
        warnings.append("No maintenance request found for member request detail check")

    return checks, warnings


def main() -> int:
    app = create_app()
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True

    failures: list[str] = []

    with app.app_context():
        page_checks, warnings = _build_page_checks()
        print("Operational surface render check")
        print(f"- Representative pages checked: {len(page_checks)}")

        for warning in warnings:
            print(f"  warning: {warning}")

        for page_check in page_checks:
            with app.test_client() as client:
                login_error = _login(client, page_check.email)
                if login_error:
                    failures.append(f"{page_check.label}: {login_error}")
                    continue

                response = client.get(page_check.path, follow_redirects=False)
                page_error = _assert_page(response, label=page_check.label, path=page_check.path)
                if page_error:
                    failures.append(page_error)
                    continue

                print(f"  - {page_check.label}: {page_check.path}")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
