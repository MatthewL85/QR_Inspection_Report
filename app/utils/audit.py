from app.extensions import db
from app.models.audit import ProfileChangeLog
from flask_login import current_user
from datetime import datetime


def log_profile_change(
    user_id,
    field_name,
    old_value,
    new_value,
    changed_by=None,
    change_reason=None,
    parsed_summary=None
):
    """
    🔐 Logs a profile field change into ProfileChangeLog.

    Parameters:
    - user_id: ID of the user whose profile was changed
    - field_name: Field name that was changed
    - old_value: Previous value
    - new_value: New value
    - changed_by: (Optional) User ID of the actor making the change. Defaults to current_user.id
    - change_reason: (Optional) Reason for the change (manual or AI-generated)
    - parsed_summary: (Optional) AI summary of the change for GAR visibility

    Skips logging if the value did not change.
    """

    if old_value == new_value:
        return  # Skip logging unchanged values

    try:
        actor_id = changed_by or (getattr(current_user, 'id', None))

        log = ProfileChangeLog(
            user_id=user_id,
            changed_by=actor_id,
            field_name=field_name,
            old_value='' if old_value is None else str(old_value),
            new_value='' if new_value is None else str(new_value),
            change_reason=change_reason,
            parsed_summary=parsed_summary,
            timestamp=datetime.utcnow()
        )

        db.session.add(log)
        db.session.commit()

        print(f"🔍 Profile change logged: {field_name} from '{old_value}' to '{new_value}' for user {user_id}")

    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Error logging profile change for user {user_id}: {e}")

def log_change(user, field, old, new):
    if str(old) != str(new):
        db.session.add(ProfileChangeLog(
            user_id=user.id,
            changed_by=current_user.id,
            field_name=field,
            old_value=str(old),
            new_value=str(new)
        ))