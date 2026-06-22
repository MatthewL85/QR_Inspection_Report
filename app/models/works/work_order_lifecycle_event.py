from datetime import datetime

from app.extensions import db


class WorkOrderLifecycleEvent(db.Model):
    __tablename__ = "work_order_lifecycle_events"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id"), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=True, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=True, index=True)
    contractor_id = db.Column(db.Integer, db.ForeignKey("contractors.id"), nullable=True, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=True, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    source_module = db.Column(db.String(80), nullable=False, default="Works Logix")
    event_type = db.Column(db.String(80), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    note = db.Column(db.Text, nullable=True)
    status_snapshot = db.Column(db.String(50), nullable=True)
    actor_label = db.Column(db.String(160), nullable=True)
    visibility_scope = db.Column(db.String(100), nullable=False, default="Admin,PM,GAR")
    event_metadata = db.Column(db.JSON, nullable=True)

    gar_context_reference = db.Column(db.String(120), nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=True, nullable=False)
    occurred_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    work_order = db.relationship("WorkOrder", back_populates="lifecycle_events")
    company = db.relationship("Company")
    client = db.relationship("Client")
    unit = db.relationship("Unit")
    contractor = db.relationship("Contractor")
    member = db.relationship("Member")
    actor_user = db.relationship("User", foreign_keys=[actor_user_id])

    __table_args__ = (
        db.Index("ix_work_order_lifecycle_work_order_occurred", "work_order_id", "occurred_at"),
    )

    def as_timeline_event(self) -> dict:
        metadata = self.event_metadata or {}
        return {
            "title": self.title,
            "source": self.source_module,
            "occurred_at": self.occurred_at,
            "actor": self.actor_label or (self.actor_user.full_name if self.actor_user else "-"),
            "note": self.note or "-",
            "status": self.status_snapshot or "",
            "event_type": self.event_type,
            "access_context": metadata.get("access_context") or "",
            "persisted": True,
        }
