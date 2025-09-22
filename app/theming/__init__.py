from flask import current_app
from app.models.onboarding import Company

def inject_theme():
    # if user isn’t authed yet, fall back to defaults
    try:
        from flask_login import current_user
        if current_user.is_authenticated:
            company = Company.query.get(getattr(current_user, "company_id", None))
        else:
            company = None
    except Exception:
        company = None

    primary = "#3f51b5"
    secondary = "#9fa8da"
    logo = None
    if company:
        primary = company.theme_primary
        secondary = company.theme_secondary
        logo = company.logo_path

    return {
        "THEME_PRIMARY": primary,
        "THEME_SECONDARY": secondary,
        "THEME_LOGO_PATH": logo,
    }
