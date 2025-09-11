# 📁 app/__init__.py
from dotenv import load_dotenv
load_dotenv()  # Local dev reads .env; on Render we use Dashboard env vars

import os
from datetime import datetime, timedelta
from decimal import Decimal
from builtins import hasattr as py_hasattr

from flask import Flask, session, redirect
from flask_wtf import CSRFProtect
from flask_babel import Babel
from werkzeug.middleware.proxy_fix import ProxyFix

# Core extensions
from app.extensions import db, migrate, login_manager, mail, register_login_loader

# Jinja helpers
from app.utils.json_helpers import json_prettify, truncate_json, parse_and_format_json
from app.utils.jinja_filters import register_custom_filters

# Optional filter
try:
    from app.utils.client_type_normalize import normalize_client_type
except Exception:  # pragma: no cover
    normalize_client_type = None

csrf = CSRFProtect()
babel = Babel()

def _int_comma(value):
    """Format numbers like 12,345 (no decimals)."""
    try:
        if value is None or value == "":
            return ""
        n = int(Decimal(str(value)))
        return f"{n:,}"
    except Exception:
        return value

def create_app():
    # Absolute paths for templates/static
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_path = os.path.join(base_dir, "templates")
    static_path = os.path.join(base_dir, "static")

    # Flask app
    app = Flask(__name__, template_folder=template_path, static_folder=static_path)

    # Load config from class path in env (defaults to ProductionConfig)
    # e.g. FLASK_CONFIG=app.config.DevelopmentConfig for local dev
    app.config.from_object(os.getenv("FLASK_CONFIG", "app.config.ProductionConfig"))

    # Behind Render proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    register_login_loader(app)

    # Babel locale selection
    def _select_locale():
        return session.get("language", "en")

    try:
        babel.init_app(app, locale_selector=_select_locale)
    except TypeError:
        babel.init_app(app)
        @babel.localeselector  # type: ignore[attr-defined]
        def _legacy_locale_selector():
            return _select_locale()

    # Ensure models are imported for Alembic
    from app import models  # noqa

    # Optionally import packages so Alembic sees them
    try:  # pragma: no cover
        from app.models.contracts import (  # noqa
            ContractTemplate, ContractTemplateVersion, ClientContract
        )
        from app.models.works.special_project import ClientSpecialProject  # noqa
    except Exception as _e:
        app.logger.debug(f"Contracts/Works models not fully available yet: {_e}")

    # Register blueprints
    from app.routes.auth import register_auth_routes
    from app.routes.super_admin import super_admin_bp

    def _maybe_register(bp_import_path, attr_name, url_prefix=None):
        try:
            mod = __import__(bp_import_path, fromlist=[attr_name])
            bp = getattr(mod, attr_name)
            app.register_blueprint(bp, url_prefix=url_prefix)
        except Exception as e:
            app.logger.info(f"Optional blueprint not registered ({bp_import_path}.{attr_name}): {e}")

    register_auth_routes(app)
    app.register_blueprint(super_admin_bp, url_prefix="/super-admin")
    _maybe_register("app.routes.property_manager", "property_manager_bp", "/pm")
    _maybe_register("app.routes.contractor", "contractor_bp", "/contractor")
    _maybe_register("app.routes.director", "director_bp", "/director")
    _maybe_register("app.routes.equipment", "equipment_bp", None)
    _maybe_register("app.routes.capex", "capex_bp", None)
    _maybe_register("app.routes.tenant", "tenant_bp", "/tenant")
    _maybe_register("app.routes.super_admin.contracts", "super_admin_contracts_bp", None)

    # Jinja filters & globals
    app.jinja_env.filters["json_prettify"] = json_prettify
    app.jinja_env.filters["truncate_json"] = truncate_json
    app.jinja_env.filters["parse_and_format_json"] = parse_and_format_json
    app.jinja_env.filters["int_comma"] = _int_comma
    register_custom_filters(app)

    if normalize_client_type is not None:
        @app.template_filter("normalize_client_type")
        def _normalize_client_type_filter(s):
            return normalize_client_type(s)

    app.jinja_env.globals.update(
        now=datetime.utcnow,
        timedelta=timedelta,
        hasattr=py_hasattr,
    )

    # Ensure upload folder exists
    upload_folder = app.config.get("UPLOAD_FOLDER") or os.path.join(static_path, "uploads")
    app.config["UPLOAD_FOLDER"] = upload_folder
    try:
        os.makedirs(upload_folder, exist_ok=True)
    except Exception as e:
        app.logger.warning(f"Could not create UPLOAD_FOLDER ({upload_folder}): {e}")

    # Root redirect & healthcheck
    @app.route("/", methods=["GET", "HEAD"])
    def root():
        return redirect("/auth/login")

    @app.route("/healthz", methods=["GET", "HEAD"])
    def healthz():
        return ("ok", 200)

    # CLI: seed & tools
    try:
        from app.cli.seed import seed_all
        @app.cli.command("seed")
        def seed_cmd():
            created_roles, company, owner = seed_all()
            print(f"✅ Seeded: {created_roles} roles")
            print(f"🏢 Company: {company.name} (active={company.is_active})")
            print(f"👤 Owner user: {owner.email} (password set in seed)")
    except Exception as e:
        app.logger.warning(f"Seed CLI unavailable: {e}")

    try:
        from app.cli.seed_contracts import seed_contract_template_ie
        app.cli.add_command(seed_contract_template_ie)
    except Exception as e:
        app.logger.info(f"Contracts seed CLI not registered: {e}")

    # --- Backfill Contract Audits CLI registration ---
    # Primary: your file is app/cli/backfill_contract_audit.py and the function is backfill_contract_audits
    try:
        from app.cli.backfill_contract_audit import backfill_contract_audits as _backfill_cmd
        app.cli.add_command(_backfill_cmd)
    except Exception as e1:
        # Fallbacks for legacy names/locations
        try:  # pragma: no cover
            from app.cli.backfill_contract_audits import backfill_contract_audits as _backfill_cmd
            app.cli.add_command(_backfill_cmd_legacy)
        except Exception as e2:
            app.logger.info(f"Backfill CLI not registered: {e1 or e2}")

    return app
