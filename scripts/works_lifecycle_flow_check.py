r"""Exercise the Phase 3 cross-module Works lifecycle.

This check creates a temporary Members -> Assistant/Works -> Contractor ->
feedback -> review -> reopen flow, verifies the persisted lifecycle events and
GAR work order context, then deletes the temporary records.

Run from the project root:
    .\venv\Scripts\python.exe scripts\works_lifecycle_flow_check.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _email(marker: str, name: str) -> str:
    return f"{name}.{marker.lower()}@example.invalid"


def _delete_by_ids(model, ids: list[int]) -> None:
    if ids:
        model.query.filter(model.id.in_(ids)).delete(synchronize_session=False)


def _cleanup_stale_smoke_records(models: dict[str, object]) -> None:
    """Remove any prior interrupted smoke data before creating a new flow."""

    Company = models["Company"]
    Client = models["Client"]
    Contractor = models["Contractor"]
    ContractorFeedback = models["ContractorFeedback"]
    MaintenanceRequest = models["MaintenanceRequest"]
    Member = models["Member"]
    Notification = models["Notification"]
    Unit = models["Unit"]
    UnitMembership = models["UnitMembership"]
    User = models["User"]
    WorkOrder = models["WorkOrder"]
    WorkOrderCompletion = models["WorkOrderCompletion"]
    WorkOrderLifecycleEvent = models["WorkOrderLifecycleEvent"]
    WorkOrderReopenRequest = models["WorkOrderReopenRequest"]

    smoke_users = User.query.filter(User.username.ilike("phase3smoke%")).all()
    smoke_companies = Company.query.filter(Company.subdomain.ilike("phase3smoke%")).all()
    smoke_contractors = Contractor.query.filter(Contractor.company_name.ilike("PHASE3SMOKE%")).all()
    smoke_clients = Client.query.filter(Client.name.ilike("PHASE3SMOKE%")).all()
    smoke_units = Unit.query.filter(Unit.unit_label.ilike("PHASE3SMOKE%")).all()
    smoke_members = Member.query.filter(Member.first_name.ilike("PHASE3SMOKE%")).all()
    smoke_requests = MaintenanceRequest.query.filter(MaintenanceRequest.title.ilike("PHASE3SMOKE%")).all()

    user_ids = [item.id for item in smoke_users]
    company_ids = [item.id for item in smoke_companies]
    contractor_ids = [item.id for item in smoke_contractors]
    client_ids = [item.id for item in smoke_clients]
    unit_ids = [item.id for item in smoke_units]
    member_ids = [item.id for item in smoke_members]
    request_ids = [item.id for item in smoke_requests]

    smoke_work_orders = WorkOrder.query.filter(
        (WorkOrder.title.ilike("PHASE3SMOKE%"))
        | (WorkOrder.company_id.in_(company_ids or [0]))
        | (WorkOrder.client_id.in_(client_ids or [0]))
        | (WorkOrder.unit_id.in_(unit_ids or [0]))
        | (WorkOrder.maintenance_request_id.in_(request_ids or [0]))
    ).all()
    work_order_ids = [item.id for item in smoke_work_orders]

    _delete_by_ids(Notification, [
        item.id
        for item in Notification.query.filter(Notification.recipient_id.in_(user_ids or [0])).all()
    ])
    WorkOrderLifecycleEvent.query.filter(
        WorkOrderLifecycleEvent.work_order_id.in_(work_order_ids or [0])
    ).delete(synchronize_session=False)
    WorkOrderReopenRequest.query.filter(
        WorkOrderReopenRequest.work_order_id.in_(work_order_ids or [0])
    ).delete(synchronize_session=False)
    ContractorFeedback.query.filter(
        ContractorFeedback.work_order_id.in_(work_order_ids or [0])
    ).delete(synchronize_session=False)
    WorkOrderCompletion.query.filter(
        WorkOrderCompletion.work_order_id.in_(work_order_ids or [0])
    ).delete(synchronize_session=False)
    _delete_by_ids(WorkOrder, work_order_ids)
    _delete_by_ids(MaintenanceRequest, request_ids)
    UnitMembership.query.filter(
        (UnitMembership.member_id.in_(member_ids or [0]))
        | (UnitMembership.unit_id.in_(unit_ids or [0]))
    ).delete(synchronize_session=False)
    _delete_by_ids(Member, member_ids)
    _delete_by_ids(Unit, unit_ids)
    _delete_by_ids(Contractor, contractor_ids)
    _delete_by_ids(Client, client_ids)
    _delete_by_ids(User, user_ids)
    _delete_by_ids(Company, company_ids)


def main() -> int:
    from app import create_app
    from app.extensions import db
    from app.models.client.client import Client
    from app.models.contractor.contractor import Contractor
    from app.models.contractor.contractor_feedback import ContractorFeedback
    from app.models.core.notification import Notification
    from app.models.core.role import Role
    from app.models.core.user import User
    from app.models.maintenance.maintenance_request import MaintenanceRequest
    from app.models.members.member import Member
    from app.models.members.unit import Unit
    from app.models.members.unit_membership import UnitMembership
    from app.models.onboarding.company import Company
    from app.models.works.work_order import WorkOrder
    from app.models.works.work_order_completion import WorkOrderCompletion
    from app.models.works.work_order_lifecycle_event import WorkOrderLifecycleEvent
    from app.models.works.work_order_reopen_request import WorkOrderReopenRequest
    from app.services.gar import build_gar_inquiry_response, build_operational_digest, build_work_order_context
    from app.services.core.notification_intelligence import build_notification_views, notification_summary
    from app.services.core.notification_feed import (
        NotificationFilters,
        build_notification_context,
        notification_feed_payload,
    )
    from app.services.members.works_context import build_member_works_context, member_works_feed_payload
    from app.services.work_order_reopen_service import WorkOrderReopenService
    from app.services.works.audit_pack_service import build_work_order_audit_pack
    from app.services.works.workflow_service import (
        ContractorWorkFilters,
        WorksFilters,
        assign_contractor_to_work_order,
        build_work_order_lifecycle,
        build_command_centre,
        contractor_work_queue_payload,
        contractor_update_work_order,
        convert_member_request_to_work_order,
        get_contractor_work_orders,
        notify_member_request_submitted,
        notify_work_order_reopen_requested,
        review_contractor_completion,
        submit_member_work_order_feedback,
        works_command_centre_payload,
    )

    app = create_app()
    marker = f"PHASE3SMOKE{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}"
    created_role_ids: list[int] = []
    ids: dict[str, list[int]] = {
        "users": [],
        "notifications": [],
        "members": [],
        "unit_memberships": [],
        "units": [],
        "maintenance_requests": [],
        "contractors": [],
        "work_orders": [],
        "companies": [],
        "clients": [],
    }

    failures: list[str] = []

    with app.app_context():
        _cleanup_stale_smoke_records(
            {
                "Company": Company,
                "Client": Client,
                "Contractor": Contractor,
                "ContractorFeedback": ContractorFeedback,
                "MaintenanceRequest": MaintenanceRequest,
                "Member": Member,
                "Notification": Notification,
                "Unit": Unit,
                "UnitMembership": UnitMembership,
                "User": User,
                "WorkOrder": WorkOrder,
                "WorkOrderCompletion": WorkOrderCompletion,
                "WorkOrderLifecycleEvent": WorkOrderLifecycleEvent,
                "WorkOrderReopenRequest": WorkOrderReopenRequest,
            }
        )
        db.session.commit()

        try:
            role = Role.query.filter_by(name="Super Admin").first()
            if not role:
                role = Role(name="Super Admin", description="Temporary role for lifecycle smoke check")
                db.session.add(role)
                db.session.flush()
                created_role_ids.append(role.id)

            assistant_manager_role = Role.query.filter_by(name="Assistant Manager").first()
            if not assistant_manager_role:
                assistant_manager_role = Role(
                    name="Assistant Manager",
                    description="Temporary cover role for lifecycle smoke check",
                )
                db.session.add(assistant_manager_role)
                db.session.flush()
                created_role_ids.append(assistant_manager_role.id)

            company = Company(
                name=f"{marker} Management Company",
                company_type="Property Management",
                country="Ireland",
                currency="EUR",
                subdomain=marker.lower(),
            )
            db.session.add(company)
            db.session.flush()
            ids["companies"].append(company.id)

            admin_user = User(
                full_name=f"{marker} Admin",
                email=_email(marker, "admin"),
                username=f"{marker.lower()}_admin",
                password_hash="not-used",
                pin="0000",
                role_id=role.id,
                company_id=company.id,
                is_active=True,
            )
            assistant_manager_user = User(
                full_name=f"{marker} Assistant Manager",
                email=_email(marker, "assistant.manager"),
                username=f"{marker.lower()}_assistant_manager",
                password_hash="not-used",
                pin="0000",
                role_id=assistant_manager_role.id,
                company_id=company.id,
                is_active=True,
            )
            contractor_user = User(
                full_name=f"{marker} Contractor",
                email=_email(marker, "contractor"),
                username=f"{marker.lower()}_contractor",
                password_hash="not-used",
                pin="0000",
                company_id=company.id,
                is_active=True,
            )
            member_user = User(
                full_name=f"{marker} Member",
                email=_email(marker, "member"),
                username=f"{marker.lower()}_member",
                password_hash="not-used",
                pin="0000",
                company_id=company.id,
                is_active=True,
                is_owner=True,
                is_resident=True,
            )
            db.session.add_all([admin_user, assistant_manager_user, contractor_user, member_user])
            db.session.flush()
            ids["users"].extend([admin_user.id, assistant_manager_user.id, contractor_user.id, member_user.id])

            client = Client(
                company_id=company.id,
                name=f"{marker} Test Development",
                property_name=f"{marker} Works Lifecycle",
                client_type="OMC",
                address_line1="Smoke Test House",
                city="Dublin",
                country="Ireland",
                region="Dublin",
                assigned_pm_id=admin_user.id,
            )
            db.session.add(client)
            db.session.flush()
            ids["clients"].append(client.id)

            unit = Unit(
                company_id=company.id,
                client_id=client.id,
                unit_label=f"{marker} A-001",
                unit_number="A-001",
                unit_type="Apartment",
                unit_category="Residential",
                block_name="Block A",
                status="Active",
                occupancy_status="owner_occupied",
            )
            db.session.add(unit)
            db.session.flush()
            ids["units"].append(unit.id)

            member = Member(
                user_id=member_user.id,
                company_id=company.id,
                client_id=client.id,
                first_name=marker,
                last_name="Member",
                email=member_user.email,
                phone="0100000000",
                is_owner=True,
                is_owner_occupier=True,
            )
            db.session.add(member)
            db.session.flush()
            ids["members"].append(member.id)

            membership = UnitMembership(
                unit_id=unit.id,
                member_id=member.id,
                role="owner",
                is_primary=True,
                is_current=True,
            )
            db.session.add(membership)
            db.session.flush()
            ids["unit_memberships"].append(membership.id)

            contractor = Contractor(
                company_name=f"{marker} Contractor Ltd",
                email=_email(marker, "contractorcompany"),
                phone="0199999999",
                business_type="General Maintenance",
                is_active=True,
                consent_to_contact=True,
            )
            db.session.add(contractor)
            db.session.flush()
            ids["contractors"].append(contractor.id)
            contractor_user.contractor_id = contractor.id

            previous_work_order = WorkOrder(
                company_id=company.id,
                client_id=client.id,
                unit_id=unit.id,
                contractor_id=contractor.id,
                assigned_user_id=contractor_user.id,
                created_by_id=admin_user.id,
                title=f"{marker} previous leaking tap",
                description="Previous plumbing leak at the same unit for GAR relevant-history detection.",
                request_type="Work Order",
                business_type="Plumbing",
                status="Closed",
            )
            db.session.add(previous_work_order)
            db.session.flush()
            ids["work_orders"].append(previous_work_order.id)
            previous_completion = WorkOrderCompletion(
                work_order_id=previous_work_order.id,
                completed_by_id=contractor_user.id,
                contractor_id=contractor.id,
                completion_notes="Replaced tap washer and checked pipework for visible leaks.",
                visibility_scope="Admin,PM,Contractor",
                consent_verified=True,
            )
            db.session.add(previous_completion)
            db.session.flush()

            maintenance_request = MaintenanceRequest(
                member_id=member.id,
                unit_id=unit.id,
                requested_by_id=member_user.id,
                title=f"{marker} leaking tap",
                description="Temporary cross-module smoke test request.",
                category="Plumbing",
                urgency_level="Normal",
                request_channel="Members Logix",
                source_system="Members Logix",
                visibility_scope="Admin,PM",
                consent_verified=True,
                status="Pending",
            )
            db.session.add(maintenance_request)
            db.session.commit()
            ids["maintenance_requests"].append(maintenance_request.id)
            notify_member_request_submitted(maintenance_request)

            work_order = convert_member_request_to_work_order(
                request_id=maintenance_request.id,
                company_id=company.id,
                created_by_id=assistant_manager_user.id,
                allowed_client_ids=None,
                access_context="assistant_manager_cover",
            )
            if not work_order:
                failures.append("Member request did not convert to a work order.")
                raise RuntimeError("workflow stopped")
            ids["work_orders"].append(work_order.id)

            if not assign_contractor_to_work_order(
                work_order_id=work_order.id,
                company_id=company.id,
                contractor_id=contractor.id,
                allowed_client_ids=None,
                assigned_by_id=assistant_manager_user.id,
                access_context="assistant_manager_cover",
            ):
                failures.append("Contractor assignment failed.")
            contractor_queue = get_contractor_work_orders(contractor.id, contractor_user.id)
            contractor_next_actions = contractor_queue.get("next_actions", [])
            if contractor_queue.get("stats", {}).get("assigned", 0) and not contractor_next_actions:
                failures.append("Contractor queue did not provide next actions for assigned work.")
            if contractor_next_actions and contractor_next_actions[0].get("anchor") != "assigned-work":
                failures.append("Contractor queue next action did not point to assigned work first.")
            contractor_assignment_feed = contractor_work_queue_payload(
                contractor_queue,
                ContractorWorkFilters(),
            )
            assigned_feed_items = contractor_assignment_feed.get("queues", {}).get("assigned", [])
            if assigned_feed_items:
                gar_history = assigned_feed_items[0].get("gar_relevant_history", {})
                if gar_history.get("related_count", 0) < 1:
                    failures.append("Contractor feed did not include GAR related work history.")
                if "contractor_safe_summary" not in gar_history:
                    failures.append("Contractor feed did not include GAR contractor-safe history summary.")
                if "routing_recommendation" not in gar_history:
                    failures.append("Contractor feed did not include GAR routing recommendation.")

            for action in ("accept", "start"):
                if not contractor_update_work_order(
                    work_order_id=work_order.id,
                    contractor_id=contractor.id,
                    user_id=contractor_user.id,
                    action=action,
                ):
                    failures.append(f"Contractor action failed: {action}")

            if not contractor_update_work_order(
                work_order_id=work_order.id,
                contractor_id=contractor.id,
                user_id=contractor_user.id,
                action="complete",
                completion_notes="Temporary completion evidence submitted.",
                evidence_reference=f"{marker}-evidence",
            ):
                failures.append("Contractor completion failed.")

            db.session.refresh(work_order)
            completion_audit_pack = build_work_order_audit_pack(work_order)
            completion_evidence = completion_audit_pack.get("completion_evidence", {})
            if not completion_evidence.get("submitted"):
                failures.append("Completion evidence pack did not identify the submitted completion.")
            if completion_evidence.get("quality_status") != "review_ready":
                failures.append("Completion evidence pack did not mark complete notes and evidence as review-ready.")
            if completion_evidence.get("evidence_reference_type") != "reference":
                failures.append("Completion evidence pack did not classify the submitted evidence reference.")
            if completion_evidence.get("attachments_count") != 1:
                failures.append("Completion evidence pack did not expose the submitted attachment count.")

            contractor_completion_feed = contractor_work_queue_payload(
                get_contractor_work_orders(contractor.id, contractor_user.id),
                ContractorWorkFilters(),
            )
            submitted_feed_item = next(
                (
                    item
                    for item in contractor_completion_feed.get("queues", {}).get("submitted", [])
                    if item.get("id") == work_order.id
                ),
                None,
            )
            if not submitted_feed_item:
                failures.append("Contractor feed did not expose the submitted work order.")
            elif submitted_feed_item.get("completion_evidence", {}).get("quality_status") != "review_ready":
                failures.append("Contractor feed did not expose review-ready completion evidence.")

            return_reason = "Please add clearer completion photos before closure."
            if not review_contractor_completion(
                work_order_id=work_order.id,
                company_id=company.id,
                reviewed_by_user_id=admin_user.id,
                decision="return",
                review_notes=return_reason,
            ):
                failures.append("Completion return failed.")

            contractor_return_feed = contractor_work_queue_payload(
                get_contractor_work_orders(contractor.id, contractor_user.id),
                ContractorWorkFilters(),
            )
            returned_feed_item = next(
                (
                    item
                    for item in contractor_return_feed.get("queues", {}).get("returned", [])
                    if item.get("id") == work_order.id
                ),
                None,
            )
            if not returned_feed_item:
                failures.append("Contractor feed did not expose the returned work order.")
            else:
                return_context = returned_feed_item.get("return_context", {})
                if not return_context.get("returned"):
                    failures.append("Returned work order feed did not expose return context.")
                if return_reason not in (return_context.get("reason") or ""):
                    failures.append("Returned work order feed did not expose the PM/Admin return reason.")
                review_cycle = returned_feed_item.get("review_cycle", {})
                if review_cycle.get("completion_returns") != 1:
                    failures.append("Returned work order feed did not count the completion return.")
                if review_cycle.get("completion_submissions") != 1:
                    failures.append("Returned work order feed did not count the original completion submission.")

            if not contractor_update_work_order(
                work_order_id=work_order.id,
                contractor_id=contractor.id,
                user_id=contractor_user.id,
                action="complete",
                completion_notes="Temporary completion evidence resubmitted after return.",
                evidence_reference=f"{marker}-resubmitted-evidence",
            ):
                failures.append("Contractor completion resubmission failed.")

            second_return_reason = "Completion evidence still needs clearer before and after notes."
            if not review_contractor_completion(
                work_order_id=work_order.id,
                company_id=company.id,
                reviewed_by_user_id=admin_user.id,
                decision="return",
                review_notes=second_return_reason,
            ):
                failures.append("Second completion return failed.")

            contractor_repeat_return_feed = contractor_work_queue_payload(
                get_contractor_work_orders(contractor.id, contractor_user.id),
                ContractorWorkFilters(),
            )
            repeated_return_feed_item = next(
                (
                    item
                    for item in contractor_repeat_return_feed.get("queues", {}).get("returned", [])
                    if item.get("id") == work_order.id
                ),
                None,
            )
            if not repeated_return_feed_item:
                failures.append("Contractor feed did not expose the repeated returned work order.")
            else:
                repeat_review_cycle = repeated_return_feed_item.get("review_cycle", {})
                if repeat_review_cycle.get("completion_returns") != 2:
                    failures.append("Repeated returned work order feed did not count both completion returns.")
                if not repeat_review_cycle.get("needs_management_attention"):
                    failures.append("Repeated returned work order feed did not flag management attention.")
                repeat_return_context = repeated_return_feed_item.get("return_context", {})
                if second_return_reason not in (repeat_return_context.get("reason") or ""):
                    failures.append("Repeated returned work order feed did not expose the latest return reason.")

            if not contractor_update_work_order(
                work_order_id=work_order.id,
                contractor_id=contractor.id,
                user_id=contractor_user.id,
                action="complete",
                completion_notes="Temporary completion evidence resubmitted after second return.",
                evidence_reference=f"{marker}-second-resubmitted-evidence",
            ):
                failures.append("Contractor second completion resubmission failed.")

            if not submit_member_work_order_feedback(
                work_order=work_order,
                given_by_id=member_user.id,
                rating=4.0,
                comments="Temporary feedback for lifecycle smoke test.",
                evidence_reference=f"{marker}-feedback-evidence",
            ):
                failures.append("Member feedback failed.")

            if not review_contractor_completion(
                work_order_id=work_order.id,
                company_id=company.id,
                reviewed_by_user_id=admin_user.id,
                decision="approve",
                review_notes="Temporary approval for lifecycle smoke test.",
            ):
                failures.append("Completion approval failed.")

            reopen_request = WorkOrderReopenService.create_request(
                work_order=work_order,
                reason="Temporary reopen test.",
                additional_details="Testing Members Logix reopen to Works Logix.",
                evidence_reference=f"{marker}-reopen-evidence",
                requested_by_member_id=member.id,
            )
            if not reopen_request:
                failures.append("Reopen request failed.")
            else:
                notify_work_order_reopen_requested(reopen_request)

            if reopen_request and not WorkOrderReopenService.approve_request(
                request_id=reopen_request.id,
                company_id=company.id,
                reviewed_by_user_id=admin_user.id,
                review_notes="Temporary reopen approval.",
            ):
                failures.append("Reopen approval failed.")

            db.session.refresh(work_order)
            events = WorkOrderLifecycleEvent.query.filter_by(work_order_id=work_order.id).all()
            event_types = {event.event_type for event in events}
            required_event_types = {
                "member_request_converted",
                "contractor_assigned",
                "contractor_accepted",
                "contractor_started",
                "completion_submitted",
                "completion_returned",
                "member_feedback_submitted",
                "completion_approved",
                "reopen_requested",
                "reopen_approved",
            }
            missing_events = sorted(required_event_types.difference(event_types))
            if missing_events:
                failures.append("Missing lifecycle events: " + ", ".join(missing_events))

            cover_events = [
                event for event in events
                if (event.event_metadata or {}).get("access_context") == "assistant_manager_cover"
            ]
            if len(cover_events) < 2:
                failures.append("Assistant Manager cover access was not recorded on conversion and routing events.")

            timeline = build_work_order_lifecycle(work_order)
            if len(timeline) < len(required_event_types):
                failures.append(
                    f"Lifecycle timeline too short: {len(timeline)} events returned."
                )
            cover_timeline_events = [
                event for event in timeline
                if event.get("access_context") == "assistant_manager_cover"
            ]
            if len(cover_timeline_events) < 2:
                failures.append("Lifecycle timeline did not expose Assistant Manager cover context.")

            gar_context = build_work_order_context(
                work_order.id,
                viewer_user_id=admin_user.id,
                audience="admin",
            )
            if gar_context.get("context_type") != "work_order":
                failures.append("GAR context did not identify the work order context type.")
            if not gar_context.get("lifecycle_context"):
                failures.append("GAR context did not include lifecycle events.")
            operational_intelligence = gar_context.get("operational_intelligence", {})
            if not operational_intelligence.get("current_owner", {}).get("team"):
                failures.append("GAR operational intelligence did not identify the current owner.")
            if not operational_intelligence.get("recommended_next_step", {}).get("action"):
                failures.append("GAR operational intelligence did not provide a recommended next step.")
            if not operational_intelligence.get("audit_signal", {}).get("lifecycle_event_count"):
                failures.append("GAR operational intelligence did not include audit signal counts.")
            contractor_signal = operational_intelligence.get("contractor_signal", {})
            if contractor_signal.get("completion_returns", 0) < 2:
                failures.append("GAR operational intelligence did not expose repeated completion return count.")
            if contractor_signal.get("resubmissions", 0) < 1:
                failures.append("GAR operational intelligence did not expose completion resubmission count.")
            if not contractor_signal.get("needs_management_attention"):
                failures.append("GAR operational intelligence did not flag repeated returns for management attention.")
            gar_audit_signal = operational_intelligence.get("audit_signal", {})
            if gar_audit_signal.get("cover_event_count", 0) < 2:
                failures.append("GAR operational intelligence did not expose Assistant Manager cover events.")
            if "assistant_manager_cover" not in gar_audit_signal.get("access_contexts", []):
                failures.append("GAR operational intelligence did not include assistant_manager_cover context.")
            relevant_history = gar_context.get("relevant_history", {})
            if relevant_history.get("context_type") != "work_order_relevant_history":
                failures.append("GAR context did not include relevant work history.")
            if relevant_history.get("summary", {}).get("related_count", 0) < 1:
                failures.append("GAR relevant history did not detect the previous related work order.")
            if "contractor_safe_summary" not in relevant_history:
                failures.append("GAR relevant history did not include a contractor-safe summary.")
            if not relevant_history.get("routing_recommendation", {}).get("action"):
                failures.append("GAR relevant history did not include routing intelligence.")

            audit_pack = build_work_order_audit_pack(work_order)
            audit_access = audit_pack.get("access_context", {})
            if audit_access.get("cover_event_count", 0) < 2:
                failures.append("Audit pack did not expose Assistant Manager cover events.")
            if "assistant_manager_cover" not in audit_access.get("contexts", []):
                failures.append("Audit pack did not include assistant_manager_cover context.")
            audit_review_cycle = audit_pack.get("review_cycle", {})
            if audit_review_cycle.get("completion_returns", 0) < 2:
                failures.append("Audit pack did not expose repeated completion return count.")
            if audit_review_cycle.get("resubmissions", 0) < 1:
                failures.append("Audit pack did not expose completion resubmission count.")
            if not audit_review_cycle.get("needs_management_attention"):
                failures.append("Audit pack did not flag repeated returns for management attention.")

            command_centre = build_command_centre(company.id, WorksFilters())
            command_centre_with_history = build_command_centre(
                company.id,
                WorksFilters(),
                include_gar_history=True,
            )
            next_actions = command_centre.get("next_actions", [])
            has_live_attention = any(
                queue.get("count", 0) > 0
                for queue in command_centre.get("operational_queues", {}).values()
            )
            if has_live_attention and not next_actions:
                failures.append("Works command centre did not provide prioritised next actions.")
            elif next_actions and next_actions[0].get("priority_rank", 0) < next_actions[-1].get("priority_rank", 0):
                failures.append("Works command centre next actions are not ordered by priority.")
            command_feed = works_command_centre_payload(
                command_centre_with_history,
                WorksFilters(),
                role_context="super_admin",
            )
            if command_feed.get("context_type") != "works_command_centre":
                failures.append("Works command-centre feed contract is missing its context type.")
            for key in ("member_requests", "open_work_orders", "closed_work_orders", "reopen_requests", "repeated_returns"):
                if key not in command_feed.get("queues", {}):
                    failures.append(f"Works command-centre feed is missing the {key} queue.")
            if command_centre.get("stats", {}).get("repeated_returns", 0) < 1:
                failures.append("Works command centre did not count repeated completion returns.")
            if command_centre.get("operational_queues", {}).get("repeated_returns", {}).get("count", 0) < 1:
                failures.append("Works command centre repeated returns queue did not surface the work order.")
            repeated_return_queue_item = next(
                (
                    item
                    for item in command_feed.get("queues", {}).get("repeated_returns", [])
                    if item.get("id") == work_order.id
                ),
                None,
            )
            if not repeated_return_queue_item:
                failures.append("Works command-centre feed did not expose the repeated return queue item.")
            elif not repeated_return_queue_item.get("review_cycle", {}).get("needs_management_attention"):
                failures.append("Works command-centre repeated return item did not expose review-cycle attention.")
            elif not repeated_return_queue_item.get("quality_review_signal", {}).get("suggested_focus"):
                failures.append("Works command-centre repeated return item did not expose quality review focus.")
            if "summary" not in command_feed.get("gar", {}):
                failures.append("Works command-centre feed did not include GAR summary context.")
            if not command_feed.get("gar", {}).get("history_review"):
                failures.append("Works command-centre feed did not include GAR history review records.")
            if not command_feed.get("gar", {}).get("contractor_quality"):
                failures.append("Works command-centre feed did not expose GAR contractor quality patterns.")
            if not command_centre_with_history.get("gar_history_work_orders"):
                failures.append("Works command centre did not expose GAR history review records.")
            command_open_items = command_feed.get("queues", {}).get("open_work_orders", [])
            current_open_item = next(
                (item for item in command_open_items if item.get("id") == work_order.id),
                None,
            )
            if current_open_item:
                gar_history = current_open_item.get("gar_relevant_history", {})
                if gar_history.get("related_count", 0) < 1:
                    failures.append("Works command-centre feed did not include GAR related work history.")
                if "admin_summary" not in gar_history:
                    failures.append("Works command-centre feed did not include GAR admin history summary.")
                if "routing_recommendation" not in gar_history:
                    failures.append("Works command-centre feed did not include GAR routing recommendation.")
            works_intelligence = command_centre.get("gar_works_intelligence", {})
            if works_intelligence.get("context_type") != "works_intelligence":
                failures.append("Works command centre did not include GAR Works intelligence.")
            if not works_intelligence.get("signals"):
                failures.append("GAR Works intelligence did not include signal definitions.")
            if "pattern_memory" not in works_intelligence:
                failures.append("GAR Works intelligence did not include issue pattern memory.")
            if works_intelligence.get("summary", {}).get("repeated_completion_returns", 0) < 1:
                failures.append("GAR Works intelligence did not count repeated completion returns.")
            if works_intelligence.get("summary", {}).get("contractor_quality_risks", 0) < 1:
                failures.append("GAR Works intelligence did not count contractor quality risks.")
            repeated_return_signal = next(
                (
                    signal for signal in works_intelligence.get("signals", [])
                    if signal.get("key") == "repeated_completion_returns"
                ),
                None,
            )
            if not repeated_return_signal:
                failures.append("GAR Works intelligence did not define the repeated completion returns signal.")
            elif repeated_return_signal.get("count", 0) < 1:
                failures.append("GAR Works intelligence repeated completion returns signal did not include the work order.")
            contractor_quality_signal = next(
                (
                    signal for signal in works_intelligence.get("signals", [])
                    if signal.get("key") == "contractor_quality_risk"
                ),
                None,
            )
            if not contractor_quality_signal:
                failures.append("GAR Works intelligence did not define the contractor quality risk signal.")
            elif contractor_quality_signal.get("count", 0) < 1:
                failures.append("GAR Works intelligence contractor quality risk signal did not include the contractor.")
            contractor_quality_patterns = (
                works_intelligence.get("pattern_memory", {})
                .get("patterns", {})
                .get("contractor_quality", [])
            )
            if not contractor_quality_patterns:
                failures.append("GAR pattern memory did not expose contractor quality risk patterns.")
            cover_context = works_intelligence.get("cover_context", {})
            if cover_context.get("cover_event_count", 0) < 2:
                failures.append("GAR Works intelligence did not expose Assistant Manager cover events.")
            if cover_context.get("access_context") != "assistant_manager_cover":
                failures.append("GAR Works intelligence did not include assistant_manager_cover context.")

            management_digest = build_operational_digest(
                company_id=company.id,
                role_context="property_manager",
            )
            management_quality = management_digest.get("quality_signals", {})
            if not management_quality.get("contractor_quality_visible"):
                failures.append("GAR management digest did not expose contractor quality visibility.")
            if management_quality.get("contractor_quality_count", 0) < 1:
                failures.append("GAR management digest did not include contractor quality risk count.")
            if not management_quality.get("contractor_quality"):
                failures.append("GAR management digest did not include contractor quality records.")

            contractor_digest = build_operational_digest(
                company_id=company.id,
                role_context="contractor",
            )
            contractor_quality = contractor_digest.get("quality_signals", {})
            if contractor_quality.get("contractor_quality_visible"):
                failures.append("GAR contractor digest exposed management contractor quality visibility.")
            if contractor_quality.get("contractor_quality"):
                failures.append("GAR contractor digest leaked contractor quality risk records.")

            management_quality_inquiry = build_gar_inquiry_response(
                "Which contractors have repeated returns or low feedback?",
                role_context="property_manager",
                company_id=company.id,
                allowed_client_ids=(client.id,),
                execute_source_query=True,
            )
            if management_quality_inquiry.get("response_status") != "ready_for_source_query":
                failures.append("GAR contractor quality inquiry was not source-query ready for management.")
            quality_result = management_quality_inquiry.get("source_query_result", {})
            if not quality_result.get("query_ready"):
                failures.append("GAR contractor quality inquiry did not return a query-ready Works result.")
            if not quality_result.get("gar", {}).get("contractor_quality_visible"):
                failures.append("GAR contractor quality inquiry did not expose management quality visibility.")
            if not quality_result.get("gar", {}).get("contractor_quality"):
                failures.append("GAR contractor quality inquiry did not return contractor quality records.")
            if not quality_result.get("records", {}).get("repeated_returns"):
                failures.append("GAR contractor quality inquiry did not include repeated return records.")

            contractor_quality_inquiry = build_gar_inquiry_response(
                "Which contractors have repeated returns or low feedback?",
                role_context="contractor",
                company_id=company.id,
                user_id=contractor_user.id,
                execute_source_query=True,
            )
            contractor_quality_result = contractor_quality_inquiry.get("source_query_result", {})
            if contractor_quality_result.get("context_type") != "gar_contractor_works_source_query":
                failures.append("GAR contractor role inquiry did not use contractor-scoped Works source query.")
            if contractor_quality_result.get("visibility", {}).get("scope") != "assigned_contractor_queue":
                failures.append("GAR contractor role inquiry did not preserve contractor queue scope.")
            if contractor_quality_result.get("gar", {}).get("contractor_quality_visible"):
                failures.append("GAR contractor role inquiry exposed management quality visibility.")
            if contractor_quality_result.get("gar", {}).get("contractor_quality"):
                failures.append("GAR contractor role inquiry leaked contractor quality records.")
            if contractor_quality_result.get("visibility", {}).get("management_quality_records_included"):
                failures.append("GAR contractor role inquiry leaked management quality records.")
            if not any(
                contractor_quality_result.get("records", {}).get(key)
                for key in ("assigned", "active", "returned", "submitted", "closed")
            ):
                failures.append("GAR contractor role inquiry did not return contractor queue records.")

            contractor_feed = contractor_work_queue_payload(
                get_contractor_work_orders(contractor.id, contractor_user.id),
                ContractorWorkFilters(),
            )
            if contractor_feed.get("context_type") != "contractor_work_queue":
                failures.append("Contractor work queue feed contract is missing its context type.")
            for key in ("assigned", "active", "submitted", "returned", "closed"):
                if key not in contractor_feed.get("queues", {}):
                    failures.append(f"Contractor work queue feed is missing the {key} queue.")

            member_links = UnitMembership.query.filter_by(
                member_id=member.id,
                is_current=True,
            ).all()
            member_context = build_member_works_context(member, member_links)
            member_feed = member_works_feed_payload(member, member_links, member_context)
            if member_feed.get("context_type") != "member_works_queue":
                failures.append("Member works feed contract is missing its context type.")
            for key in (
                "linked_units",
                "next_actions",
                "attention_queues",
                "requests",
                "open_work_orders",
                "closed_work_orders",
                "reopen_requests",
            ):
                if key not in member_feed:
                    failures.append(f"Member works feed is missing {key}.")
            if not member_feed.get("linked_units"):
                failures.append("Member works feed did not include linked units.")

            member_works_inquiry = build_gar_inquiry_response(
                "What work orders and maintenance requests need my attention?",
                role_context="member",
                company_id=company.id,
                user_id=member_user.id,
                execute_source_query=True,
            )
            member_works_result = member_works_inquiry.get("source_query_result", {})
            if member_works_result.get("context_type") != "gar_member_works_source_query":
                failures.append("GAR member inquiry did not use member-scoped Works source query.")
            if member_works_result.get("visibility", {}).get("scope") != "linked_member_units":
                failures.append("GAR member inquiry did not preserve linked-unit scope.")
            if member_works_result.get("visibility", {}).get("other_member_records_included"):
                failures.append("GAR member inquiry leaked other member records.")
            if member_works_result.get("visibility", {}).get("management_quality_records_included"):
                failures.append("GAR member inquiry leaked management quality records.")
            if work_order.id not in {
                item.get("id")
                for item in (
                    member_works_result.get("records", {}).get("open_work_orders", [])
                    + member_works_result.get("records", {}).get("closed_work_orders", [])
                )
            }:
                failures.append("GAR member inquiry did not return linked work order records.")
            member_reopen_feed_item = next(
                (
                    item
                    for item in member_feed.get("reopen_requests", [])
                    if item.get("work_order_id") == work_order.id
                ),
                None,
            )
            if not member_reopen_feed_item:
                failures.append("Member works feed did not expose the reopen request.")
            elif not member_reopen_feed_item.get("evidence_submitted"):
                failures.append("Member works feed did not expose reopen request evidence.")
            member_work_feed_items = (
                member_feed.get("open_work_orders", [])
                + member_feed.get("closed_work_orders", [])
            )
            current_member_work_item = next(
                (item for item in member_work_feed_items if item.get("id") == work_order.id),
                None,
            )
            if not current_member_work_item:
                failures.append("Member works feed did not expose the lifecycle work order.")
            elif not current_member_work_item.get("completion_evidence", {}).get("submitted"):
                failures.append("Member works feed did not expose the completion evidence signal.")
            elif not current_member_work_item.get("feedback", {}).get("evidence_submitted"):
                failures.append("Member works feed did not expose member feedback evidence.")

            ids["notifications"] = [
                item.id
                for item in Notification.query.filter(
                    Notification.recipient_id.in_(ids["users"])
                ).all()
            ]
            notifications = Notification.query.filter(Notification.id.in_(ids["notifications"])).all()
            notification_by_type = {item.type: item for item in notifications}

            expected_notification_types = {
                "works_member_request",
                "works_assignment",
                "works_completion",
                "works_completion_review",
                "works_returned",
                "works_quality_review",
                "works_member_feedback",
                "works_closed",
                "works_reopen_request",
            }
            missing_notification_types = sorted(
                expected_notification_types.difference(notification_by_type)
            )
            if missing_notification_types:
                failures.append("Missing workflow notifications: " + ", ".join(missing_notification_types))

            cover_request_notification = next(
                (
                    item for item in Notification.query.filter_by(
                        recipient_id=assistant_manager_user.id,
                        type="works_member_request",
                    ).all()
                    if (item.extracted_data or {}).get("maintenance_request_id") == maintenance_request.id
                ),
                None,
            )
            if not cover_request_notification:
                failures.append("Assistant Manager cover did not receive the member request notification.")
            elif "/assistant/work-orders" not in (cover_request_notification.link_url or ""):
                failures.append("Assistant Manager cover notification did not target the assistant work queue.")

            member_request_notification = notification_by_type.get("works_member_request")
            if member_request_notification and f"#member-request-{maintenance_request.id}" not in (member_request_notification.link_url or ""):
                failures.append("Member request notification does not target the triage row.")

            assignment_notification = notification_by_type.get("works_assignment")
            if assignment_notification and f"#work-order-{work_order.id}" not in (assignment_notification.link_url or ""):
                failures.append("Contractor assignment notification does not target the work order row.")

            completion_notification = notification_by_type.get("works_completion")
            if completion_notification and f"#work-order-{work_order.id}" not in (completion_notification.link_url or ""):
                failures.append("Member completion notification does not target the linked work order row.")

            closed_notification = notification_by_type.get("works_closed")
            if closed_notification and f"#closed-work-order-{work_order.id}" not in (closed_notification.link_url or ""):
                failures.append("Member closure notification does not target the closed work order row.")

            review_notification = notification_by_type.get("works_completion_review")
            if review_notification and "#completion-review" not in (review_notification.link_url or ""):
                failures.append("Completion review notification does not target the review section.")

            returned_notification = notification_by_type.get("works_returned")
            if returned_notification and f"#returned-work-order-{work_order.id}" not in (returned_notification.link_url or ""):
                failures.append("Returned work notification does not target the returned contractor row.")

            quality_notification = notification_by_type.get("works_quality_review")
            if quality_notification:
                if "repeated-returns" not in (quality_notification.link_url or ""):
                    failures.append("Quality review notification does not target the repeated returns queue.")
                if (quality_notification.extracted_data or {}).get("return_count", 0) < 2:
                    failures.append("Quality review notification did not include the repeated return count.")
                if (quality_notification.extracted_data or {}).get("gar_signal") != "repeated_completion_returns":
                    failures.append("Quality review notification did not include the GAR repeated return signal.")

            feedback_notification = notification_by_type.get("works_member_feedback")
            if feedback_notification and "#member-feedback" not in (feedback_notification.link_url or ""):
                failures.append("Member feedback notification does not target the feedback section.")

            reopen_notification = notification_by_type.get("works_reopen_request")
            if reopen_notification and "#reopen-review" not in (reopen_notification.link_url or ""):
                failures.append("Reopen request notification does not target the reopen review section.")

            notification_views = build_notification_views(notifications)
            action_notification_types = {
                item["notification"].type
                for item in notification_views
                if item["is_action_required"]
            }
            if not {"works_assignment", "works_completion_review", "works_member_feedback", "works_quality_review"}.issubset(action_notification_types):
                failures.append("Notification intelligence did not classify core workflow actions correctly.")
            stage_by_type = {
                item["notification"].type: item.get("workflow_stage")
                for item in notification_views
            }
            expected_stages = {
                "works_member_request": "Member Request",
                "works_assignment": "Contractor Assigned",
                "works_completion": "Completion Submitted",
                "works_completion_review": "PM Review",
                "works_returned": "Returned",
                "works_quality_review": "Quality Review",
                "works_member_feedback": "Member Feedback",
                "works_reopen_request": "Reopen Requested",
                "works_closed": "Closed",
            }
            missing_stages = [
                f"{notification_type} -> {stage}"
                for notification_type, stage in expected_stages.items()
                if stage_by_type.get(notification_type) != stage
            ]
            if missing_stages:
                failures.append("Notification intelligence missed workflow stages: " + ", ".join(missing_stages))
            source_by_type = {
                item["notification"].type: item.get("source_reference", {})
                for item in notification_views
            }
            expected_notification_sources = {
                "works_member_request": ("MaintenanceRequest", maintenance_request.id),
                "works_assignment": ("WorkOrder", work_order.id),
                "works_completion": ("WorkOrder", work_order.id),
                "works_completion_review": ("WorkOrder", work_order.id),
                "works_returned": ("WorkOrder", work_order.id),
                "works_quality_review": ("WorkOrder", work_order.id),
                "works_member_feedback": ("WorkOrder", work_order.id),
                "works_reopen_request": ("WorkOrder", work_order.id),
                "works_closed": ("WorkOrder", work_order.id),
            }
            missing_sources = [
                f"{notification_type} -> {model} #{record_id}"
                for notification_type, (model, record_id) in expected_notification_sources.items()
                if (
                    source_by_type.get(notification_type, {}).get("model") != model
                    or source_by_type.get(notification_type, {}).get("record_id") != record_id
                    or not source_by_type.get(notification_type, {}).get("label")
                )
            ]
            if missing_sources:
                failures.append("Notification intelligence missed workflow source references: " + ", ".join(missing_sources))
            stage_counts = notification_summary(notification_views).get("stage_counts", {})
            for stage in ("Member Request", "Contractor Assigned", "PM Review", "Quality Review", "Reopen Requested"):
                if stage_counts.get(stage, 0) < 1:
                    failures.append(f"Notification summary did not count the {stage} stage.")

            notification_feed_context = build_notification_context(
                admin_user.id,
                NotificationFilters(status="all"),
                limit=100,
            )
            notification_feed = notification_feed_payload(notification_feed_context)
            if notification_feed.get("context_type") != "notification_queue":
                failures.append("Notification feed contract is missing its context type.")
            if not notification_feed.get("notifications"):
                failures.append("Notification feed did not include user notifications.")
            for key in ("unread_count", "read_count", "all_count", "action_count", "module_counts", "stage_counts"):
                if key not in notification_feed.get("summary", {}):
                    failures.append(f"Notification feed summary is missing {key}.")
            if "filters" not in notification_feed:
                failures.append("Notification feed did not include applied filters.")

        except Exception as exc:
            if not failures:
                failures.append(str(exc))
        finally:
            db.session.rollback()

            ids["notifications"] = [
                item.id
                for item in Notification.query.filter(
                    Notification.recipient_id.in_(ids["users"])
                ).all()
            ]
            _delete_by_ids(Notification, ids["notifications"])
            db.session.flush()

            WorkOrderLifecycleEvent.query.filter(
                WorkOrderLifecycleEvent.work_order_id.in_(ids["work_orders"])
            ).delete(synchronize_session=False)
            _delete_by_ids(WorkOrderReopenRequest, [
                item.id
                for item in WorkOrderReopenRequest.query.filter(
                    WorkOrderReopenRequest.work_order_id.in_(ids["work_orders"])
                ).all()
            ])
            _delete_by_ids(ContractorFeedback, [
                item.id
                for item in ContractorFeedback.query.filter(
                    ContractorFeedback.work_order_id.in_(ids["work_orders"])
                ).all()
            ])
            _delete_by_ids(WorkOrderCompletion, [
                item.id
                for item in WorkOrderCompletion.query.filter(
                    WorkOrderCompletion.work_order_id.in_(ids["work_orders"])
                ).all()
            ])
            _delete_by_ids(WorkOrder, ids["work_orders"])
            _delete_by_ids(MaintenanceRequest, ids["maintenance_requests"])
            _delete_by_ids(UnitMembership, ids["unit_memberships"])
            _delete_by_ids(Member, ids["members"])
            _delete_by_ids(Unit, ids["units"])
            _delete_by_ids(Contractor, ids["contractors"])
            _delete_by_ids(Client, ids["clients"])
            _delete_by_ids(User, ids["users"])
            if created_role_ids:
                Role.query.filter(Role.id.in_(created_role_ids)).delete(synchronize_session=False)
            _delete_by_ids(Company, ids["companies"])
            db.session.commit()

    print("Works lifecycle flow check")
    print(f"- Temporary marker: {marker}")
    print("- Flow exercised: Members -> Assistant/Works -> Contractor -> Feedback -> Review -> Reopen")

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
