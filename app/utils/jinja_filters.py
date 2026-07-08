# app/utils/jinja_filters.py
from __future__ import annotations

import html
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from html.parser import HTMLParser
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

    @app.template_filter("key_site_content")
    def key_site_content(value: Any) -> Markup:
        """
        Render Key Site Info with a tiny allow-list for operational formatting.
        Allows the rich text controls used by the Key Site editor while still
        escaping scripts, arbitrary styles and unsafe URLs.
        """
        if value is None:
            return Markup("")

        raw = html.unescape(str(value).strip())
        if not raw:
            return Markup("")

        color_pattern = re.compile(
            r"^(#[0-9a-fA-F]{3,8}|rgba?\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}(?:\s*,\s*(?:0|1|0?\.\d+))?\s*\)|[a-zA-Z]+)$"
        )
        safe_url_pattern = re.compile(r"^(https?:|mailto:|tel:|/|#)", re.IGNORECASE)
        safe_text_alignments = {"left", "center", "right", "justify"}

        block_tags = {"p", "ul", "ol", "li", "blockquote", "h2", "h3", "h4", "table", "thead", "tbody", "tr", "th", "td"}
        inline_tags = {"strong", "b", "em", "i", "u", "span", "a", "br"}
        media_tags = {"img", "video", "source"}
        allowed_tags = block_tags | inline_tags | media_tags

        def _safe_style(style: str | None) -> str:
            if not style:
                return ""
            safe_parts: list[str] = []
            for part in style.split(";"):
                name, _, val = part.partition(":")
                prop = name.strip().lower()
                raw_value = val.strip()
                if prop in {"color", "background-color"}:
                    color = raw_value
                    if color_pattern.match(color):
                        safe_parts.append(f"{prop}: {html.escape(color, quote=True)}")
                elif prop == "text-align" and raw_value.lower() in safe_text_alignments:
                    safe_parts.append(f"text-align: {raw_value.lower()}")
            return "; ".join(safe_parts)

        def _safe_attrs(tag: str, attrs) -> str:
            attr_map = {name.lower(): value for name, value in attrs}
            safe: list[str] = []

            style = _safe_style(attr_map.get("style"))
            if style and tag in {"p", "span", "td", "th", "h2", "h3", "h4"}:
                safe.append(f'style="{style}"')

            if tag == "a":
                href = (attr_map.get("href") or "").strip()
                if href and safe_url_pattern.match(href):
                    safe.append(f'href="{html.escape(href, quote=True)}"')
                    safe.append('rel="noopener noreferrer"')
                    safe.append('target="_blank"')

            if tag in {"img", "video", "source"}:
                src = (attr_map.get("src") or "").strip()
                if src and safe_url_pattern.match(src):
                    safe.append(f'src="{html.escape(src, quote=True)}"')
                if tag == "img":
                    alt = attr_map.get("alt") or ""
                    safe.append(f'alt="{html.escape(alt, quote=True)}"')
                if tag == "video":
                    safe.append("controls")
                    width = (attr_map.get("width") or "").strip()
                    height = (attr_map.get("height") or "").strip()
                    if width.isdigit():
                        safe.append(f'width="{width}"')
                    if height.isdigit():
                        safe.append(f'height="{height}"')

            return (" " + " ".join(safe)) if safe else ""

        class _KeySiteParser(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.parts: list[str] = []
                self.suppressed_tag_depth = 0

            def handle_starttag(self, tag, attrs):
                tag = tag.lower()
                if tag in {"script", "style"}:
                    self.suppressed_tag_depth += 1
                    return
                if self.suppressed_tag_depth:
                    return
                if tag not in allowed_tags:
                    return
                if tag == "br":
                    self.parts.append("<br>")
                    return
                self.parts.append(f"<{tag}{_safe_attrs(tag, attrs)}>")

            def handle_startendtag(self, tag, attrs):
                tag = tag.lower()
                if self.suppressed_tag_depth:
                    return
                if tag not in allowed_tags:
                    return
                if tag in {"br", "img", "source"}:
                    self.parts.append(f"<{tag}{_safe_attrs(tag, attrs)}>")

            def handle_endtag(self, tag):
                tag = tag.lower()
                if tag in {"script", "style"} and self.suppressed_tag_depth:
                    self.suppressed_tag_depth -= 1
                    return
                if self.suppressed_tag_depth:
                    return
                if tag in allowed_tags and tag not in {"br", "img", "source"}:
                    self.parts.append(f"</{tag}>")

            def handle_data(self, data):
                if self.suppressed_tag_depth:
                    return
                self.parts.append(html.escape(data))

        if "<" not in raw or ">" not in raw:
            paragraphs = [
                f"<p>{html.escape(line.strip())}</p>"
                for line in raw.splitlines()
                if line.strip()
            ]
            return Markup("".join(paragraphs))

        parser = _KeySiteParser()
        try:
            parser.feed(raw)
            rendered = "".join(parser.parts).strip()
            return Markup(rendered or html.escape(raw))
        except Exception:
            return Markup(html.escape(raw))

    # ---------- New: safe 'format' override + simple 'money' helper ----------

    def _format_safe(fmt: Any, *args, **kwargs) -> str:
        """
        Drop-in replacement for Jinja's built-in `format` filter that won't 500 on None.
        Behaves like Python %-formatting used by Jinja:
          {{ '€%.2f' | format(amount) }}
        If `amount` is None, this returns '€0.00' (or best-effort) instead of raising.
        """
        s = str(fmt)

        # Detect whether the format string includes a numeric conversion
        has_numeric = bool(re.search(r"%[-+ #0-9.]*[dfFeEgG]", s))

        def _coerce(v):
            if v is None:
                return 0 if has_numeric else ""
            return v

        try:
            if kwargs:
                return s % {k: _coerce(v) for k, v in kwargs.items()}
            return s % tuple(_coerce(v) for v in args)
        except Exception:
            # As a last resort, return the original format string
            return s

    @app.template_filter("money")
    def money(value: Any, symbol: str = "€", decimals: int = 0) -> str:
        """
        {{ value | money('€') }}  ->  €12,000  (default no cents)
        {{ value | money('£', 2) }} -> £12,000.00
        """
        try:
            f = float(_to_decimal(value))
        except Exception:
            f = 0.0
        decimals = int(decimals or 0)
        if decimals > 0:
            return f"{symbol}{f:,.{decimals}f}"
        return f"{symbol}{f:,.0f}"

    # ---------- New: data coercion helpers for forms (to avoid dicts in inputs) ----------

    def _looks_like_address(d: dict) -> bool:
        keys = set(k.lower() for k in d.keys())
        return any(
            k in keys
            for k in (
                "line1", "line_1", "address1", "address_1", "street",
                "line2", "line_2", "address2", "address_2",
                "city", "town", "county", "state", "region", "province",
                "postal_code", "postcode", "zip", "country"
            )
        )

    def _address_to_str(d: dict) -> str:
        def take(*names):
            for n in names:
                if n in d and d[n]:
                    return str(d[n])
            return ""
        parts = [
            take("line1", "line_1", "address1", "address_1", "street"),
            take("line2", "line_2", "address2", "address_2"),
            take("city", "town"),
            take("county", "state", "region", "province"),
            take("postal_code", "postcode", "zip"),
            take("country"),
        ]
        return ", ".join([p for p in parts if p]).strip(", ") or ""

    @app.template_filter("address_join")
    def address_join(value: Any) -> str:
        """
        Formats a dict-like address into a single line string.
        """
        if isinstance(value, dict) and _looks_like_address(value):
            return _address_to_str(value)
        return "" if value in (None, {}, []) else str(value)

    @app.template_filter("deep_get")
    def deep_get(value: Any, path: str, default: Any = "") -> Any:
        """
        Dot-path extractor: {{ obj | deep_get('issuer.issuer_name') }}
        Works with dicts and objects (via getattr).
        """
        if value is None or not path:
            return default
        cur = value
        for part in str(path).split("."):
            if isinstance(cur, dict):
                cur = cur.get(part, default)
            else:
                cur = getattr(cur, part, default)
            if cur is default:
                break
        return cur

    @app.template_filter("coerce_text")
    def coerce_text(value: Any, kind: str = "auto") -> str:
        """
        Turn nested values into clean, human-friendly strings for inputs.
        kind ∈ {'auto','name','address','role','contact'}
        """
        if value is None:
            return ""

        # Simple primitives
        if isinstance(value, (int, float, Decimal, str)):
            return "" if value == "null" else str(value)

        # Dict handling
        if isinstance(value, dict):
            k = (kind or "auto").lower()
            lower_keys = {kk.lower(): kk for kk in value.keys()}

            if k in ("address",) or (k == "auto" and _looks_like_address(value)):
                return _address_to_str(value)

            if k in ("name", "auto"):
                for key in ("display_name", "legal_name", "name", "issuer_name", "client_name", "agent_name", "full_name", "contact_name"):
                    if key in lower_keys and value[lower_keys[key]]:
                        return str(value[lower_keys[key]])

            if k in ("role",) and "role" in lower_keys:
                return str(value[lower_keys["role"]])

            if k in ("contact",):
                email = None
                phone = None
                for key in ("email", "e_mail"):
                    if key in lower_keys and value[lower_keys[key]]:
                        email = value[lower_keys[key]]
                        break
                for key in ("phone", "mobile", "tel"):
                    if key in lower_keys and value[lower_keys[key]]:
                        phone = value[lower_keys[key]]
                        break
                pieces = [p for p in (email, phone) if p]
                if pieces:
                    return " • ".join(str(p) for p in pieces)

            # Fallback: best available field
            for key in ("name", "title", "label", "id"):
                if key in lower_keys and value[lower_keys[key]]:
                    return str(value[lower_keys[key]])
            return ""  # avoid dumping dict repr into input

        # Lists/Tuples — join simple items
        if isinstance(value, (list, tuple)):
            items = [coerce_text(v, kind) for v in value]
            items = [i for i in items if i]
            return ", ".join(items)

        # Fallback
        try:
            return str(value)
        except Exception:
            return ""

    @app.template_filter("safe_str")
    def safe_str(value: Any) -> str:
        """
        Safer stringification for inputs — returns '' for dicts/lists rather than
        dumping Python repr into the UI.
        """
        if value is None:
            return ""
        if isinstance(value, (dict, list, tuple, set)):
            return ""
        return str(value)

    # ✅ Final explicit bindings (useful if decorators are bypassed in some contexts)
    app.jinja_env.filters["currency"] = currency
    app.jinja_env.filters["int_comma"] = int_comma
    app.jinja_env.filters["percent"] = percent
    app.jinja_env.filters["ai_score_label"] = ai_score_label
    app.jinja_env.filters["compliance_status_tag"] = compliance_status_tag
    app.jinja_env.filters["format_date_human"] = format_date_human
    app.jinja_env.filters["truncate_text"] = truncate_text
    app.jinja_env.filters["highlight_keywords"] = highlight_keywords

    # New explicit bindings
    app.jinja_env.filters["format"] = _format_safe  # override built-in safely
    app.jinja_env.filters["money"] = money
    app.jinja_env.filters["address_join"] = address_join
    app.jinja_env.filters["deep_get"] = deep_get
    app.jinja_env.filters["coerce_text"] = coerce_text
    app.jinja_env.filters["safe_str"] = safe_str
