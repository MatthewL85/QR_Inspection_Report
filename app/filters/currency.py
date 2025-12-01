from flask import Flask

def format_currency(value, symbol="€", sep=","):
    """
    Format a number as currency without decimal points.
    Example: 12000 -> "€12,000"
    """
    if value is None:
        return ""
    try:
        # Cast to float first in case it's Decimal
        amount = float(value)
        return f"{symbol}{amount:,.0f}".replace(",", sep)
    except Exception:
        return str(value)

def init_currency_filter(app: Flask):
    """Register the currency filter with Jinja2."""
    app.jinja_env.filters["currency"] = format_currency
