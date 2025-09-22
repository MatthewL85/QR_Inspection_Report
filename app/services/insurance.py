from datetime import date
from typing import List, Optional, Dict
from app.models.onboarding import InsurancePolicy

def get_active_policies(company_id: int) -> List[InsurancePolicy]:
    today = date.today()
    return (InsurancePolicy.query
            .filter(
                InsurancePolicy.company_id == company_id,
                InsurancePolicy.active.is_(True),
                (InsurancePolicy.expiry_date.is_(None)) | (InsurancePolicy.expiry_date >= today)
            )
            .order_by(InsurancePolicy.policy_type.asc(), InsurancePolicy.is_default.desc(), InsurancePolicy.expiry_date.asc())
            .all())

def get_default_policy(company_id: int, policy_type: str) -> Optional[InsurancePolicy]:
    return (InsurancePolicy.query
            .filter_by(company_id=company_id, policy_type=policy_type, is_default=True, active=True)
            .first())

def build_insurance_block(company_id: int) -> List[Dict]:
    """
    Returns a list of active policies for embedding into documents (contracts/quotes).
    """
    blocks = []
    for p in get_active_policies(company_id):
        blocks.append({
            "type": p.policy_type,
            "provider": p.provider,
            "policy_number": p.policy_number,
            "coverage_amount": str(p.coverage_amount) if p.coverage_amount is not None else None,
            "currency": p.currency,
            "start_date": p.start_date.isoformat() if p.start_date else None,
            "expiry_date": p.expiry_date.isoformat() if p.expiry_date else None,
            "document_path": p.document_path,
        })
    return blocks
