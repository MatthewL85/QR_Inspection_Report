from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from app.extensions import db
from app.routes.auth import auth_bp
from app.utils.file import allowed_file, save_profile_photo
from app.models.audit import ProfileChangeLog
from werkzeug.security import generate_password_hash

# 👤 Profile View
@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)
