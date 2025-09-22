# app/utils/jinja_filters.py
from __future__ import annotations

import html
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
from markupsafe import Markup

# Optional: locale-aware formatting if Babel is installed
try:
    from babel.numbers import format_currency as babel_format_currency  # type: ignore
except Exception:  # pragma: no cover
    babel_format_currency = None


# ------------------------- helpers -------------------------

def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


_CURRENCY_SYMBOLS = {
    "EUR": "€",
    "GBP": "£",
    "USD": "$",
    "CAD": "$",
    "AUD": "$",
    "NZD": "$",
}


# ------------------- registration entrypoint -------------------

def register_custom_filters(app):
    """
    Register all custom Jinja filters used across LogixPM.
    Call this once in create_app().
    """

    # ---------- Currency / numbers ----------

    @app.template_filter()
    def currency(value: Any, code: str = "EUR", decimals: int | None = None, locale: str | None = None) -> str:
        """
        {{ amount | currency('EUR') }}
        - Uses Babel when available; falls back to symbol + thousand separators.
        - decimals default: 0 when abs(value) >= 1000 else 2.
        """
        amt = _to_decimal(value)
        if decimals is None:
            decimals = 0 if abs(amt) >= 1000 else 2

        # Prefer locale-aware formatting
        if babel_format_currency:
            loc = (
                locale
                or ("en_IE" if code.upper() == "EUR" else "en_GB" if code.upper() == "GBP" else "en_US")
            )
            try:
                return babel_format_currency(amt, code.upper(), locale=loc)
            except Exception:
                pass  # fall back to manual

        # Manual formatting
        q = Decimal("1") if decimals == 0 else Decimal("0.01")
        amt_q = amt.quantize(q, rounding=ROUND_HALF_UP)
        formatted = f"{amt_q:,.{decimals}f}"
        symbol = _CURRENCY_SYMBOLS.get(code.upper(), code.upper() + " ")
        return f"{symbol}{formatted}" if symbol in _CURRENCY_SYMBOLS.values() else f"{symbol} {formatted}"

    @app.template_filter()
    def int_comma(value: Any) -> str:
        """{{ n | int_comma }} -> 12,345"""
        try:
            n = int(_to_decimal(value))
        except Exception:
            n = 0
        return f"{n:,}"

    @app.template_filter()
    def percent(value: Any, decimals: int = 0) -> str:
        """{{ ratio | percent(1) }} -> '12.3%' (expects 0.123 as input for 12.3%)"""
        try:
            d = _to_decimal(value)
            return f"{d:.{decimals}%}"
        except Exception:
            return "0%"

    # ---------- Your UI helpers ----------

    @app.template_filter()
    def ai_score_label(score):
        if score is None:
            return "N/A"
        try:
            score = float(score)
            if score >= 85:
                return "🌟 Excellent"
            elif score >= 70:
                return "✅ Good"
            elif score >= 50:
                return "⚠️ Average"
            else:
                return "🔴 Needs Review"
        except (ValueError, TypeError):
            return "Invalid Score"

    @app.template_filter()
    def compliance_status_tag(status):
        if not status:
            return "❔ Unknown"
        s = str(status).strip().lower()
        mapping = {
            "valid": "✅ Valid",
            "expired": "⚠️ Expired",
            "missing": "❌ Missing",
            "pending": "🕓 Pending",
        }
        return mapping.get(s, f"❔ {s.capitalize()}")

    @app.template_filter()
    def format_date_human(date_obj):
        if not date_obj:
            return "—"
        try:
            # Accept both datetime and date
            if isinstance(date_obj, datetime):
                return date_obj.strftime("%d %B %Y")
            return date_obj.strftime("%d %B %Y")
        except Exception:
            return str(date_obj)

    @app.template_filter()
    def truncate_text(text, length: int = 100):
        if not text:
            return ""
        try:
            s = str(text)
            return s if len(s) <= length else s[:length].rstrip() + "..."
        except Exception:
            return str(text)

    @app.template_filter()
    def highlight_keywords(text, keywords):
        """
        Safely highlight one/more keywords (case-insensitive) with <mark>.
        Usage: {{ body | highlight_keywords(['fee','budget'])|safe }}
        The filter returns Markup already, so extra |safe is optional.
        """
        if text is None:
            return Markup("")
        try:
            s = html.escape(str(text))
            kws = [keywords] if isinstance(keywords, str) else (keywords or [])
            for kw in kws:
                if not kw:
                    continue
                pattern = re.compile(re.escape(str(kw)), re.IGNORECASE)
                s = pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", s)
            return Markup(s)
        except Exception:
            return Markup(html.escape(str(text)))

    # ✅ Final explicit bindings (useful if decorators are bypassed in some contexts)
    app.jinja_env.filters["currency"] = currency
    app.jinja_env.filters["int_comma"] = int_comma
    app.jinja_env.filters["percent"] = percent
    app.jinja_env.filters["ai_score_label"] = ai_score_label
    app.jinja_env.filters["compliance_status_tag"] = compliance_status_tag
    app.jinja_env.filters["format_date_human"] = format_date_human
    app.jinja_env.filters["truncate_text"] = truncate_text
    app.jinja_env.filters["highlight_keywords"] = highlight_keywords
