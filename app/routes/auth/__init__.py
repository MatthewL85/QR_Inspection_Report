# 📍 app/routes/auth/__init__.py

from flask import Blueprint

# 🔐 Define Blueprint
auth_bp = Blueprint('auth', __name__)

# ✅ Route Registration Function
def register_auth_routes(app):
    # Import routes to attach them to auth_bp
    from app.routes.auth import (
        login,
        logout,
        onboard,
        reset_password,
        forgot_password,
        language,
    )
    from app.routes.auth.profile import (
        profile,
        edit_profile,
        change_password,
        deactivate,
        upload_photo,
        update_theme,
    )
    from app.routes.auth.email import (
        change_email,
        verify_email,
        resend_verification,
    )
    from app.routes.auth.security import (
        two_factor,
        two_factor_setup,
        verify_token,
    )

    # ✅ Register the blueprint with the app
    app.register_blueprint(auth_bp, url_prefix='/auth')
