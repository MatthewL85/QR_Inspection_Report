from app.models import db
from app.models.hr.hr_profile import HRProfile
from app.models.hr.hr_settings import HRSettings
from app.models.onboarding.company import Company


def _truthy_setting(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "enabled", "active", "on"}
    return bool(value)


def company_uses_logix_hr(company_id):
    if not company_id:
        return False

    if HRSettings.query.filter_by(company_id=company_id).first():
        return True

    company = Company.query.get(company_id)
    if not company:
        return False

    settings = company.default_settings or {}
    integrations = company.integrations or {}
    keys = ("logix_hr", "logix_hr_enabled", "hr_enabled", "uses_logix_hr")

    for source in (settings, integrations):
        if not isinstance(source, dict):
            continue
        for key in keys:
            if key in source and _truthy_setting(source.get(key)):
                return True

    return False


def ensure_hr_profile_for_user(user):
    """Create the HR shell profile when the user's company has Logix HR enabled."""
    if not user or not user.id or not company_uses_logix_hr(user.company_id):
        return None

    existing = HRProfile.query.filter_by(user_id=user.id).first()
    if existing:
        return existing

    profile = HRProfile(
        user_id=user.id,
        job_title=user.role.name if user.role else None,
        employment_status="Active" if user.is_active else "Inactive",
        visibility_scope="Admin,HR",
        source_system="LogixPM User Manager",
        sync_status="Pending",
        is_private=True,
        requires_hr_review=True,
        gar_chat_ready=False,
    )
    db.session.add(profile)
    return profile
