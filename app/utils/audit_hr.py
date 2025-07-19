# app/utils/audit_hr.py

from app.models.hr_audit_log import HRAuditLog
from app.extensions import db
from datetime import datetime

def log_hr_change(actor_id, module, record_id, action, field_changed=None,
                  previous_value=None, new_value=None,
                  target_user_id=None, notes=None,
                  ai_flags=None, gar_risk_score=None):
    """
    Manually log a change in any HR module with GAR/AI overlay.
    """
    audit_entry = HRAuditLog(
        actor_id=actor_id,
        target_user_id=target_user_id,
        action=action,
        module=module,
        record_id=record_id,
        field_changed=field_changed,
        previous_value=str(previous_value) if previous_value else None,
        new_value=str(new_value) if new_value else None,
        notes=notes,
        ai_flags=ai_flags,
        gar_risk_score=gar_risk_score,
        is_ai_processed=True if ai_flags or gar_risk_score else False,
        timestamp=datetime.utcnow()
    )
    db.session.add(audit_entry)
    db.session.commit()
