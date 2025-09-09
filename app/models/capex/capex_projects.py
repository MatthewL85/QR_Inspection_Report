# app/models/capex.py
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

# One row per CAPEX project
class CapexProject(db.Model):
    __tablename__ = "capex_projects"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)

    name = db.Column(db.String(200), nullable=False)
    target_year = db.Column(db.Integer, nullable=True)
    cost = db.Column(db.Numeric(14, 2), nullable=True)

    priority = db.Column(db.String(10), nullable=False, server_default="Medium")   # High/Medium/Low
    funding = db.Column(db.String(20), nullable=False, server_default="Reserve Fund")  # Reserve Fund/Special Levy/Insurance/Other
    status = db.Column(db.String(20), nullable=False, server_default="Planned")    # Planned/Approved/In Tender/In Progress/Done/Deferred

    notes = db.Column(db.Text, nullable=True)

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    client = db.relationship("Client", backref=db.backref("capex_projects", cascade="all, delete-orphan", lazy="dynamic"))

# Self‑referential many‑to‑many for dependencies (project A depends on B)
class CapexProjectDependency(db.Model):
    __tablename__ = "capex_project_dependencies"
    parent_id = db.Column(UUID(as_uuid=True), db.ForeignKey("capex_projects.id", ondelete="CASCADE"), primary_key=True)
    child_id  = db.Column(UUID(as_uuid=True), db.ForeignKey("capex_projects.id", ondelete="CASCADE"), primary_key=True)
