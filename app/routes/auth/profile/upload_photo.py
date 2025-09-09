from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from app.extensions import db
from app.routes.auth import auth_bp
from app.utils.file import allowed_file, save_profile_photo
from app.models.audit import ProfileChangeLog
from werkzeug.security import generate_password_hash

# 📸 Profile Photo Upload (Standalone)
@auth_bp.route('/upload-photo', methods=['POST'])
@login_required
def upload_photo():
    file = request.files.get('photo')
    if file and allowed_file(file.filename):
        path = save_profile_photo(file, current_user.id)
        log_change(current_user, 'profile_photo', current_user.profile_photo or '', path)
        current_user.profile_photo = path
        db.session.commit()
        flash("Profile photo updated!", "success")
    else:
        flash("Invalid image file", "danger")
    return redirect(url_for('auth.profile'))