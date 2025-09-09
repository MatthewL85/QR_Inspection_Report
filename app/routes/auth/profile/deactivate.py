# 📍 app/routes/auth/profile/deactivate.py

from flask import redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.routes.auth import auth_bp
from app.extensions import db
from app.models.audit import ProfileChangeLog
from app.utils.audit import log_change

# ❌ Deactivate Account (Super Admin only)
@auth_bp.route('/deactivate-account', methods=['POST'])
@login_required
def deactivate_account():
    if current_user.role.name != "Super Admin":
        abort(403)

    log_change(current_user, 'account_status', 'Active', 'Deactivated')
    current_user.is_active = False
    db.session.commit()

    flash("Your account has been deactivated.", "warning")
    return redirect(url_for('auth.logout'))
