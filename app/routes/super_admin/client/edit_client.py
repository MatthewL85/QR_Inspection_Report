from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from decimal import Decimal, InvalidOperation
import os
import json
import re
from datetime import datetime, date  # NEW

from app.routes.super_admin import super_admin_bp
from app.decorators.role import super_admin_required
from app.models import db, Client, User
# NEW: Document model import (with fallback)
try:
    from app.models.core.document import Document
except Exception:
    from app.models.document import Document

from app.forms.client.edit_client_form import EditClientForm

try:
    from app.utils.client_type_normalize import normalized_choice_list, normalize_client_type
except Exception:
    def normalize_client_type(s: str) -> str:  # minimal fallback
        return (s or "").strip()
    def normalized_choice_list(opts):
        seen, out = set(), []
        for o in (opts or []):
            v = normalize_client_type(o)
            if v not in seen:
                out.append((v, v))
                seen.add(v)
        return out

# -----------------------------
# Country normalisation helpers
# -----------------------------
COUNTRY_ALIASES = {
    # IE
    'republic of ireland': 'IE',
    'ireland': 'IE',
    'ie': 'IE',
    # GB / UK
    'united kingdom': 'GB',
    'uk': 'GB',
    'great britain': 'GB',
    'gb': 'GB',
    'england': 'GB',
    'scotland': 'GB',
    'wales': 'GB',
    'northern ireland': 'GB',
    # Common ISO passthroughs for others
    'us': 'US', 'usa': 'US', 'united states': 'US', 'united states of america': 'US',
    'ca': 'CA', 'canada': 'CA',
    'au': 'AU', 'australia': 'AU',
    'nz': 'NZ', 'new zealand': 'NZ',
    'sg': 'SG', 'singapore': 'SG',
    'hk': 'HK', 'hong kong': 'HK', 'hong kong sar': 'HK',
    'ae': 'AE', 'uae': 'AE', 'u.a.e': 'AE',
}

def canonical_country(val: str) -> str:
    if not val:
        return ''
    v = val.strip().lower()
    return COUNTRY_ALIASES.get(v, val).upper()

# -----------------------------
# Lookup helpers
# -----------------------------
def mgmt_types_for(country: str) -> list[str]:
    c = (country or '').strip().lower()
    if c in ('ireland', 'ie', 'republic of ireland'):
        return ['OMC', 'Commercial Management Company', 'Mixed-Use']
    if c in ('united kingdom', 'uk', 'great britain', 'gb', 'england', 'wales'):
        return ['RMC', 'RTM Company', 'Commonhold Association']
    if c == 'scotland':
        return ['Owners’ Association', 'Property Factor']
    if c in ('northern ireland', 'ni'):
        return ['Owners’ Association', 'Management Company']
    if c in ('united states', 'united states of america', 'usa', 'us'):
        return ['HOA', 'Condo Association', 'Co-op Board']
    if c in ('canada', 'ca'):
        return ['Condo Corp.', 'Strata', 'HOA']
    if c in ('australia', 'au'):
        return ['Owners Corporation', 'Strata', 'Community Association']
    if c in ('new zealand', 'nz'):
        return ['Body Corporate', 'Strata', 'Manager']
    if c in ('singapore', 'sg'):
        return ['MCST']
    if c in ('hong kong', 'hk', 'hong kong sar'):
        return ["Owners’ Corporation"]
    if c in ('united arab emirates', 'uae', 'u.a.e', 'dubai', 'abu dhabi', 'sharjah', 'ajman',
             'umm al-quwain', 'ras al khaimah', 'fujairah'):
        return ['Owners Association', 'Master Community']
    if c in ('austria','belgium','bulgaria','croatia','cyprus','czech republic','czechia','denmark',
             'estonia','finland','france','germany','greece','hungary','iceland','italy','latvia',
             'lithuania','luxembourg','malta','netherlands','norway','poland','portugal','romania',
             'slovakia','slovenia','spain','sweden','switzerland','liechtenstein'):
        return ['Owners’ Association', 'Management Company']
    return ['Management Company', 'Owners’ Association']

def ownership_types_for(country: str) -> list[str]:
    c = (country or '').strip().lower()
    if c in ('ireland','ie','republic of ireland','united kingdom','uk','great britain','gb','england','scotland','wales','northern ireland'):
        return ['Freehold','Leasehold','Share of Freehold']
    if c in ('united states','united states of america','usa','us'):
        return ['Freehold','Condominium','Co-op']
    if c in ('canada','ca'):
        return ['Freehold','Condominium (Strata)','Leasehold']
    if c in ('australia','au'):
        return ['Freehold','Strata Title','Community Title']
    if c in ('new zealand','nz'):
        return ['Freehold','Unit Title','Leasehold']
    if c in ('singapore','sg'):
        return ['Freehold','Leasehold','Strata']
    if c in ('hong kong','hk','hong kong sar'):
        return ['Leasehold','Strata']
    if c in ('united arab emirates','uae','u.a.e','dubai','abu dhabi','sharjah','ajman','umm al-quwain','ras al khaimah','fujairah'):
        return ['Freehold','Leasehold','Strata']
    if c in ('austria','belgium','bulgaria','croatia','cyprus','czech republic','czechia','denmark',
             'estonia','finland','france','germany','greece','hungary','iceland','italy','latvia',
             'lithuania','luxembourg','malta','netherlands','norway','poland','portugal','romania',
             'slovakia','slovenia','spain','sweden','switzerland'):
        return ['Freehold','Leasehold']
    return ['Freehold','Leasehold']

def default_language_for(country: str) -> str:
    c = (country or '').strip().lower()
    if c in ('ireland','ie','united kingdom','uk','great britain','gb','england','scotland','wales','northern ireland',
             'united states','usa','us','canada','australia','new zealand','singapore','hong kong',
             'hong kong sar','united arab emirates','uae'):
        return 'English'
    if c in ('france',): return 'French'
    if c in ('spain',): return 'Spanish'
    if c in ('portugal',): return 'Portuguese'
    if c in ('germany',): return 'German'
    if c in ('italy',): return 'Italian'
    if c in ('netherlands',): return 'Dutch'
    return 'English'

def currency_for(country: str) -> str:
    c = (country or '').strip().lower()
    if c in ('ireland','ie'): return 'EUR'
    if c in ('united kingdom','uk','great britain','gb','england','scotland','wales','northern ireland'): return 'GBP'
    if c in ('united states','usa','us'): return 'USD'
    if c in ('canada','ca'): return 'CAD'
    if c in ('australia','au'): return 'AUD'
    if c in ('new zealand','nz'): return 'NZD'
    if c in ('singapore','sg'): return 'SGD'
    if c in ('hong kong','hk','hong kong sar'): return 'HKD'
    if c in ('united arab emirates','uae','u.a.e'): return 'AED'
    if c in ('france','germany','spain','portugal','italy','netherlands','belgium','austria','finland',
             'ireland','latvia','lithuania','luxembourg','malta','cyprus','estonia','slovakia','slovenia','greece'):
        return 'EUR'
    if c in ('sweden',): return 'SEK'
    if c in ('denmark',): return 'DKK'
    if c in ('norway',): return 'NOK'
    if c in ('switzerland',): return 'CHF'
    return 'EUR'

def timezone_for(country: str) -> str:
    c = (country or '').strip().lower()
    if c in ('ireland','ie'): return 'Europe/Dublin'
    if c in ('united kingdom','uk','great britain','gb','england','scotland','wales','northern ireland'): return 'Europe/London'
    if c in ('united states','usa','us'): return 'America/New_York'
    if c in ('canada','ca'): return 'America/Toronto'
    if c in ('australia','au'): return 'Australia/Sydney'
    if c in ('new zealand','nz'): return 'Pacific/Auckland'
    if c in ('singapore','sg'): return 'Asia/Singapore'
    if c in ('hong kong','hk','hong kong sar'): return 'Asia/Hong_Kong'
    if c in ('united arab emirates','uae','u.a.e'): return 'Asia/Dubai'
    if c in ('france','germany','spain','italy','netherlands','belgium','portugal'): return 'Europe/Paris'
    return 'UTC'

# -----------------------------
# FK normalization helper (no autoflush)
# -----------------------------
def normalize_and_validate(role_name: str, user_id):
    try:
        uid = int(user_id or 0)
    except Exception:
        uid = 0
    if uid <= 0:
        return None
    with db.session.no_autoflush:
        user = (
            User.query.join(User.role)
            .filter(
                User.id == uid,
                User.is_active.is_(True),
                User.company_id == current_user.company_id,
                User.role.has(name=role_name)
            )
            .first()
        )
    return user.id if user else None

# Simple int parser for posted numbers (supports "1,234")
def _to_int(val):
    try:
        return int(str(val).replace(',', '').strip())
    except Exception:
        return 0

@super_admin_bp.route('/clients/<int:client_id>/edit/', methods=['GET', 'POST'], endpoint='edit_client')
@login_required
@super_admin_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)

    # Users by role
    pm_query = (
        User.query.join(User.role)
        .filter(
            User.is_active.is_(True),
            User.company_id == current_user.company_id,
            User.role.has(name='Property Manager')
        )
        .order_by(User.full_name.asc())
    )
    fc_query = (
        User.query.join(User.role)
        .filter(
            User.is_active.is_(True),
            User.company_id == current_user.company_id,
            User.role.has(name='Financial Controller')
        )
        .order_by(User.full_name.asc())
    )
    asst_query = (
        User.query.join(User.role)
        .filter(
            User.is_active.is_(True),
            User.company_id == current_user.company_id,
            User.role.has(name='Assistant Property Manager')
        )
        .order_by(User.full_name.asc())
    )

    form = EditClientForm(obj=client)
    form.assigned_pm_id.choices = [(0, '— Select —')] + [(u.id, u.full_name) for u in pm_query.all()]
    form.assigned_fc_id.choices = [(0, '— Select —')] + [(u.id, u.full_name) for u in fc_query.all()]
    form.assigned_assistant_id.choices = [(0, '— Select —')] + [(u.id, u.full_name) for u in asst_query.all()]

    # Jurisdiction-aware choices
    posted_country = request.form.get('country') if request.method == 'POST' else None
    country_for_choices_raw = posted_country if posted_country is not None else (client.country or '')
    country_key = canonical_country(country_for_choices_raw)

    raw_types = mgmt_types_for(country_key) or []
    form.client_type.choices = [('', '— Select —')] + normalized_choice_list(raw_types)
    form.ownership_types.choices = [(t, t) for t in ownership_types_for(country_key)]

    # Accept client_type POSTed by the browser (legacy/variant), but normalise it first
    if request.method == 'POST':
        posted_type = (request.form.get('client_type') or '').strip()
        posted_norm = normalize_client_type(posted_type) if posted_type else ''
        existing_values = {v for v, _ in form.client_type.choices}
        if posted_norm and posted_norm not in existing_values:
            form.client_type.choices.append((posted_norm, posted_norm))

    # Prefill defaults on GET if empty, and show canonical client_type
    if request.method == 'GET':
        if client.client_type:
            form.client_type.data = normalize_client_type(client.client_type)
        if not client.preferred_language:
            form.preferred_language.data = default_language_for(country_key)
        if not client.currency:
            form.currency.data = currency_for(country_key)
        if not client.timezone:
            form.timezone.data = timezone_for(country_key)

    form.client_id.data = client.id

    # ---------- Validate & Save ----------
    # Graceful handling for FYE (string "DD/MM") even if the form field is DateField
    raw_fye = (request.form.get(getattr(form.financial_year_end, 'name', 'financial_year_end')) or '').strip() \
              if request.method == 'POST' else ''
    fye_pattern = re.compile(r'^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])$')

    valid = form.validate_on_submit()
    if request.method == 'POST' and not valid:
        # If the only blocker is FYE formatting (client-side text), allow save
        other_errors = {k: v for k, v in (form.errors or {}).items() if k != 'financial_year_end'}
        if (not other_errors) and (raw_fye == '' or fye_pattern.match(raw_fye)):
            # Treat as valid; we'll set FYE manually below
            valid = True

    if valid:
        # ---- Sanitize assignment IDs FIRST (inside no_autoflush) ----
        raw_pm   = form.assigned_pm_id.data
        raw_fc   = form.assigned_fc_id.data
        raw_asst = form.assigned_assistant_id.data

        pm_id   = normalize_and_validate('Property Manager', raw_pm)
        fc_id   = normalize_and_validate('Financial Controller', raw_fc)
        asst_id = normalize_and_validate('Assistant Property Manager', raw_asst)

        try:
            if (int(raw_pm or 0) != 0) and pm_id is None:
                flash("Invalid Property Manager selection. It has been cleared.", "warning")
            if (int(raw_fc or 0) != 0) and fc_id is None:
                flash("Invalid Financial Controller selection. It has been cleared.", "warning")
            if (int(raw_asst or 0) != 0) and asst_id is None:
                flash("Invalid Assistant selection. It has been cleared.", "warning")
        except Exception:
            pass

        # Consent select → bool
        consent_raw = request.form.get('consent_to_communicate', '')
        consent_to_communicate = str(consent_raw).lower() in ('true', '1', 'yes', 'on')

        # Contract Value: strip commas
        contract_value = form.contract_value.data
        if isinstance(contract_value, str):
            raw = contract_value.replace(',', '').strip()
            if raw == '':
                contract_value = None
            else:
                try:
                    contract_value = Decimal(raw)
                except (InvalidOperation, ValueError):
                    contract_value = None
                    flash("Contract Value could not be parsed. It was saved as empty.", "warning")

        # Optional re-upload
        rel_doc_path = None
        uploaded_mimetype = None
        uploaded_filename = None
        if form.document_file.data:
            file_storage = form.document_file.data
            original = secure_filename(file_storage.filename or '')
            base, ext = os.path.splitext(original)
            ext = ext or '.pdf'
            safe_base = secure_filename(((getattr(form, 'property_name', None) and form.property_name.data) or form.name.data or client.property_name if hasattr(client,'property_name') else client.name or 'client').lower().replace(' ', '_'))
            filename = f"{safe_base}_contract{ext.lower()}"
            abs_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'contracts')
            os.makedirs(abs_dir, exist_ok=True)
            file_storage.save(os.path.join(abs_dir, filename))
            rel_doc_path = os.path.join('uploads', 'contracts', filename).replace('\\', '/')
            uploaded_mimetype = getattr(file_storage, 'mimetype', None)
            uploaded_filename = filename

        # JSON-like fields
        ownership_types = form.ownership_types.data or []
        if isinstance(ownership_types, str):
            try:
                ownership_types = json.loads(ownership_types)
            except Exception:
                ownership_types = [ownership_types] if ownership_types else []

        ai_raw = (form.ai_key_clauses.data or '').strip()
        try:
            ai_key_clauses = json.loads(ai_raw) if ai_raw else None
        except Exception:
            ai_key_clauses = None

        # Apply simple fields from form
        form.populate_obj(client)
        client.consent_to_communicate = consent_to_communicate
        client.contract_value = contract_value
        client.ownership_types = ownership_types
        client.ai_key_clauses = ai_key_clauses

        # ✅ Normalise client_type before saving
        client.client_type = normalize_client_type(form.client_type.data or '')

        # Explicitly persist address fields
        if hasattr(client, 'address_line1') and hasattr(form, 'address_line1'):
            client.address_line1 = form.address_line1.data
        if hasattr(client, 'address_line2') and hasattr(form, 'address_line2'):
            client.address_line2 = form.address_line2.data
        if hasattr(client, 'city') and hasattr(form, 'city'):
            client.city = form.city.data
        if hasattr(client, 'property_name') and hasattr(form, 'property_name'):
            client.property_name = form.property_name.data

        # --- number_of_units: compute on server if breakdown present ---
        posted_total = _to_int(request.form.get('number_of_units'))
        parts_total = (
            _to_int(request.form.get('units_apartments'))
            + _to_int(request.form.get('units_houses'))
            + _to_int(request.form.get('units_duplexes'))
            + _to_int(request.form.get('units_commercial'))
        )
        if parts_total > 0 and (posted_total == 0 or posted_total != parts_total):
            client.number_of_units = parts_total
        else:
            # keep posted total if provided, otherwise leave existing value
            client.number_of_units = posted_total or client.number_of_units

        # 🔁 Transfer of common area (bool + date)
        # Prefer the visible select (transfer_of_common_area_select) when present
        sel = (request.form.get('transfer_of_common_area_select') or '').lower()
        if sel in ('true', 'false'):
            client.transfer_of_common_area = (sel == 'true')
        else:
            # fall back to the hidden boolean field
            val = (request.form.get(getattr(form.transfer_of_common_area, 'name', 'transfer_of_common_area')) or '')
            client.transfer_of_common_area = str(val).lower() in ('y', 'true', '1', 'yes', 'on')

        # Date field from <input type="date"> comes as YYYY-MM-DD
        posted_transfer_date = (request.form.get('transfer_of_common_area_date') or '').strip()
        if posted_transfer_date:
            try:
                client.transfer_of_common_area_date = datetime.strptime(posted_transfer_date, '%Y-%m-%d').date()
            except ValueError:
                flash('Transfer Completion Date format was invalid and was not saved.', 'warning')
        else:
            # Clear if empty submission
            if hasattr(client, 'transfer_of_common_area_date'):
                client.transfer_of_common_area_date = None

        # 🗓️ Financial Year End: accept "DD/MM" text, or clear if blank
        if raw_fye != '':
            if fye_pattern.match(raw_fye):
                client.financial_year_end = raw_fye
            else:
                flash('Financial Year End must be DD/MM (e.g. 31/12). It was not changed.', 'warning')
        else:
            client.financial_year_end = None

        # Overwrite FK fields with sanitized IDs (None, not 0)
        if hasattr(client, 'assigned_pm_id'):
            client.assigned_pm_id = pm_id
        if hasattr(client, 'assigned_fc_id'):
            client.assigned_fc_id = fc_id
        if hasattr(client, 'assigned_assistant_id'):
            client.assigned_assistant_id = asst_id

        # Document row if uploaded
        if rel_doc_path:
            doc = Document(
                file_name=uploaded_filename or os.path.basename(rel_doc_path),
                file_type=(uploaded_mimetype or os.path.splitext(rel_doc_path)[1].lstrip('.').lower() or 'file'),
                file_path=rel_doc_path,
                category="Client Contract",
                description="Uploaded via Edit Client",
                uploaded_by=getattr(current_user, 'id', None),
                upload_date=datetime.utcnow(),
                linked_client_id=client.id,
                version='1.0',
                is_current_version=True,
                access_scope='private'
            )
            db.session.add(doc)

        db.session.commit()
        flash('✅ Client updated successfully.', 'success')
        return redirect(url_for('super_admin.manage_clients'))

    elif request.method == 'POST':
        # Show validation errors (so you can spot any other blockers)
        for field, errs in (form.errors or {}).items():
            for e in errs:
                flash(f"{field}: {e}", "danger")

    # Read-only client code preview (if the model has it)
    preview_client_code = getattr(client, 'client_code', None)

    return render_template('super_admin/client/edit_client.html', form=form, client=client, preview_client_code=preview_client_code)
