from flask import render_template, request
from flask_login import login_required
from app.routes.super_admin import super_admin_bp
from app.decorators.role import super_admin_required
from app.models.core.user import User
from app.models.core.role import Role

@super_admin_bp.route("/contractors", endpoint="manage_contractors")
@login_required
@super_admin_required
def manage_contractors():
    """List only Contractor users (with pagination)."""
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # Use relationship-safe join to avoid AmbiguousForeignKeysError
    q = (
        User.query
            .join(User.role)                # <-- joins via relationship, safe
            .filter(Role.name == "Contractor")
            .order_by(User.full_name.asc())
    )

    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        "super_admin/user/manage_contractors.html",
        users=pagination,
        total=pagination.total,
    )
