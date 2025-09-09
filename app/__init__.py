# 📁 app/__init__.py

from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from builtins import hasattr as py_hasattr  # ✅ expose hasattr to Jinja safely

from flask import Flask, session
from flask_wtf import CSRFProtect
from flask_babel import Babel

# 🔌 Core Extensions
from app.extensions import db, migrate, login_manager, mail, register_login_loader

# 🧪 Jinja Helpers
from app.utils.json_helpers import json_prettify, truncate_json, parse_and_format_json
from app.utils.jinja_filters import register_custom_filters

# (Optional) client-type normaliser as a template filter
try:
    from app.utils.client_type_normalize import normalize_client_type
except Exception:  # pragma: no cover
    normalize_client_type = None

# ✅ CSRF & i18n
csrf = CSRFProtect()
babel = Babel()


# 🔢 Custom filter for integer with comma formatting
def _int_comma(value):
    """Format numbers like 12,345 (no decimals)."""
    try:
        if value is None or value == "":
            return ""
        n = int(Decimal(str(value)))
        return f"{n:,}"  # 12,345
    except (InvalidOperation, ValueError, TypeError):
        return value


def create_app():
    # 📁 Absolute paths for templates/static
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_path = os.path.join(base_dir, 'templates')
    static_path = os.path.join(base_dir, 'static')

    # 🚀 Initialize Flask app
    app = Flask(__name__, template_folder=template_path, static_folder=static_path)
    app.config.from_object('app.config.Config')  # 🧠 Load config from class

    # 🔌 Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    register_login_loader(app)

    # 🌐 Flask-Babel — robust init across versions (2.x/3.x/4.x)
    def _select_locale():
        # Pull from session, fall back to 'en'
        return session.get('language', 'en')

    try:
        # Babel >= 3 supports the locale_selector kwarg
        babel.init_app(app, locale_selector=_select_locale)
    except TypeError:
        # Babel 2.x fallback using decorator
        babel.init_app(app)

        @babel.localeselector  # type: ignore[attr-defined]
        def _legacy_locale_selector():
            return _select_locale()

    # 📦 Import models for Alembic to “see” them
    from app import models  # noqa: F401

    # (Optional safety) explicitly import new contracts/works packages so Alembic never misses them
    try:  # pragma: no cover
        from app.models.contracts import (  # noqa: F401
            ContractTemplate,
            ContractTemplateVersion,
            ClientContract,
        )
        from app.models.works.special_project import ClientSpecialProject  # noqa: F401
    except Exception as _e:
        # Don't break app startup if models are being introduced incrementally
        app.logger.debug(f"Contracts/Works models not fully available yet: {_e}")

    # 🧠 Register role-based blueprints
    from app.routes.auth import register_auth_routes
    from app.routes.super_admin import super_admin_bp
    from app.routes.property_manager import property_manager_bp
    from app.routes.contractor import contractor_bp
    from app.routes.director import director_bp
    from app.routes.equipment import equipment_bp
    from app.routes.capex import capex_bp
    from app.routes.tenant import tenant_bp
    from app.guards.onboarding_guard import register_onboarding_guard

    # NEW: Contracts renewal wizard (templates, preview, PDF, e-sign stub)
    # Import from the package path: app/routes/super_admin/contracts/contracts.py (re-exported in __init__.py)
    try:
        from app.routes.super_admin.contracts import super_admin_contracts_bp
    except Exception as _e:  # pragma: no cover
        super_admin_contracts_bp = None
        app.logger.debug(f"Contracts blueprint not available yet: {_e}")

    # ✅ Register routes / blueprints
    register_auth_routes(app)
    app.register_blueprint(super_admin_bp, url_prefix='/super-admin')
    app.register_blueprint(property_manager_bp, url_prefix='/pm')
    app.register_blueprint(contractor_bp, url_prefix='/contractor')
    app.register_blueprint(director_bp, url_prefix='/director')
    app.register_blueprint(equipment_bp)
    app.register_blueprint(capex_bp)
    app.register_blueprint(tenant_bp, url_prefix="/tenant")
    register_onboarding_guard(app)

    if super_admin_contracts_bp:
        # contracts BP already carries its own url_prefix="/super-admin/contracts"
        app.register_blueprint(super_admin_contracts_bp)

    # 🧪 Register custom Jinja filters
    app.jinja_env.filters['json_prettify'] = json_prettify
    app.jinja_env.filters['truncate_json'] = truncate_json
    app.jinja_env.filters['parse_and_format_json'] = parse_and_format_json
    app.jinja_env.filters['int_comma'] = _int_comma  # ✅ Register our new filter
    register_custom_filters(app)

    # (Optional) make normalize_client_type available as a template filter
    if normalize_client_type is not None:
        @app.template_filter('normalize_client_type')
        def _normalize_client_type_filter(s):
            return normalize_client_type(s)

    # 🧠 Global Jinja context (+ fix hasattr in templates)
    app.jinja_env.globals.update(
        now=datetime.utcnow,
        timedelta=timedelta,
        hasattr=py_hasattr,  # ✅ so `{% if hasattr(obj, 'field') %}` works
    )

    # 🧰 CLI: seed roles + demo company + owner
    try:
        from app.cli.seed import seed_all

        @app.cli.command("seed")
        def seed_cmd():
            """Seed roles, a demo management company, and a Super Admin user."""
            created_roles, company, owner = seed_all()
            print(f"✅ Seeded: {created_roles} roles")
            print(f"🏢 Company: {company.name} (active={company.is_active})")
            print(f"👤 Owner user: {owner.email} (password set in seed)")
    except Exception as e:
        app.logger.warning(f"Seed CLI unavailable: {e}")

    # 🧰 CLI: seed IE/PSRA contract template + version
    try:
        from app.cli.seed_contracts import seed_contract_template_ie
        app.cli.add_command(seed_contract_template_ie)
    except Exception as e:
        app.logger.info(f"Contracts seed CLI not registered: {e}")

    # 🧰 CLI: backfill contract audits  ✅ NEW
    try:
        from app.cli.backfill_contract_audits import backfill_contract_audits
        app.cli.add_command(backfill_contract_audits)
    except Exception as e:
        app.logger.info(f"Backfill CLI not registered: {e}")

    return app
