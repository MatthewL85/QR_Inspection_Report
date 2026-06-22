# 📍 app/routes/auth/onboard.py

from flask import current_app, render_template, redirect, url_for, session
from flask_login import current_user, login_required
from app.routes.auth import auth_bp


@auth_bp.route('/onboard')
@login_required
def onboard():
    # 🛡️ Prevent re-onboarding for fully onboarded users
    if current_user.is_fully_onboarded:
        role_routes = {
            "Super Admin": "super_admin.dashboard",
            "Property Manager": "property_manager.pm_dashboard",
            "Contractor": "contractor.contractor_dashboard",
            "Director": "director.dashboard",
            "Assistant": "assistant.dashboard",
            "Assistant Property Manager": "assistant.dashboard",
            "Assistant Manager": "assistant.dashboard",
            "Master Assistant": "assistant.dashboard",
        }
        endpoint = role_routes.get(current_user.role_name, "auth.profile")
        if endpoint not in current_app.view_functions:
            endpoint = "auth.profile"
        return redirect(url_for(endpoint))

    # Optional future hook: track onboarding stage in session
    session['onboarding_step'] = 'welcome'

    return render_template('auth/onboard.html')
