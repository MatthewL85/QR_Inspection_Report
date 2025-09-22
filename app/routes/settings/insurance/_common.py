from flask_login import current_user
from app.models.onboarding import InsurancePolicy

def current_company_id() -> int:
    return current_user.company_id

def get_policy_or_404(policy_id: int) -> InsurancePolicy:
    return (InsurancePolicy.query
            .filter_by(company_id=current_company_id(), id=policy_id)
            .first_or_404())

def clear_other_defaults(policy_type: str, exclude_id: int | None = None):
    q = (InsurancePolicy.query
         .filter(InsurancePolicy.company_id == current_company_id(),
                 InsurancePolicy.policy_type == policy_type,
                 InsurancePolicy.is_default.is_(True)))
    if exclude_id:
        q = q.filter(InsurancePolicy.id != exclude_id)
    q.update({"is_default": False})
