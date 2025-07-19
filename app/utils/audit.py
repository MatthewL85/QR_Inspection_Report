from app.models.audit.audit_log import log_audit_change
from app.models import db, ProfileChangeLog
from flask_login import current_user
from datetime import datetime


def log_profile_change(user_id, field_name, old_value, new_value, changed_by=None):
    if old_value == new_value:
        return  # Skip unchanged fields

    log = ProfileChangeLog(
        user_id=user_id,
        changed_by=changed_by or current_user.id,
        field_name=field_name,
        old_value=str(old_value) if old_value else '',
        new_value=str(new_value) if new_value else '',
        timestamp=datetime.utcnow()
    )
    db.session.add(log)
