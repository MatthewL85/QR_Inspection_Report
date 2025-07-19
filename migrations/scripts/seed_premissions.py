# scripts/seed_permissions.py

from app.extensions import db
from app.models.core.role import Role
from app.models.core.role_permission import RolePermission
from app import create_app

def seed_permissions():
    app = create_app()
    with app.app_context():
        permissions_by_role = {
            'Super Admin': [
                'manage_users',
                'manage_clients',
                'view_all_data',
                'view_audit_logs',
                'manage_compliance',
                'view_financials',
                'assign_roles',
                'access_all_dashboards'
            ],
            'Admin': [
                'manage_clients',
                'view_all_data',
                'assign_property_managers',
                'create_work_orders',
                'view_reports'
            ],
            'Property Manager': [
                'view_assigned_clients',
                'create_work_orders',
                'view_work_orders',
                'upload_documents',
                'respond_to_capex'
            ],
            'Contractor': [
                'view_assigned_work_orders',
                'complete_work_orders',
                'upload_compliance_docs',
                'submit_invoices'
            ],
            'Director': [
                'view_site_summary',
                'review_capex',
                'vote_capex',
                'view_compliance_docs'
            ],
            'Resident': [
                'submit_request',
                'view_unit_docs',
                'view_issue_status'
            ],
            'Owner': [
                'submit_request',
                'view_account_balance',
                'download_documents'
            ]
        }

        created_count = 0
        for role_name, permissions in permissions_by_role.items():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                print(f"⚠️ Role '{role_name}' not found. Skipping...")
                continue

            for perm in permissions:
                exists = RolePermission.query.filter_by(role_id=role.id, permission=perm).first()
                if not exists:
                    db.session.add(RolePermission(role_id=role.id, permission=perm))
                    created_count += 1

        if created_count:
            db.session.commit()
            print(f"✅ Seeded {created_count} role permissions.")
        else:
            print("ℹ️ No new permissions added.")

if __name__ == "__main__":
    seed_permissions()

