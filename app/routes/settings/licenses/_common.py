from flask_login import current_user
from app.models.onboarding import CompanyLicense

def current_company_id() -> int:
    return current_user.company_id

def get_license_or_404(license_id: int) -> CompanyLicense:
    return (CompanyLicense.query
            .filter_by(company_id=current_company_id(), id=license_id)
            .first_or_404())

def clear_other_defaults(country: str, region: str | None, exclude_id: int | None = None):
    q = (CompanyLicense.query
         .filter(CompanyLicense.company_id == current_company_id(),
                 CompanyLicense.country == country,
                 (CompanyLicense.region.is_(None) if region is None else CompanyLicense.region == region),
                 CompanyLicense.is_default.is_(True)))
    if exclude_id:
        q = q.filter(CompanyLicense.id != exclude_id)
    q.update({"is_default": False})
