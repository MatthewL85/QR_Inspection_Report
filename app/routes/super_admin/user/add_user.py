# 📍 app/routes/super_admin/user/add_user.py

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from flask_wtf import FlaskForm
from app.routes.super_admin import super_admin_bp
from app.decorators.role import super_admin_required
from app.models import db
from app.models.core.user import User
from app.models.core.role import Role
from app.models.contractor.contractor import Contractor
import re

USERNAME_RE = re.compile(r'^[a-z0-9._-]{3,50}$')
RESERVED_USERNAMES = {"admin", "support", "api", "system", "super-admin"}

class CSRFOnlyForm(FlaskForm):
    """No fields; just provides CSRF token via hidden_tag()."""
    pass

@super_admin_bp.route("/users/add", methods=["GET", "POST"])
@login_required
@super_admin_required
def add_user():
    form = CSRFOnlyForm()

    roles = (
        Role.query
        .filter_by(is_active=True, is_assignable=True)
        .order_by(Role.name.asc())
        .all()
    )
    # Only needed if the role is Contractor; OK to keep loaded
    contractor_companies = (
        Contractor.query.order_by(Contractor.company_name.asc()).all()
    )

    # If your current SA has no company, stop here (rare bootstrap case)
    if not current_user.company_id:
        flash("Your Super Admin account is not linked to a management company. Please create/link one first.", "danger")
        return render_template(
            "super_admin/users/add_user.html",
            form=form, roles=roles,
            contractor_companies=contractor_companies,
            management_companies=[],  # not used anymore
        )

    if request.method == "POST" and form.validate_on_submit():
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        username = (request.form.get("username") or "").strip().lower() or None
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        role_id = request.form.get("role_id")
        pin = request.form.get("pin")
        is_active = bool(request.form.get("is_active"))

        # Basic required checks
        if not all([full_name, email, password, confirm_password, role_id, pin]):
            flash("Please fill in all required fields.", "warning")
            return render_template(
                "super_admin/users/add_user.html",
                form=form, roles=roles,
                contractor_companies=contractor_companies,
                management_companies=[],
            )

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template(
                "super_admin/users/add_user.html",
                form=form, roles=roles,
                contractor_companies=contractor_companies,
                management_companies=[],
            )

        # Email uniqueness
        if User.query.filter_by(email=email).first():
            flash("A user with that email already exists.", "danger")
            return render_template(
                "super_admin/users/add_user.html",
                form=form, roles=roles,
                contractor_companies=contractor_companies,
                management_companies=[],
            )

        # Optional username validation
        if username:
            if not USERNAME_RE.match(username):
                flash("Invalid username format. Use 3–50 chars: lowercase letters, numbers, dot, underscore, hyphen.", "danger")
                return render_template(
                    "super_admin/users/add_user.html",
                    form=form, roles=roles,
                    contractor_companies=contractor_companies,
                    management_companies=[],
                )
            if username in RESERVED_USERNAMES:
                flash("That username is reserved. Please choose another.", "danger")
                return render_template(
                    "super_admin/users/add_user.html",
                    form=form, roles=roles,
                    contractor_companies=contractor_companies,
                    management_companies=[],
                )
            if User.query.filter_by(username=username).first():
                flash("Username already taken. Please choose another.", "danger")
                return render_template(
                    "super_admin/users/add_user.html",
                    form=form, roles=roles,
                    contractor_companies=contractor_companies,
                    management_companies=[],
                )

        role = Role.query.get(role_id)
        if not role or not role.is_active or not role.is_assignable:
            flash("Invalid role selected.", "danger")
            return render_template(
                "super_admin/users/add_user.html",
                form=form, roles=roles,
                contractor_companies=contractor_companies,
                management_companies=[],
            )

        # Create the user
        user = User(
            full_name=full_name,
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            role_id=role.id,
            pin=pin,
            is_active=is_active,
        )

        # 🔧 Organization assignment:
        # - Contractor role: must choose a contractor company
        # - Everyone else: auto-attach to the SA's company (no dropdown required)
        if role.name.lower() == "contractor":
            contractor_id = request.form.get("contractor_id")
            if contractor_id:
                user.contractor_id = int(contractor_id)
                user.company_id = None
            else:
                flash("Please select a contractor company.", "warning")
                return render_template(
                    "super_admin/users/add_user.html",
                    form=form, roles=roles,
                    contractor_companies=contractor_companies,
                    management_companies=[],
                )
        else:
            user.company_id = current_user.company_id
            user.contractor_id = None

        try:
            db.session.add(user)
            db.session.commit()
            flash("✅ User created successfully.", "success")
            return redirect(url_for("super_admin.manage_users"))
        except Exception as e:
            db.session.rollback()
            flash(f"Could not create user: {e}", "danger")

    elif request.method == "POST":
        flash("Your session expired or CSRF token is missing. Please try again.", "danger")

    # GET or invalid POST
    return render_template(
        "super_admin/users/add_user.html",
        form=form,
        roles=roles,
        contractor_companies=contractor_companies,
        management_companies=[],  # no longer used
    )
