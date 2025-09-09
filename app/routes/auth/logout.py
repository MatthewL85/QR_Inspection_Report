# 📍 app/routes/auth/logout.py

from flask import redirect, url_for, flash, session
from flask_login import logout_user, login_required
from app.routes.auth import auth_bp


@auth_bp.route('/logout')
@login_required
def logout():
    # 🔐 Log out the user securely
    logout_user()

    # 🧹 Clear session data
    session.clear()

    # ✅ User feedback
    flash("👋 You’ve been logged out successfully.", "info")

    # 🔁 Redirect to login
    return redirect(url_for('auth.login'))
