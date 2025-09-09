from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime  # NEW

from app.models import db, Client, User
# NEW: use your core Document model (fallback path included for safety)
try:
    from app.models.core.document import Document
except Exception:
    from app.models.document import Document

from app.forms.client.client_create_form import ClientCreateForm
from app.decorators.role import super_admin_required
from app.routes.super_admin import super_admin_bp
from app.utils.audit import log_change
from app.services.capex.capex_service import recompute_capex_profile

# 🔁 Prefer the real helper, but fall back to safe stubs if the module is missing
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
    """Return a canonical country code/name token for downstream lookups."""
    if not val:
        return ''
    v = val.strip().lower()
    return COUNTRY_ALIASES.get(v, val).upper()

# -----------------------------
# Lookup helpers
# -----------------------------
def mgmt_types_for(country: str) -> list[str]:
    """
    Return canonical client types aligned with jurisdictions.json.
    (We avoid legacy phrasing like “Owner Management Company (OMC)”.)
    """
    c = (country or '').strip().lower()

    # Ireland
    if c in ('ireland', 'ie', 'republic of ireland'):
        return ['OMC', 'Commercial Management Company', 'Mixed-Use']

    # United Kingdom (E&W general)
    if c in ('united kingdom', 'uk', 'great britain', 'gb', 'england', 'wales'):
        return ['RMC', 'RTM Company', 'Commonhold Association']

    # Scotland
    if c == 'scotland':
        return ['Owners’ Association', 'Property Factor']

    # Northern Ireland
    if c in ('northern ireland', 'ni'):
        return ['Owners’ Association', 'Management Company']

    # United States
    if c in ('united states', 'united states of america', 'usa', 'us'):
        return ['HOA', 'Condo Association', 'Co-op Board']

    # Canada
    if c in ('canada', 'ca'):
        return ['Condo Corp.', 'Strata', 'HOA']

    # Australia
    if c in ('australia', 'au'):
        return ['Owners Corporation', 'Strata', 'Community Association']

    # New Zealand
    if c in ('new zealand', 'nz'):
        return ['Body Corporate', 'Strata', 'Manager']

    # Singapore
    if c in ('singapore', 'sg'):
        return ['MCST']  # Management Corporation Strata Title

    # Hong Kong
    if c in ('hong kong', 'hk', 'hong kong sar'):
        return ["Owners’ Corporation"]

    # UAE (generic, incl. emirates)
    if c in ('united arab emirates', 'uae', 'u.a.e', 'dubai', 'abu dhabi', 'sharjah', 'ajman',
             'umm al-quwain', 'ras al khaimah', 'fujairah'):
        return ['Owners Association', 'Master Community']

    # Broad EU/EEA fallback
    if c in ('austria','belgium','bulgaria','croatia','cyprus','czech republic','czechia','denmark',
             'estonia','finland','france','germany','greece','hungary','iceland','italy','latvia',
             'lithuania','luxembourg','malta','netherlands','norway','poland','portugal','romania',
             'slovakia','slovenia','spain','sweden','switzerland','liechtenstein'):
        return ['Owners’ Association', 'Management Company']

    # Default
    return ['Management Company', 'Owners’ Association']

def generate_client_code(company_id: int | None) -> str:
    """
    Simple sequential code per company. Adjust to your own logic/format later.
    Safe to call before model migration; assignment guarded via hasattr.
    """
    q = Client.query
    if company_id:
        q = q.filter(Client.company_id == company_id)
    count = q.count() + 1
    prefix = f"C{company_id:03d}" if company_id else "C000"
    return f"{prefix}-{count:05d}"

@super_admin_bp.route('/clients/add/', methods=['GET', 'POST'], endpoint='add_client')
@login_required
@super_admin_required
def add_client():
    form = ClientCreateForm()

    # --- Populate dropdowns (PM / FC / Assistant) ---
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

    form.assigned_pm_id.choices = [(0, '— Select —')] + [(u.id, u.full_name) for u in pm_query.all()]
    form.assigned_fc_id.choices = [(0, '— Select —')] + [(u.id, u.full_name) for u in fc_query.all()]
    form.assigned_assistant_id.choices = [(0, '— Select —')] + [(u.id, u.full_name) for u in asst_query.all()]

    # Country config placeholder
    form.country_config_id.choices = [(0, 'None')]

    # -------------------------------
    # Client Type choices (GET & POST)
    # -------------------------------
    country_input_raw = (request.form.get('country') if request.method == 'POST' else form.country.data) or ''
    country_key = canonical_country(country_input_raw)

    raw_types = mgmt_types_for(country_key) or []
    choices = [('', '— Select —')] + normalized_choice_list(raw_types)

    # If browser posted a value (legacy or variant), normalise and allow it
    if request.method == 'POST':
        posted_type = (request.form.get('client_type') or '').strip()
        posted_norm = normalize_client_type(posted_type) if posted_type else ''
        existing_values = {v for v, _ in choices}
        if posted_norm and posted_norm not in existing_values:
            choices.append((posted_norm, posted_norm))

    form.client_type.choices = choices

    if request.method == 'GET' and len(form.assigned_pm_id.choices) <= 1:
        flash("No Property Managers found for your company. Add a PM user first.", "warning")

    preview_client_code = generate_client_code(getattr(current_user, 'company_id', None))

    if request.method == 'POST' and form.validate_on_submit():
        if not current_user.company_id:
            flash("Your account isn’t linked to a company. Please contact support.", "danger")
            return redirect(url_for('super_admin.dashboard'))
        company_id = current_user.company_id

        # Normalize assignments (0 = None)
        pm_id = form.assigned_pm_id.data or 0
        fc_id = form.assigned_fc_id.data or 0
        asst_id = form.assigned_assistant_id.data or 0

        # Validate only if > 0
        def validate_role(role_name: str, user_id: int | None):
            if not user_id or user_id == 0:
                return None
            user = (
                User.query.join(User.role)
                .filter(
                    User.id == user_id, User.is_active.is_(True),
                    User.company_id == company_id,
                    User.role.has(name=role_name)
                ).first()
            )
            return user.id if user else None

        pm_id = validate_role('Property Manager', pm_id)
        fc_id = validate_role('Financial Controller', fc_id)
        asst_id = validate_role('Assistant Property Manager', asst_id)

        # Consent Yes/No select → boolean
        consent_raw = request.form.get('consent_to_communicate', '')
        consent_to_communicate = str(consent_raw).lower() in ('true', '1', 'yes', 'on')

        # Contract Value: strip commas → Decimal or None
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

        # File upload (optional)
        rel_doc_path = None
        uploaded_mimetype = None  # NEW
        uploaded_filename = None  # NEW
        if form.document_file.data:
            file_storage = form.document_file.data
            original = secure_filename(file_storage.filename or '')
            base, ext = os.path.splitext(original)
            ext = ext or '.pdf'
            safe_base = secure_filename(((getattr(form, 'property_name', None) and form.property_name.data) or form.name.data or 'client').lower().replace(' ', '_'))
            filename = f"{safe_base}_contract{ext.lower()}"
            abs_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'contracts')
            os.makedirs(abs_dir, exist_ok=True)
            file_storage.save(os.path.join(abs_dir, filename))
            rel_doc_path = os.path.join('uploads', 'contracts', filename).replace('\\', '/')
            uploaded_mimetype = getattr(file_storage, 'mimetype', None)  # NEW
            uploaded_filename = filename  # NEW

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

        # Build Client (safe for evolving models)
        client = Client(
            company_id=company_id,
            # Core (existing)
            name=form.name.data,
            address=getattr(form, 'address', None).data if hasattr(form, 'address') else None,
            postal_code=form.postal_code.data,
            registration_number=form.registration_number.data,
            vat_reg_number=form.vat_reg_number.data,
            tax_number=form.tax_number.data,
            year_of_construction=form.year_of_construction.data,
            number_of_units=form.number_of_units.data,
            client_type=normalize_client_type(form.client_type.data or ''),  # ✅ normalised
            contract_value=contract_value,
            # Governance
            financial_year_end=form.financial_year_end.data,
            last_agm_date=form.last_agm_date.data,
            agm_completed=form.agm_completed.data,
            # Jurisdiction
            country=form.country.data,
            region=form.region.data,
            currency=form.currency.data,
            timezone=form.timezone.data,
            preferred_language=form.preferred_language.data,
            ownership_type=form.ownership_type.data,
            # Compliance
            transfer_of_common_area=form.transfer_of_common_area.data,
            deed_of_covenants=form.deed_of_covenants.data,
            data_protection_compliance=form.data_protection_compliance.data,
            consent_to_communicate=consent_to_communicate,
            resident_logic=form.resident_logic.data,
            enforce_gdpr=form.enforce_gdpr.data,
            default_visibility_scope=form.default_visibility_scope.data,
            # Structure
            min_directors=form.min_directors.data,
            max_directors=form.max_directors.data,
            number_of_blocks=form.number_of_blocks.data,
            block_names=form.block_names.data,
            cores_per_block=form.cores_per_block.data,
            apartments_per_block=form.apartments_per_block.data,
            # Valuation
            reinstatement_value=form.reinstatement_value.data,
            reinstatement_valuation_date=form.reinstatement_valuation_date.data,
            # Uploads / AI Parse
            # REMOVED: document_path=rel_doc_path,  # ❌ was causing TypeError if model lacks this field
            ownership_types=ownership_types,
            ai_key_clauses=ai_key_clauses,
            tags=form.tags.data,
            # CAPEX (status-only at onboarding)
            capex_profile=None,
            capex_status=form.capex_status.data,
            # GAR / AI meta
            ai_governance_summary=form.ai_governance_summary.data,
            ai_flagged_risks=form.ai_flagged_risks.data,
            ai_advice_summary=form.ai_advice_summary.data,
            ai_review_comment=form.ai_review_comment.data,
            is_gar_monitored=form.is_gar_monitored.data,
            gar_chat_ready=form.gar_chat_ready.data,
            gar_resolution_status=form.gar_resolution_status.data,
            # Country-specific config
            country_config_id=(form.country_config_id.data if form.country_config_id.data != 0 else None),
        )

        # Assign new/conditional fields only if model has them
        if hasattr(client, 'property_name'):
            client.property_name = getattr(form, 'property_name', None).data if hasattr(form, 'property_name') else None
        if hasattr(client, 'address_line1'):
            client.address_line1 = getattr(form, 'address_line1', None).data if hasattr(form, 'address_line1') else None
        if hasattr(client, 'address_line2'):
            client.address_line2 = getattr(form, 'address_line2', None).data if hasattr(form, 'address_line2') else None
        if hasattr(client, 'city'):
            client.city = getattr(form, 'city', None).data if hasattr(form, 'city') else None
        if hasattr(client, 'client_code'):
            client.client_code = generate_client_code(company_id)

        # Assign FKs (only if columns exist)
        if hasattr(client, 'assigned_pm_id'):
            client.assigned_pm_id = pm_id
        if hasattr(client, 'assigned_fc_id'):
            client.assigned_fc_id = fc_id
        if hasattr(client, 'assigned_assistant_id'):
            client.assigned_assistant_id = asst_id

        try:
            db.session.add(client)
            db.session.flush()  # NEW: get client.id before creating Document

            # NEW: create Document row if a file was uploaded
            if rel_doc_path:
                doc = Document(
                    file_name=uploaded_filename or os.path.basename(rel_doc_path),
                    file_type=(uploaded_mimetype or os.path.splitext(rel_doc_path)[1].lstrip('.').lower() or 'file'),
                    file_path=rel_doc_path,
                    category="Client Contract",
                    description="Uploaded via Add Client",
                    uploaded_by=getattr(current_user, 'id', None),
                    upload_date=datetime.utcnow(),
                    linked_client_id=client.id,
                    version='1.0',
                    is_current_version=True,
                    access_scope='private'
                )
                db.session.add(doc)

            db.session.commit()

            try:
                log_change(
                    action="client_create",
                    user_id=current_user.id,
                    meta={
                        "client_id": client.id,
                        "client_name": client.name,
                        "company_id": company_id,
                        "assigned_pm_id": pm_id,
                        "assigned_fc_id": fc_id,
                        "assigned_assistant_id": asst_id,
                        "client_code": getattr(client, 'client_code', None),
                    },
                )
            except Exception:
                pass

            try:
                recompute_capex_profile(client_id=client.id, actor_user_id=current_user.id)
            except Exception:
                pass

            flash('✅ Client added successfully.', 'success')
            return redirect(url_for('super_admin.manage_clients'))
        except Exception as e:
            db.session.rollback()
            flash(f"Could not create client: {e}", "danger")

    # GET or invalid POST
    return render_template('super_admin/client/add_client.html', form=form, preview_client_code=preview_client_code)
