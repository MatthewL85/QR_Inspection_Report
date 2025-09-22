# app/routes/__init__.py

from app.routes.super_admin.dashboard import super_admin_bp
from app.routes.onboarding import onboarding_bp

def register_routes(app):
    app.register_blueprint(super_admin_bp)
    app.register_blueprint(super_admin_users_bp)
    app.register_blueprint(onboarding_bp)
    

    # Later you’ll add:
    # from app.routes.admin.dashboard import admin_bp
    # from app.routes.property_manager.dashboard import pm_bp
    # app.register_blueprint(admin_bp)
    # app.register_blueprint(pm_bp)
