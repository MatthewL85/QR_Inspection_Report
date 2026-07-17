from datetime import datetime

from app.extensions import db


class WorkOrderReopenRequest(db.Model):
    __tablename__ = "work_order_reopen_requests"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id"), nullable=False, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=False, index=True)
    requested_by_member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=True, index=True)

    reason = db.Column(db.String(255), nullable=True)
    additional_details = db.Column(db.Text, nullable=True)
    evidence_reference = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default="Pending", nullable=False, index=True)

    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    work_order = db.relationship("WorkOrder", back_populates="reopen_requests")
    unit = db.relationship("Unit", backref="work_order_reopen_requests")
    requested_by_member = db.relationship("Member", backref="work_order_reopen_requests")
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_user_id])

    @property
    def is_pending(self) -> bool:
        return self.status == "Pending"
