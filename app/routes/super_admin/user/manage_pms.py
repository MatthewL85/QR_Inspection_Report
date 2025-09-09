from flask import render_template, request
from flask_login import login_required
from app.routes.super_admin import super_admin_bp
from app.decorators.role import super_admin_required
from app.models.core.user import User
from app.models.core.role import Role

@super_admin_bp.route("/property-managers", endpoint="manage_pms")
@login_required
@super_admin_required
def manage_pms():
    """List only Property Manager users (with pagination)."""
    page = request.args.get("page", 1, type=int)
    per_page = 10

    q = (
        User.query
            .join(User.role)
            .filter(Role.name == "Property Manager")
            .order_by(User.full_name.asc())
    )

    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        "super_admin/user/manage_pms.html",
        users=pagination,
        total=pagination.total,
    )
