# 📍 app/routes/auth/onboard.py

from flask import render_template, redirect, url_for, session
from flask_login import current_user, login_required
from app.routes.auth import auth_bp


@auth_bp.route('/onboard')
@login_required
def onboard():
    # 🛡️ Prevent re-onboarding for fully onboarded users
    if current_user.is_fully_onboarded:
        return redirect(url_for('dashboard_route_selector'))

    # Optional future hook: track onboarding stage in session
    session['onboarding_step'] = 'welcome'

    return render_template('auth/onboard.html')
