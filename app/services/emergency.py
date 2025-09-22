from datetime import date
from typing import List, Dict
from app.models.onboarding import EmergencyContact

def get_active_emergency_contacts(company_id: int, service_type: str | None = None) -> List[EmergencyContact]:
    q = (EmergencyContact.query
         .filter(EmergencyContact.company_id == company_id,
                 EmergencyContact.active.is_(True)))
    today = date.today()
    # Validity window (optional)
    q = q.filter(
        (EmergencyContact.valid_from.is_(None)) | (EmergencyContact.valid_from <= today),
        (EmergencyContact.valid_to.is_(None))   | (EmergencyContact.valid_to >= today),
    )
    if service_type:
        q = q.filter(EmergencyContact.service_type == service_type)
    return q.order_by(EmergencyContact.service_type.asc(),
                      EmergencyContact.priority.asc(),
                      EmergencyContact.is_default.desc()).all()

def build_emergency_block(company_id: int) -> List[Dict]:
    """
    Returns a list of emergency contacts (ordered) for embedding into contracts/quotes.
    Grouping by service_type can be done in the template if desired.
    """
    rows = get_active_emergency_contacts(company_id)
    block: List[Dict] = []
    for r in rows:
        block.append({
            "label": r.label,
            "service_type": r.service_type,
            "provider": r.provider,
            "phone": r.phone,
            "alt_phone": r.alt_phone,
            "email": r.email,
            "coverage": r.coverage,           # e.g., '24x7', 'weeknights', 'custom'
            "days_of_week": r.days_of_week,   # for 'custom'
            "start_time": r.start_time.isoformat() if r.start_time else None,
            "end_time": r.end_time.isoformat() if r.end_time else None,
            "priority": r.priority,
            "is_default": r.is_default,
            "notes": r.notes,
        })
    return block
