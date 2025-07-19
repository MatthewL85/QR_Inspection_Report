def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)

    # ✅ Defer imports to avoid circular issues
    from app.routes.capex import capex_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.property_manager import property_manager_bp
    from app.routes.contractor import contractor_bp
    from app.routes.director import director_bp

    app.register_blueprint(capex_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(property_manager_bp, url_prefix='/pm')
    app.register_blueprint(contractor_bp, url_prefix='/contractor')
    app.register_blueprint(director_bp, url_prefix='/director')

    return app
