from datetime import datetime
from typing import Optional

from app.extensions import db
from app.models.members.unit import Unit
from app.models.works.work_order import WorkOrder
from app.models.works.work_order_lifecycle_event import WorkOrderLifecycleEvent
from app.models.works.work_order_reopen_request import WorkOrderReopenRequest


class WorkOrderReopenService:
    @staticmethod
    def _add_lifecycle_event(
        *,
        work_order: WorkOrder,
        event_type: str,
        title: str,
        source_module: str,
        note: str = "",
        actor_user_id: Optional[int] = None,
        member_id: Optional[int] = None,
        status_snapshot: str = "",
        metadata: Optional[dict] = None,
    ) -> None:
        db.session.add(
            WorkOrderLifecycleEvent(
                work_order_id=work_order.id,
                company_id=work_order.company_id,
                client_id=work_order.client_id,
                unit_id=work_order.unit_id,
                contractor_id=work_order.contractor_id,
                member_id=member_id,
                actor_user_id=actor_user_id,
                source_module=source_module,
                event_type=event_type,
                title=title,
                note=note,
                status_snapshot=status_snapshot or work_order.status,
                event_metadata=metadata,
                gar_context_reference=f"WorkOrder#{work_order.id}",
            )
        )

    @staticmethod
    def get_request(request_id: int, company_id: int) -> Optional[WorkOrderReopenRequest]:
        return (
            WorkOrderReopenRequest.query.join(WorkOrder)
            .join(Unit, WorkOrder.unit_id == Unit.id)
            .filter(
                WorkOrderReopenRequest.id == request_id,
                Unit.company_id == company_id,
            )
            .first()
        )

    @staticmethod
    def get_pending_for_unit(unit_id: int, company_id: int):
        return (
            WorkOrderReopenRequest.query.join(WorkOrder)
            .join(Unit, WorkOrder.unit_id == Unit.id)
            .filter(
                WorkOrderReopenRequest.unit_id == unit_id,
                WorkOrderReopenRequest.status == "Pending",
                Unit.company_id == company_id,
            )
            .order_by(WorkOrderReopenRequest.created_at.desc())
            .all()
        )

    @staticmethod
    def create_request(
        work_order: WorkOrder,
        reason: str,
        additional_details: str = "",
        evidence_reference: str = "",
        requested_by_member_id: Optional[int] = None,
    ) -> WorkOrderReopenRequest:
        request = WorkOrderReopenRequest(
            work_order_id=work_order.id,
            unit_id=work_order.unit_id,
            requested_by_member_id=requested_by_member_id,
            reason=reason,
            additional_details=additional_details,
            evidence_reference=evidence_reference or None,
            status="Pending",
        )
        db.session.add(request)
        WorkOrderReopenService._add_lifecycle_event(
            work_order=work_order,
            event_type="reopen_requested",
            title="Reopen requested",
            source_module="Members Logix",
            note=reason or additional_details,
            member_id=requested_by_member_id,
            status_snapshot=request.status,
            metadata={
                "additional_details": additional_details or None,
                "evidence_reference": evidence_reference or None,
                "evidence_submitted": bool(evidence_reference),
            },
        )
        db.session.commit()
        return request

    @staticmethod
    def approve_request(request_id: int, company_id: int, reviewed_by_user_id: int, review_notes: str = "") -> bool:
        request = WorkOrderReopenService.get_request(request_id, company_id)
        if not request or request.status != "Pending":
            return False

        request.status = "Approved"
        request.reviewed_by_user_id = reviewed_by_user_id
        request.reviewed_at = datetime.utcnow()
        request.review_notes = review_notes
        request.work_order.status = "Open"
        WorkOrderReopenService._add_lifecycle_event(
            work_order=request.work_order,
            event_type="reopen_approved",
            title="Reopen request approved",
            source_module="Works Logix",
            note=review_notes or "Reopen request approved and work order reopened.",
            actor_user_id=reviewed_by_user_id,
            member_id=request.requested_by_member_id,
            status_snapshot=request.work_order.status,
            metadata={"reopen_request_id": request.id},
        )
        db.session.commit()
        return True

    @staticmethod
    def reject_request(request_id: int, company_id: int, reviewed_by_user_id: int, review_notes: str = "") -> bool:
        request = WorkOrderReopenService.get_request(request_id, company_id)
        if not request or request.status != "Pending":
            return False

        request.status = "Rejected"
        request.reviewed_by_user_id = reviewed_by_user_id
        request.reviewed_at = datetime.utcnow()
        request.review_notes = review_notes
        WorkOrderReopenService._add_lifecycle_event(
            work_order=request.work_order,
            event_type="reopen_rejected",
            title="Reopen request rejected",
            source_module="Works Logix",
            note=review_notes or "Reopen request rejected after review.",
            actor_user_id=reviewed_by_user_id,
            member_id=request.requested_by_member_id,
            status_snapshot=request.work_order.status,
            metadata={"reopen_request_id": request.id},
        )
        db.session.commit()
        return True
