from datetime import datetime

from app.extensions import db


class WorkOrderProgressUpdate(db.Model):
    __tablename__ = "work_order_progress_updates"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id"), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=True, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=True, index=True)
    contractor_id = db.Column(db.Integer, db.ForeignKey("contractors.id"), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    visibility_scope = db.Column(db.String(40), nullable=False, default="management")
    update_type = db.Column(db.String(40), nullable=False, default="progress")
    note = db.Column(db.Text, nullable=False)
    evidence_links = db.Column(db.JSON, nullable=True)
    attachments_count = db.Column(db.Integer, nullable=False, default=0)
    source_module = db.Column(db.String(80), nullable=False, default="Contractor Logix")

    gar_chat_ready = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    work_order = db.relationship("WorkOrder", back_populates="progress_updates")
    company = db.relationship("Company")
    client = db.relationship("Client")
    unit = db.relationship("Unit")
    contractor = db.relationship("Contractor")
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    __table_args__ = (
        db.Index("ix_work_order_progress_work_order_created", "work_order_id", "created_at"),
    )

    @property
    def visibility_label(self) -> str:
        labels = {
            "contractor_internal": "Contractor Only",
            "management": "Contractor + Management",
            "reporter_visible": "All Parties",
        }
        return labels.get(self.visibility_scope or "", "Contractor + Management")

    @property
    def update_type_label(self) -> str:
        labels = {
            "progress": "Progress Update",
            "completion": "Completion",
        }
        return labels.get(self.update_type or "", "Progress Update")

    def __repr__(self):
        return f"<WorkOrderProgressUpdate work_order_id={self.work_order_id} type={self.update_type} visibility={self.visibility_scope}>"
