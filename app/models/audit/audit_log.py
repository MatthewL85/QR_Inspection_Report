from flask_login import current_user
from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.inspection import inspect

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 📌 Entity Context
    entity_type = db.Column(db.String(100), nullable=False)      # 'User', 'Invoice', 'WorkOrder'
    entity_id = db.Column(db.Integer, nullable=False)            # ID of the affected record
    action = db.Column(db.String(100), nullable=False)           # 'created', 'updated', 'deleted', etc.

    # 👤 User + Org Context
    performed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)

    # 📝 Detailed Changes
    field_changes = db.Column(JSONB, nullable=True)              # {"field": {"old": val1, "new": val2}}
    reason = db.Column(db.String(255), nullable=True)            # Optional justification (e.g., salary change)

    # 🧠 AI & GAR Integration
    gar_flagged = db.Column(db.Boolean, default=False)
    gar_notes = db.Column(db.Text, nullable=True)                # Why GAR flagged the change
    gar_context_reference = db.Column(db.String(100), nullable=True)  # e.g. "WorkOrder#1543"
    ai_explanation = db.Column(db.Text, nullable=True)           # GAR rationale or narrative
    gar_chat_ready = db.Column(db.Boolean, default=False)        # Exposed for GAR querying
    gar_feedback = db.Column(db.Text, nullable=True)             # Optional human comment on AI flag

    # 🌍 External / Integration Source
    integration_source = db.Column(db.String(100), nullable=True)    # e.g., "QuickBooks", "Stripe"
    external_reference_id = db.Column(db.String(100), nullable=True)

    # ⏱ Timestamping
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔁 Relationships
    performed_by = db.relationship("User", foreign_keys=[performed_by_id])
    client = db.relationship("Client", backref="audit_logs")
    company = db.relationship("Company", backref="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.entity_type}:{self.entity_id} action={self.action} at {self.timestamp}>"


# ✅ Global audit logger function
def log_audit_change(
    entity_type,
    entity_id,
    action,
    old_obj=None,
    new_obj=None,
    fields_to_track=None,
    reason=None,
    gar_flagged=False,
    gar_notes=None,
    gar_context_reference=None,
    ai_explanation=None,
    gar_chat_ready=False,
    gar_feedback=None,
    integration_source=None,
    external_reference_id=None,
    client_id=None,
    company_id=None,
    performed_by_id=None,
):
    """
    Logs a detailed audit event with optional field tracking, GAR reasoning, and source context.
    """
    field_changes = {}

    if old_obj and new_obj:
        tracked_fields = fields_to_track or [
            c.key for c in inspect(new_obj.__class__).mapper.column_attrs
        ]
        for field in tracked_fields:
            old_val = getattr(old_obj, field, None)
            new_val = getattr(new_obj, field, None)
            if old_val != new_val:
                field_changes[field] = {
                    "old": str(old_val) if old_val is not None else None,
                    "new": str(new_val) if new_val is not None else None
                }

    log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        field_changes=field_changes if field_changes else None,
        reason=reason,
        gar_flagged=gar_flagged,
        gar_notes=gar_notes,
        gar_context_reference=gar_context_reference,
        ai_explanation=ai_explanation,
        gar_chat_ready=gar_chat_ready,
        gar_feedback=gar_feedback,
        integration_source=integration_source,
        external_reference_id=external_reference_id,
        client_id=client_id,
        company_id=company_id,
        performed_by_id=performed_by_id or getattr(current_user, "id", None),
        timestamp=datetime.utcnow()
    )

    db.session.add(log)
    db.session.commit()
