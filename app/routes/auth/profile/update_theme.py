from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from app.extensions import db
from app.routes.auth import auth_bp
from app.utils.file import allowed_file, save_profile_photo
from app.models.audit import ProfileChangeLog
from werkzeug.security import generate_password_hash

# 🌗 Theme Preference Update
@auth_bp.route('/update-theme', methods=['POST'], endpoint='update_theme_post')
@login_required
def update_theme():
    theme = request.form.get('theme')
    if theme and theme in ['light', 'dark', 'auto']:
        if current_user.theme_preference != theme:
            log_change(current_user, 'theme_preference', current_user.theme_preference or '—', theme)
            current_user.theme_preference = theme
            db.session.commit()
            flash("Theme preference saved.", "success")
    else:
        flash("Invalid theme selection.", "danger")
    return redirect(url_for('auth.profile'))