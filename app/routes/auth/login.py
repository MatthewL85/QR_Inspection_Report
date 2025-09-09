# 📍 app/routes/auth/login.py

from flask import request, redirect, render_template, flash, url_for, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from sqlalchemy import or_, func

from app.routes.auth import auth_bp
from app.forms.auth.login_form import LoginForm
from app.models.core.user import User
from app.extensions import db  # use your shared db instance


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        identifier = (request.form.get("identifier") or "").strip().lower()
        password = request.form.get("password") or ""

        # Allow login by either email or username (case-insensitive)
        user = (
            User.query
            .filter(
                or_(
                    func.lower(User.email) == identifier,
                    func.lower(User.username) == identifier
                )
            )
            .first()
        )

        # Validate user + password + active state
        if user and user.is_active and (user.deleted_at is None) and check_password_hash(user.password_hash, password):
            login_user(user)

            # 🌐 Store session context
            session['user'] = {
                'id': user.id,
                'email': user.email,
                'role': user.role.name if user.role else 'Unassigned',
                'company': user.company.name if getattr(user, "company", None) else '—',
                'name': user.full_name
            }
            session['user_id'] = user.id
            session['role'] = user.role.name if user.role else 'Unassigned'
            session['company_id'] = user.company_id

            flash('✅ Login successful!', 'success')

            # 🔁 Redirect based on role
            route_map = {
                'Super Admin': 'super_admin.dashboard',
                'Admin': 'admin.dashboard',
                'Property Manager': 'property_manager.dashboard',
                'Contractor': 'contractor.dashboard',
                'Director': 'director.dashboard',
                'Financial Controller': 'finance.dashboard',
                'Member': 'member.dashboard',
                'Resident': 'resident.dashboard'
            }
            return redirect(url_for(route_map.get(session['role'], 'auth.login')))

        # Fallback: bad creds or inactive
        flash('❌ Invalid credentials or inactive account.', 'danger')

    return render_template('auth/login.html', form=form)
