from flask_login import current_user
from app.models.onboarding import EmergencyContact

def current_company_id() -> int:
    return current_user.company_id

def get_contact_or_404(contact_id: int) -> EmergencyContact:
    return (EmergencyContact.query
            .filter_by(company_id=current_company_id(), id=contact_id)
            .first_or_404())

def clear_other_defaults(service_type: str, exclude_id: int | None = None):
    q = (EmergencyContact.query
         .filter(EmergencyContact.company_id == current_company_id(),
                 EmergencyContact.service_type == service_type,
                 EmergencyContact.is_default.is_(True)))
    if exclude_id:
        q = q.filter(EmergencyContact.id != exclude_id)
    q.update({"is_default": False})
