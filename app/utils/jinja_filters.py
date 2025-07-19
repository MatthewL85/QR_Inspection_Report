import html
import re
from datetime import datetime


def register_custom_filters(app):
    # ✅ AI Score Label (for Capex, Documents, Logs, etc.)
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

    # ✅ Compliance Status Tag (for documents & checks)
    @app.template_filter()
    def compliance_status_tag(status):
        if not status:
            return "❔ Unknown"
        status = status.strip().lower()
        mapping = {
            'valid': '✅ Valid',
            'expired': '⚠️ Expired',
            'missing': '❌ Missing',
            'pending': '🕓 Pending'
        }
        return mapping.get(status, f"❔ {status.capitalize()}")

    # ✅ Format datetime to “02 July 2025” (Human-readable)
    @app.template_filter()
    def format_date_human(date_obj):
        if not date_obj:
            return "—"
        try:
            return date_obj.strftime('%d %B %Y')
        except Exception:
            return str(date_obj)

    # ✅ Truncate long text safely (e.g. logs, descriptions)
    @app.template_filter()
    def truncate_text(text, length=100):
        if not text:
            return ''
        try:
            text = str(text)
            return text if len(text) <= length else text[:length].rstrip() + '...'
        except Exception:
            return str(text)

    # ✅ Highlight one or more keywords in text (case-insensitive)
    @app.template_filter()
    def highlight_keywords(text, keywords):
        if not text or not keywords:
            return html.escape(text)

        try:
            text = html.escape(text)
            if isinstance(keywords, str):
                keywords = [keywords]

            for kw in keywords:
                pattern = re.compile(re.escape(kw), re.IGNORECASE)
                text = pattern.sub(lambda match: f'<mark>{match.group(0)}</mark>', text)

            return text
        except Exception:
            return html.escape(text)

    # ✅ Register all filters with the Flask app
    app.jinja_env.filters['ai_score_label'] = ai_score_label
    app.jinja_env.filters['compliance_status_tag'] = compliance_status_tag
    app.jinja_env.filters['format_date_human'] = format_date_human
    app.jinja_env.filters['truncate_text'] = truncate_text
    app.jinja_env.filters['highlight_keywords'] = highlight_keywords
