# 📁 app/__init__.py
from dotenv import load_dotenv
load_dotenv()  # Local dev reads .env; on Render we use Dashboard env vars

import os
from datetime import datetime, timedelta
from decimal import Decimal
from builtins import hasattr as py_hasattr
from flask_wtf.csrf import generate_csrf
from flask import Flask, session, redirect, g, url_for
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
    app.config.from_object(os.getenv("FLASK_CONFIG", "app.config.ProductionConfig"))

    # Defaults for brand assets (used by sidebar/logo/avatar)
    app.config.setdefault("BRAND_LOGO_PATH", "assets/img/logo-ct-dark.png")
    app.config.setdefault("DEFAULT_AVATAR_PATH", "assets/img/team-2.jpg")
    app.config.setdefault("BRAND_COMPANY_NAME", "LogixPM")  # used as a final fallback

    # Behind Render proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    register_login_loader(app)

    # 🔐 Make csrf_token() available in all templates
    app.jinja_env.globals.update(csrf_token=generate_csrf)

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

    # ---- 🔗 Register blueprints ----
    from app.routes.auth import register_auth_routes
    from app.routes.super_admin import super_admin_bp
    register_auth_routes(app)
    app.register_blueprint(super_admin_bp, url_prefix="/super-admin")

    # Settings is required (your current code expects it)
    from app.routes.settings import settings_bp
    app.register_blueprint(settings_bp)

    # Onboarding blueprint
    try:
        from app.routes.onboarding import onboarding_bp
        app.register_blueprint(onboarding_bp)  # onboarding_bp already has url_prefix in its module
        app.logger.info("Registered onboarding blueprint")
    except Exception as e:
        app.logger.warning(f"Onboarding blueprint not registered: {e}")

    # Optional modules
    def _maybe_register(bp_import_path, attr_name, url_prefix=None):
        try:
            mod = __import__(bp_import_path, fromlist=[attr_name])
            bp = getattr(mod, attr_name)
            app.register_blueprint(bp, url_prefix=url_prefix)
        except Exception as e:
            app.logger.info(f"Optional blueprint not registered ({bp_import_path}.{attr_name}): {e}")

    _maybe_register("app.routes.property_manager", "property_manager_bp", "/pm")
    _maybe_register("app.routes.contractor", "contractor_bp", "/contractor")
    _maybe_register("app.routes.director", "director_bp", "/director")
    _maybe_register("app.routes.equipment", "equipment_bp", None)
    _maybe_register("app.routes.capex", "capex_bp", None)
    _maybe_register("app.routes.tenant", "tenant_bp", "/tenant")
    _maybe_register("app.routes.super_admin.contracts", "super_admin_contracts_bp", None)

    # ---- 🖌️ Settings + Theme injection (GLOBAL) ----
    try:
        from app.models.org.company_settings import CompanySettings  # type: ignore
    except Exception:
        CompanySettings = None  # type: ignore

    # Also read Company branding as a fallback during onboarding
    try:
        from app.models.onboarding.company import Company  # type: ignore
    except Exception:
        Company = None  # type: ignore

    # Devtools
    try:
        from app.routes.devtools import devtools_bp
        app.register_blueprint(devtools_bp)
    except Exception as e:
        app.logger.info(f"Devtools not registered: {e}")

    @app.before_request
    def _load_company_settings():
        """
        Load CompanySettings row into g (if present).
        Also stash a lightweight 'branding fallback' from Company when settings are absent.
        This runs for ALL pages, including login/logout.
        """
        if CompanySettings is None:
            g.company_settings = None
        else:
            try:
                g.company_settings = CompanySettings.query.first()
            except Exception as e:
                app.logger.debug(f"CompanySettings load skipped: {e}")
                g.company_settings = None

        g.branding_fallback = None
        if Company is not None:
            try:
                cid = session.get("onboarding_company_id")
                q = Company.query
                company = q.get(cid) if cid else None
                if company is None:
                    company = q.first()
                g.branding_fallback = company
            except Exception as e:
                app.logger.debug(f"Branding fallback load skipped: {e}")

    @app.context_processor
    def _inject_theme_vars():
        """
        Make theme variables and logo URL available to ALL templates.
        Priority:
          1) CompanySettings
          2) Company fallback (brand_primary_color, brand_secondary_color, brand_color, logo_path)
          3) Defaults
        Also exposes auth-friendly BRAND_* aliases so login/logout can theme easily.
        Adds SHOW_ONBOARDING_BANNER flag for dashboards.
        """
        S = getattr(g, "company_settings", None)
        C = getattr(g, "branding_fallback", None)

        def _norm_hex(h, default_hex):
            if not h:
                return default_hex
            s = str(h).strip()
            if not s.startswith("#"):
                s = "#" + s
            return s

        # Colors
        primary   = _norm_hex(getattr(S, "primary_hex", None) if S else None,
                              _norm_hex(getattr(C, "brand_primary_color", None) if C else None, "#2152ff"))
        secondary = _norm_hex(getattr(S, "secondary_hex", None) if S else None,
                              _norm_hex(getattr(C, "brand_secondary_color", None) if C else None, "#2dce89"))
        accent    = _norm_hex(getattr(S, "accent_hex", None) if S else None,
                              _norm_hex(getattr(C, "brand_color", None) if C else None, "#f5365c"))
        sidebar   = getattr(S, "sidebar_hex", None) if S and getattr(S, "sidebar_hex", None) else "#1f283e"
        rounded   = bool(getattr(S, "rounded", True)) if S else True

        # Logo URL resolve
        if S and getattr(S, "logo_path", None):
            logo_path = S.logo_path
        elif C and getattr(C, "logo_path", None):
            logo_path = C.logo_path
        else:
            logo_path = app.config.get("BRAND_LOGO_PATH", "assets/img/logo-ct-dark.png")

        filename = str(logo_path).lstrip("/")
        if filename.startswith("static/"):
            filename = filename[len("static/"):]
        try:
            logo_url = url_for("static", filename=filename)
        except Exception:
            logo_url = f"/static/{filename}".replace("//", "/")

        company_name = (getattr(C, "name", None)
                        or getattr(S, "company_name", None)
                        or app.config.get("BRAND_COMPANY_NAME", "LogixPM"))

        # ✅ Compute whether onboarding banner should show
        def _is_configured():
            name_ok = bool(company_name and company_name.strip().lower() != "new company")
            has_logo = bool((S and getattr(S, "logo_path", None)) or (C and getattr(C, "logo_path", None)))
            has_primary = bool((S and getattr(S, "primary_hex", None)) or (C and getattr(C, "brand_primary_color", None)))
            return name_ok and (has_logo or has_primary)

        done_in_session = bool(session.get("onboarding_completed_at"))
        show_onboarding_banner = (not done_in_session) and (not _is_configured())

        # Return both THEME_* and BRAND_* (aliases for auth/public templates)
        return dict(
            # Theme vars (existing)
            THEME_PRIMARY=primary,
            THEME_SECONDARY=secondary,
            THEME_ACCENT=accent,
            THEME_SIDEBAR=sidebar,
            THEME_ROUNDED=rounded,

            # Branding vars (aliases, now safe on login/logout)
            BRAND_PRIMARY_COLOR=primary,
            BRAND_SECONDARY_COLOR=secondary,
            BRAND_ACCENT_COLOR=accent,
            BRAND_LOGO_URL=logo_url,
            BRAND_COMPANY_NAME=company_name,

            # New: flag the dashboard can use to hide the wizard banner
            SHOW_ONBOARDING_BANNER=show_onboarding_banner,

            # Raw objects (if anyone needs them)
            COMPANY_SETTINGS=S,
            COMPANY_BRANDING=C,
        )

    # ---- Jinja filters & globals ----
    app.jinja_env.filters["json_prettify"] = json_prettify
    app.jinja_env.filters["truncate_json"] = truncate_json
    app.jinja_env.filters["parse_and_format_json"] = parse_and_format_json
    app.jinja_env.filters["int_comma"] = _int_comma
    register_custom_filters(app)

    if normalize_client_type is not None:
        @app.template_filter("normalize_client_type")
        def _normalize_client_type_filter(s):
            return normalize_client_type(s)

    # Common globals
    app.jinja_env.globals.update(
        now=datetime.utcnow,
        timedelta=timedelta,
        hasattr=py_hasattr,
    )

    # Make current_app & config available inside templates
    from flask import current_app as flask_current_app

    @app.context_processor
    def inject_template_globals():
        return {
            "current_app": flask_current_app,
            "config": flask_current_app.config,
        }

    # Ensure upload folder exists (and branding subdir)
    upload_folder = app.config.get("UPLOAD_FOLDER") or os.path.join(static_path, "uploads")
    app.config["UPLOAD_FOLDER"] = upload_folder
    try:
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(os.path.join(upload_folder, "branding"), exist_ok=True)
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
    try:
        from app.cli.backfill_contract_audit import backfill_contract_audits as _backfill_cmd
        app.cli.add_command(_backfill_cmd)
    except Exception as e1:
        try:  # pragma: no cover
            from app.cli.backfill_contract_audits import backfill_contract_audits as _backfill_cmd
            app.cli.add_command(_backfill_cmd)
        except Exception as e2:
            app.logger.info(f"Backfill CLI not registered: primary={e1}; fallback={e2}")

    # --- DB safety net: rollback the session if a request ends with an error ---
    @app.teardown_request
    def _rollback_on_teardown(exc):
        if exc is not None:
            try:
                db.session.rollback()
            except Exception:
                pass

    return app
