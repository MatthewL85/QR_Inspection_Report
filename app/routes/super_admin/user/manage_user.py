# 📍 app/routes/super_admin/user/manage_user.py

from flask import render_template, redirect, url_for, flash, request, Response
from flask_login import login_required
from io import StringIO
import csv

from app.models.core.user import User
from app.models.core.role import Role
from app.models.onboarding.company import Company   # ✅ use the core Company model
from app.extensions import db
from app.routes.super_admin import super_admin_bp

from app.decorators.role import super_admin_required
from app.decorators.permissions import has_permission


@super_admin_bp.route('/users', endpoint='manage_users')
@login_required
@super_admin_required
@has_permission('manage_users')
def manage_users():
    """👥 Super Admin view for managing users with filters, search, and pagination."""

    search = request.args.get('search', '').strip().lower()
    role_filter = request.args.get('role_filter', '').strip()
    company_filter = request.args.get('company_filter', '').strip()
    sort_by = request.args.get('sort_by', 'full_name')
    sort_dir = request.args.get('sort_dir', 'asc')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Allowed sorting fields
    valid_fields = {
        'email': User.email,
        'full_name': User.full_name,
        'company': Company.name,
        'role': Role.name,
    }

    sort_column = valid_fields.get(sort_by, User.full_name)
    sort_order = sort_column.asc() if sort_dir == 'asc' else sort_column.desc()

    # ✅ EXPLICIT, NON-AMBIGUOUS JOINS
    base_query = (
        User.query
        .outerjoin(Role, User.role_id == Role.id)               # keep users with no role
        .outerjoin(Company, User.company_id == Company.id)      # keep users with no company
        .order_by(sort_order)
    )

    if search:
        base_query = base_query.filter(
            (User.email.ilike(f'%{search}%')) |
            (User.full_name.ilike(f'%{search}%')) |
            (User.username.ilike(f'%{search}%'))
        )

    if role_filter:
        # already outer-joined Role, so filtering on Role.name is fine
        base_query = base_query.filter(Role.name == role_filter)

    if company_filter:
        base_query = base_query.filter(Company.name.ilike(f'%{company_filter}%'))

    active_users_query = base_query.filter(User.is_active.is_(True))
    inactive_users_query = base_query.filter(User.is_active.is_(False))

    active_users = active_users_query.paginate(page=page, per_page=per_page, error_out=False)
    inactive_users = inactive_users_query.paginate(page=page, per_page=per_page, error_out=False)

    roles = Role.query.order_by(Role.name.asc()).all()
    companies = Company.query.order_by(Company.name.asc()).all()

    return render_template(
        'super_admin/users/manage_users.html',  # ✅ match your folder structure (plural)
        active_users=active_users,
        inactive_users=inactive_users,
        roles=roles,
        companies=companies,
        total_active=active_users.total,
        total_inactive=inactive_users.total,
        page=page,
        sort_by=sort_by,
        sort_dir=sort_dir,
        role_filter=role_filter,
        company_filter=company_filter,
        search=search,
    )


# ✅ Export users CSV with SAME filters/sorting and a status scope (active/inactive/all)
@super_admin_bp.route('/users/export', methods=['GET'], endpoint='export_users')
@login_required
@super_admin_required
@has_permission('manage_users')  # reuse same permission gate
def export_users():
    """
    Export filtered/sorted users as CSV.
    Mirrors the logic in manage_users(), with an extra `status` param:
      - status=active (default)
      - status=inactive
      - status=all
    """

    search = request.args.get('search', '').strip().lower()
    role_filter = request.args.get('role_filter', '').strip()
    company_filter = request.args.get('company_filter', '').strip()
    sort_by = request.args.get('sort_by', 'full_name')
    sort_dir = request.args.get('sort_dir', 'asc')
    status = (request.args.get('status') or 'active').strip().lower()  # 👈 new

    valid_fields = {
        'email': User.email,
        'full_name': User.full_name,
        'company': Company.name,
        'role': Role.name,
    }
    sort_column = valid_fields.get(sort_by, User.full_name)
    sort_order = sort_column.asc() if sort_dir == 'asc' else sort_column.desc()

    # Same joins / filters as manage_users
    q = (
        User.query
        .outerjoin(Role, User.role_id == Role.id)
        .outerjoin(Company, User.company_id == Company.id)
        .order_by(sort_order)
    )

    if search:
        q = q.filter(
            (User.email.ilike(f'%{search}%')) |
            (User.full_name.ilike(f'%{search}%')) |
            (User.username.ilike(f'%{search}%'))
        )

    if role_filter:
        q = q.filter(Role.name == role_filter)

    if company_filter:
        q = q.filter(Company.name.ilike(f'%{company_filter}%'))

    # 👇 scope by status (best practice: mirror the current tab)
    if status == 'active':
        q = q.filter(User.is_active.is_(True))
    elif status == 'inactive':
        q = q.filter(User.is_active.is_(False))
    # elif status == 'all':  # no filter

    users = q.all()

    # Build CSV
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "email", "full_name", "username", "role", "company", "status"])

    for u in users:
        role_name = getattr(getattr(u, "role", None), "name", "")      # robust with outerjoin
        company_name = getattr(getattr(u, "company", None), "name", "")
        writer.writerow([
            u.id,
            u.email,
            u.full_name,
            u.username,
            role_name,
            company_name,
            "active" if getattr(u, "is_active", True) else "inactive",
        ])

    data = buf.getvalue().encode("utf-8-sig")
    filename = f"users_{status}.csv" if status in {"active", "inactive"} else "users.csv"
    return Response(
        data,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
