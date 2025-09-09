from flask import (
    Blueprint, request, redirect, render_template, flash,
    url_for, session, current_app
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)
from werkzeug.utils import secure_filename

from app.models import User
from app.helpers.auth_helpers import create_user, authenticate_user, user_exists
from app.utils.helpers import role_name_to_dashboard_route  # Optional helper


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/onboard')
def onboard():
    return render_template('onboard.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = authenticate_user(email, password)

        if user:
            login_user(user)

            role_name = user.role.name if user.role else 'Unassigned'
            company_name = user.company.name if user.company else '—'

            session['user'] = {
                'id': user.id,
                'email': user.email,
                'role_name': role_name,
                'company': company_name,
                'name': user.full_name
            }

            session['user_id'] = user.id
            session['role'] = role_name
            session['company_id'] = user.company_id

            print(f"✅ Login successful for: {email}")
            print(f"🧑 Role: {role_name}")
            print(f"🏢 Company: {company_name}")

            flash('Login successful!', 'success')

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

            target_route = route_map.get(role_name)

            if target_route:
                return redirect(url_for(target_route))
            else:
                print(f"❌ Unknown role encountered: {role_name}")
                flash(f"Unknown role: {role_name}. Contact support.", 'danger')
                return redirect(url_for('auth.login'))
        else:
            print(f"❌ Login failed for: {email}")
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash("You’ve been logged out.", "info")
    return redirect(url_for('auth.login'))

from flask_login import login_required, current_user

@auth_bp.route('/profile')
@login_required
def profile():
    user = current_user
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/edit-profile', methods=['POST'])
@login_required
def edit_profile():
    user = current_user

    full_name = request.form.get('full_name')
    share_with_directors = request.form.get('share_with_directors') == 'on'
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # ✅ Full name update
    if full_name and user.full_name != full_name:
        log_change(user, 'full_name', user.full_name, full_name)
        user.full_name = full_name

    # ✅ Share toggle (Property Manager only)
    if user.role and user.role.name == 'Property Manager':
        if user.share_with_directors != share_with_directors:
            log_change(user, 'share_with_directors', user.share_with_directors, share_with_directors)
        user.share_with_directors = share_with_directors

    # ✅ Profile photo upload
    if 'profile_photo' in request.files:
        photo = request.files['profile_photo']
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            path = os.path.join('uploads/profile_photos', filename)
            full_path = os.path.join(current_app.static_folder, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            photo.save(full_path)
            if user.profile_photo != path:
                log_change(user, 'profile_photo', user.profile_photo or '', path)
            user.profile_photo = path

    # ✅ Password update
    if new_password:
        if new_password == confirm_password:
            log_change(user, 'password_hash', '[old_hash]', '[new_hash]')
            user.password_hash = generate_password_hash(new_password)
        else:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('auth.profile'))

    db.session.commit()
    flash("Profile updated successfully!", "success")
    return redirect(url_for('auth.profile'))

# 🔒 Audit log helper
def log_change(user, field, old, new):
    if str(old) != str(new):
        db.session.add(ProfileChangeLog(
            user_id=user.id,
            changed_by=current_user.id,
            field_name=field,
            old_value=str(old),
            new_value=str(new)
        ))


@auth_bp.route('/change-email', methods=['POST'])
@login_required
def change_email():
    if current_user.role.name != "Super Admin":
        abort(403)
    new_email = request.form.get('new_email')
    if new_email:
        log_change(current_user, 'email', current_user.email, new_email)
        current_user.email = new_email
        db.session.commit()
        flash("Email updated successfully.", "success")
    return redirect(url_for('auth.profile'))

@auth_bp.route('/deactivate-account', methods=['POST'])
@login_required
def deactivate_account():
    if current_user.role.name != "Super Admin":
        abort(403)
    current_user.is_active = False
    db.session.commit()
    flash("Your account has been deactivated.", "warning")
    return redirect(url_for('auth.logout'))
