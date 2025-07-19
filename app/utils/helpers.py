# app/utils/helpers.py

def role_name_to_dashboard_route(role_name):
    mapping = {
        'Super Admin': 'super_admin.dashboard',
        'Admin': 'super_admin.dashboard',
        'Property Manager': 'property_manager.dashboard',
        'Contractor': 'contractor.dashboard',
        'Director': 'director.dashboard',
    }
    return mapping.get(role_name, 'main.index')
