from datetime import date
from typing import Optional, Dict
from app.models.onboarding import CompanyLicense

def find_applicable_license(company_id: int, country: str, region: str | None = None) -> Optional[CompanyLicense]:
    today = date.today()
    q = (CompanyLicense.query
         .filter(CompanyLicense.company_id == company_id,
                 CompanyLicense.active.is_(True),
                 (CompanyLicense.status == "active"),
                 (CompanyLicense.expiry_date.is_(None)) | (CompanyLicense.expiry_date >= today)))

    # Prefer exact (country+region) defaults, then any non-default active in that region,
    # then fall back to country-only default/active.
    if region:
        best = q.filter_by(country=country, region=region, is_default=True).first()
        if best:
            return best
        any_reg = (q.filter_by(country=country, region=region)
                     .order_by(CompanyLicense.is_default.desc(), CompanyLicense.expiry_date.asc().nullsfirst())
                     .first())
        if any_reg:
            return any_reg

    # Country-only fallback
    best_country = q.filter_by(country=country, region=None, is_default=True).first()
    if best_country:
        return best_country

    any_country = (q.filter_by(country=country, region=None)
                     .order_by(CompanyLicense.is_default.desc(), CompanyLicense.expiry_date.asc().nullsfirst())
                     .first())
    return any_country

def build_license_block(company_id: int, country: str, region: str | None = None) -> Dict | None:
    lic = find_applicable_license(company_id, country, region)
    if not lic:
        return None
    return {
        "regulator": lic.regulator_name,
        "license_type": lic.license_type,
        "license_number": lic.license_number,
        "jurisdiction": {
            "country": lic.country,
            "region": lic.region,
            "city": lic.city,
        },
        "valid_from": lic.valid_from.isoformat() if lic.valid_from else None,
        "expiry_date": lic.expiry_date.isoformat() if lic.expiry_date else None,
        "status": lic.status,
        "document_path": lic.document_path,
    }
