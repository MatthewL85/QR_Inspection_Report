# app/services/contract/contracts.py
from __future__ import annotations

import os
import re
from typing import Optional, Tuple, List

from flask import current_app, url_for
from flask import render_template_string

from app.models.contracts import ClientContract, ContractTemplateVersion


# ---------- small utils ----------

def _safe_slug(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-{2,}", "-", s).strip("-") or "doc"


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _static_rel_and_abs(*parts) -> tuple[str, str]:
    """
    Build a path relative to the app's static folder + the absolute FS path.
    Returns (rel, abs).
    """
    rel = os.path.join(*parts)
    abs_ = os.path.join(current_app.static_folder, rel)
    _ensure_dir(os.path.dirname(abs_))
    return rel.replace("\\", "/"), abs_


def _save_string_as_static_asset(content: str, rel_path: str) -> str:
    """
    Save a text file under the static folder and return its static URL.
    """
    abs_path = os.path.join(current_app.static_folder, rel_path)
    _ensure_dir(os.path.dirname(abs_path))
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)
    return url_for("static", filename=rel_path)


# ---------- PDF backends ----------

def _render_pdf_weasy(html: str, base_url: str, css_paths: Optional[List[str]] = None) -> Optional[bytes]:
    """
    Try WeasyPrint. Returns PDF bytes or None if WeasyPrint not available.
    """
    try:
        from weasyprint import HTML, CSS  # type: ignore
    except Exception:
        return None

    css_objs = []
    for css_rel in (css_paths or []):
        css_abs = os.path.join(current_app.static_folder, css_rel)
        if os.path.exists(css_abs):
            css_objs.append(CSS(filename=css_abs))

    pdf_bytes = HTML(string=html, base_url=base_url).write_pdf(stylesheets=css_objs)
    return pdf_bytes


def _render_pdf_wkhtml(html: str, out_abs_path: str, base_url: str, css_paths: Optional[List[str]] = None) -> bool:
    """
    Try pdfkit (wkhtmltopdf). Returns True if the file was written.
    """
    try:
        import pdfkit  # type: ignore
    except Exception:
        return False

    # Option 1: write html to a temp file and render with file path
    # Option 2: render from string (requires --enable-local-file-access when reading local CSS)
    options = {
        "enable-local-file-access": None,
        "page-size": "A4",
        "print-media-type": None,
        "margin-top": "10mm",
        "margin-right": "10mm",
        "margin-bottom": "12mm",
        "margin-left": "10mm",
        "encoding": "UTF-8",
    }

    css_abs_list = []
    for css_rel in (css_paths or []):
        css_abs = os.path.join(current_app.static_folder, css_rel)
        if os.path.exists(css_abs):
            css_abs_list.append(css_abs)

    try:
        pdfkit.from_string(html, out_abs_path, options=options, css=css_abs_list)
        return os.path.exists(out_abs_path)
    except Exception:
        return False


# ---------- Public API ----------

def render_contract_html(contract: ClientContract) -> str:
    """
    Render HTML using the template version's Jinja template with 'data' + 'contract'.
    """
    tv: ContractTemplateVersion = contract.template_version
    data = contract.data_json or {}
    # Make sure we can resolve relative URLs for images/CSS in template (base_url = static root)
    html = render_template_string(tv.html_template, data=data, contract=contract)
    return html


def generate_contract_artifacts(client, contract: ClientContract) -> Tuple[str, Optional[str]]:
    """
    Render HTML, save it under /static/contracts/<contract.id>/,
    attempt to render a PDF (WeasyPrint or wkhtmltopdf). Return (html_url, pdf_url_or_None).
    """
    # 1) Render HTML
    html = render_contract_html(contract)

    # 2) Paths
    folder_rel, folder_abs = _static_rel_and_abs("contracts", str(contract.id))
    html_rel = os.path.join(folder_rel, "contract.html").replace("\\", "/")
    pdf_rel  = os.path.join(folder_rel, "contract.pdf").replace("\\", "/")
    html_abs = os.path.join(current_app.static_folder, html_rel)
    pdf_abs  = os.path.join(current_app.static_folder, pdf_rel)

    # 3) Save HTML
    _ensure_dir(os.path.dirname(html_abs))
    with open(html_abs, "w", encoding="utf-8") as f:
        f.write(html)
    html_url = url_for("static", filename=html_rel)

    # 4) Try to create PDF (WeasyPrint first)
    base_url = current_app.static_url_path  # for resolving /static/... in CSS/images
    css_list = ["css/pdf.css"]  # you can add per-tenant CSS later
    pdf_bytes = _render_pdf_weasy(html, base_url=base_url, css_paths=css_list)
    pdf_url: Optional[str] = None

    if pdf_bytes:
        with open(pdf_abs, "wb") as f:
            f.write(pdf_bytes)
        pdf_url = url_for("static", filename=pdf_rel)
    else:
        # 5) Fallback: wkhtmltopdf/pdfkit
        ok = _render_pdf_wkhtml(html, out_abs_path=pdf_abs, base_url=base_url, css_paths=css_list)
        if ok:
            pdf_url = url_for("static", filename=pdf_rel)
        else:
            pdf_url = None  # gracefully degrade; UI will show "PDF not available"

    return html_url, pdf_url

def render_html_for_version(template_version, data: dict, contract=None) -> str:
    """
    Render HTML string for a given ContractTemplateVersion and data_json-like dict.
    Does not persist anything.
    """
    html_template = template_version.html_template or ""
    # give template access to "data" (preferred) and "contract" (optional)
    return render_template_string(html_template, data=data or {}, contract=contract)


# ----------------------- SNAPSHOT & AUDIT HELPERS (added) -----------------------
from datetime import datetime, date  # added
from decimal import Decimal          # added
from flask_login import current_user # added
from app import db                   # added
# use your actual helper location (you confirmed this path earlier)
from app.services.contract.contract_audits import create_contract_audit  # added

_JSON_SAFE_TYPES = (str, int, float, bool, type(None))  # added


def _to_json_safe(value):  # added
    """Convert common non-JSON types to JSON-safe primitives."""
    if isinstance(value, _JSON_SAFE_TYPES):
        return value
    if isinstance(value, Decimal):
        try:
            return float(value)
        except Exception:
            return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(v) for v in value]
    # Fallback
    return str(value)


def contract_snapshot(contract) -> dict:  # added
    """
    Return a JSON-safe dict of key fields we care about in audits.
    Adjust the field list to match your ClientContract schema.
    """
    fields = [
        "id",
        "name",
        "sign_status",
        "contract_value",
        "currency",
        "start_date",
        "end_date",
        "next_fee_increase_date",
        "template_version_id",
    ]
    snap = {}
    for f in fields:
        snap[f] = _to_json_safe(getattr(contract, f, None))
    return snap


def log_contract_audit(  # added
    contract: ClientContract,
    action: str,
    before: dict | None,
    after: dict | None,
    notes: str | None = None,
    actor_id: int | None = None,
):
    """
    Convenience wrapper to stage a ContractAudit row for this contract.
    Does not commit — let the caller control the transaction boundary.
    """
    if actor_id is None:
        try:
            actor_id = current_user.id  # if in request context
        except Exception:
            actor_id = None

    create_contract_audit(
        db.session,
        contract_id=contract.id,
        action=action,
        before=before,
        after=after,
        notes=notes,
        actor_id=actor_id,
    )
