# 📍 app/routes/auth/email/change_email.py

from flask import request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.routes.auth import auth_bp
from app.extensions import db
from app.models.audit import ProfileChangeLog
from app.utils.audit import log_change

# ✉️ Super Admin: Change email address (admin-only for now)
@auth_bp.route('/change-email', methods=['POST'])
@login_required
def change_email():
    if current_user.role.name != "Super Admin":
        abort(403)

    new_email = request.form.get('new_email')
    if new_email and new_email != current_user.email:
        log_change(current_user, 'email', current_user.email, new_email)
        current_user.email = new_email
        db.session.commit()
        flash("📧 Email updated successfully.", "success")
    else:
        flash("⚠️ No new email entered or email is unchanged.", "warning")

    return redirect(url_for('auth.profile'))
