# 📍 app/routes/auth/profile/edit_profile.py

from flask import request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.routes.auth import auth_bp
from app.utils.audit import log_change
from app.utils.file import allowed_file, save_profile_photo
from werkzeug.security import generate_password_hash


# 📝 Profile Edit
@auth_bp.route('/edit-profile', methods=['POST'])
@login_required
def edit_profile():
    user = current_user

    full_name = request.form.get('full_name')
    share_with_directors = request.form.get('share_with_directors') == 'on'
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # 👤 Full name
    if full_name and user.full_name != full_name:
        log_change(user, 'full_name', user.full_name, full_name)
        user.full_name = full_name

    # 👥 Share with Directors (PM only)
    if user.role and user.role.name == 'Property Manager':
        if user.share_with_directors != share_with_directors:
            log_change(user, 'share_with_directors', user.share_with_directors, share_with_directors)
            user.share_with_directors = share_with_directors

    # 📸 Profile Photo Upload
    if 'profile_photo' in request.files:
        photo = request.files['profile_photo']
        if photo and allowed_file(photo.filename):
            path = save_profile_photo(photo, user.id)
            if user.profile_photo != path:
                log_change(user, 'profile_photo', user.profile_photo or '', path)
            user.profile_photo = path

    # 🔒 Password Update
    if new_password:
        if new_password == confirm_password:
            log_change(user, 'password_hash', '[old_hash]', '[new_hash]')
            user.password_hash = generate_password_hash(new_password)
        else:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('auth.profile'))

    db.session.commit()
    flash("✅ Profile updated successfully!", "success")
    return redirect(url_for('auth.profile'))
