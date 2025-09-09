# app/routes/auth/signup.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user
from werkzeug.security import generate_password_hash

from app.routes.auth import auth_bp  # your auth blueprint
from app.forms.auth.signup_form import SignupForm
from app.models import db
from app.models.core.user import User
from app.models.core.role import Role

@auth_bp.route("/signup", methods=["GET", "POST"], endpoint="signup")
def signup():
    # If already logged in, skip
    if current_user.is_authenticated:
        return redirect(url_for("super_admin.dashboard"))

    form = SignupForm()

    if request.method == "POST" and form.validate_on_submit():
        email = form.email.data.strip().lower()
        username = form.username.data.strip().lower()
        full_name = form.full_name.data.strip()
        password = form.password.data

        # Uniqueness checks
        if User.query.filter_by(email=email).first():
            flash("A user with that email already exists.", "danger")
            return render_template("auth/signup.html", form=form)

        if User.query.filter_by(username=username).first():
            flash("That username is already taken.", "danger")
            return render_template("auth/signup.html", form=form)

        # Fetch/create Super Admin role (assignable root role)
        role = Role.query.filter_by(name="Super Admin").first()
        if not role:
            role = Role(name="Super Admin", is_active=True, is_assignable=True)
            db.session.add(role)
            db.session.flush()

        # Create the user (no company yet — will be set after onboarding)
        user = User(
            full_name=full_name,
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            role_id=role.id,
            is_active=True,
            pin="SETLATER"  # or generate a default, up to you
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("✅ Account created. Let’s set up your company.", "success")
        return redirect(url_for("tenant.company_onboarding"))

    return render_template("auth/signup.html", form=form)
