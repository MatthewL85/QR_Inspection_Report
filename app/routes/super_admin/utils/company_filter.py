# app/routes/super_admin/utils/company_filter.py

from flask import Blueprint, jsonify, request
from app.models.onboarding.company import Company
from app.decorators.role import super_admin_required
from flask_login import login_required

company_filter_bp = Blueprint('company_filter', __name__)

@company_filter_bp.route('/filter-companies', methods=['POST'])
@login_required
@super_admin_required
def filter_companies():
    role_id = request.json.get('role_id')

    if not role_id:
        return jsonify({'error': 'Role ID is required'}), 400

    # You may want to customize this mapping
    if int(role_id) == 5:  # Contractor
        companies = Company.query.filter(Company.company_type == 'Contractor').all()
    else:  # Property Management, Admins, etc.
        companies = Company.query.filter(Company.company_type == 'Property Management').all()

    company_options = [{'id': c.id, 'name': c.name} for c in companies]
    return jsonify(company_options)
