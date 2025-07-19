from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, timedelta
from flask import Flask
from app.extensions import db, migrate, login_manager, register_login_loader  # Centralized extensions


# ✅ Import custom Jinja filters
from app.utils.json_helpers import json_prettify, truncate_json, parse_and_format_json
from app.utils.jinja_filters import register_custom_filters  # Modular Jinja filter loader

def create_app():
    # ✅ Setup absolute paths for template/static folders
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_path = os.path.join(base_dir, 'templates')
    static_path = os.path.join(base_dir, 'static')

    # ✅ Initialize Flask app
    app = Flask(__name__, template_folder=template_path, static_folder=static_path)
    app.config.from_object('config.Config')

    # ✅ Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    register_login_loader(app)

    # ✅ Ensure models are loaded for Alembic migration detection
    from app import models

    # ✅ Register all blueprints (role-based modules)
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.super_admin import super_admin_bp
    from app.routes.property_manager import property_manager_bp
    from app.routes.contractor import contractor_bp
    from app.routes.director import director_bp
    from app.routes.equipment import equipment_bp
    from app.routes.capex import capex_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(super_admin_bp, url_prefix='/super-admin')
    app.register_blueprint(property_manager_bp, url_prefix='/pm')
    app.register_blueprint(contractor_bp, url_prefix='/contractor')
    app.register_blueprint(director_bp, url_prefix='/director')
    app.register_blueprint(equipment_bp)
    app.register_blueprint(capex_bp)

    # ✅ Register custom Jinja filters (for JSON, AI, formatting)
    app.jinja_env.filters['json_prettify'] = json_prettify
    app.jinja_env.filters['truncate_json'] = truncate_json
    app.jinja_env.filters['parse_and_format_json'] = parse_and_format_json
    register_custom_filters(app)  # from app/utils/jinja_filters.py

    # ✅ Register global Jinja variables
    app.jinja_env.globals.update(now=datetime.utcnow, timedelta=timedelta)

    return app

