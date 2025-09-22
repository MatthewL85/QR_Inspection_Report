from typing import Dict
from app.models.onboarding import Company
from app.services.banking import build_bank_block
from app.services.insurance import build_insurance_block
from app.services.licenses import build_license_block

def build_issuer_defaults_for_contract(company: Company, client_country: str | None, client_region: str | None) -> Dict:
    return {
        "issuer_name": company.name,
        "issuer_registration_number": company.registration_number,
        "issuer_vat_number": company.vat_number,
        "issuer_tax_identifier": company.tax_identifier,
        "issuer_type": company.company_type,
        "issuer_industry": company.industry,
        "issuer_contact": {
            "email": company.email,
            "phone": company.phone,
            "website": company.website,
        },
        "issuer_address": {
            "line1": company.address_line1,
            "line2": company.address_line2,
            "city": company.city,
            "state": company.state,
            "postal_code": company.postal_code,
            "country": company.country,
        },
        "issuer_brand": {
            "primary_color": company.theme_primary,
            "secondary_color": company.theme_secondary,
            "logo_path": company.logo_path,
        },
        "issuer_bank": build_bank_block("company", company.id),
        "issuer_insurance": build_insurance_block(company.id),  # ← list of active policies
        "issuer_emergency_contacts": build_emergency_block(company.id),   # 👈 NEWCold
        "issuer_license": build_license_block(company.id, client_country or company.country, client_region),
    }

