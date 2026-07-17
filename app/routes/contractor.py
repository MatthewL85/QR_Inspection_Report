import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, Response, render_template, session, request, current_app, flash, redirect, url_for, jsonify, abort, send_file
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from app.extensions import db
from app.helpers.decorators import login_required
from app.models import ContractorComplianceDocument
from app.models.contractor.contractor_team import ContractorTeam
from app.models.contractor.job_docket import JobDocket, JobDocketPrivateWorkLog
from app.models.core.document_template import CoreDocumentTemplate
from app.models.core.user import User
from app.models.onboarding.bank_account import BankAccount
from app.models.onboarding.insurance_policy import InsurancePolicy
from app.services.gar import (
    attach_gar_capability_readiness,
    build_gar_inquiry_response,
    build_contractor_role_digest,
    build_work_order_relevant_history,
)
from app.services.core.contractor_access import contractor_portal_denial_reason
from app.services.core.document_template_service import (
    DOCUMENT_TEMPLATE_DEFAULTS,
    document_template_catalog,
    document_template_preview_payload,
    get_document_template_payload,
)
from app.services.core.module_connections import module_connection_context
from app.services.core.module_settings_registry import module_settings_by_key
from app.services.core.organisation_identity import (
    accept_organisation_connection_invite,
    create_organisation_connection_invite,
)
from app.services.works.workflow_service import (
    ContractorWorkFilters,
    WORK_ORDER_PROGRESS_VISIBILITY,
    WORK_ORDER_UPDATE_TYPES,
    add_work_order_progress_update,
    build_work_order_lifecycle_for_audience,
    build_work_order_return_context,
    build_work_order_review_cycle,
    contractor_work_queue_payload,
    contractor_update_work_order,
    get_contractor_work_orders,
    progress_updates_for_audience,
    record_work_order_lifecycle_event,
    submit_quote_response,
    update_quote_recipient_decision,
)
from app.services.contractor.job_docket_service import (
    build_standalone_job_docket_pack,
    build_job_docket_document_payload,
    build_payment_request_document_payload,
    build_contractor_calendar_ics,
    calendar_context,
    contractor_calendar_entries_for_ics,
    contractor_schedule_feed_payload,
    contractor_today_schedule_context,
    create_standalone_job_docket,
    schedule_job_docket,
)
from app.services.works.audit_pack_service import build_completion_evidence_pack
from app.models.works.quote_recipient import QuoteRecipient
from app.models.works.quote_response import QuoteResponse
from app.models.works.work_order import WorkOrder
from app.services.works.work_order_docket_service import (
    build_contractor_work_order_docket,
    render_contractor_work_order_pdf,
)

contractor_bp = Blueprint('contractor', __name__)

CONTRACTOR_EVIDENCE_UPLOAD_EXTENSIONS = {
    "jpg", "jpeg", "png", "gif", "webp", "heic",
    "mp4", "mov", "webm", "avi", "m4v",
    "pdf", "doc", "docx", "xls", "xlsx", "csv",
}


def _save_contractor_evidence_upload(file_storage, work_order_id: int) -> str | None:
    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename)
    if not filename or "." not in filename:
        return None

    extension = filename.rsplit(".", 1)[-1].lower()
    if extension not in CONTRACTOR_EVIDENCE_UPLOAD_EXTENSIONS:
        return None

    upload_dir = os.path.join(current_app.static_folder, "uploads", "contractor_evidence", str(work_order_id))
    os.makedirs(upload_dir, exist_ok=True)
    stored_name = f"{os.urandom(8).hex()}.{extension}"
    file_storage.save(os.path.join(upload_dir, stored_name))
    return f"/static/uploads/contractor_evidence/{work_order_id}/{stored_name}"


def _save_contractor_evidence_uploads(file_storages, work_order_id: int) -> tuple[list[str], list[str]]:
    uploaded_references: list[str] = []
    unsupported_filenames: list[str] = []
    for file_storage in file_storages or []:
        if not file_storage or not file_storage.filename:
            continue
        uploaded_reference = _save_contractor_evidence_upload(file_storage, work_order_id)
        if uploaded_reference:
            uploaded_references.append(uploaded_reference)
        else:
            unsupported_filenames.append(file_storage.filename)
    return uploaded_references, unsupported_filenames


def _save_contractor_docket_upload(file_storage, docket_id: int) -> str | None:
    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename)
    if not filename or "." not in filename:
        return None

    extension = filename.rsplit(".", 1)[-1].lower()
    if extension not in CONTRACTOR_EVIDENCE_UPLOAD_EXTENSIONS:
        return None

    upload_dir = os.path.join(current_app.static_folder, "uploads", "contractor_dockets", str(docket_id))
    os.makedirs(upload_dir, exist_ok=True)
    stored_name = f"{os.urandom(8).hex()}.{extension}"
    file_storage.save(os.path.join(upload_dir, stored_name))
    return f"/static/uploads/contractor_dockets/{docket_id}/{stored_name}"


def _save_contractor_docket_uploads(file_storages, docket_id: int) -> tuple[list[str], list[str]]:
    uploaded_references: list[str] = []
    unsupported_filenames: list[str] = []
    for file_storage in file_storages or []:
        if not file_storage or not file_storage.filename:
            continue
        uploaded_reference = _save_contractor_docket_upload(file_storage, docket_id)
        if uploaded_reference:
            uploaded_references.append(uploaded_reference)
        else:
            unsupported_filenames.append(file_storage.filename)
    return uploaded_references, unsupported_filenames


def _save_contractor_quote_upload(file_storage, work_order_id: int) -> str | None:
    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename)
    if not filename or "." not in filename:
        return None

    extension = filename.rsplit(".", 1)[-1].lower()
    if extension not in CONTRACTOR_EVIDENCE_UPLOAD_EXTENSIONS:
        return None

    upload_dir = os.path.join(current_app.static_folder, "uploads", "contractor_quotes", str(work_order_id))
    os.makedirs(upload_dir, exist_ok=True)
    stored_name = f"{os.urandom(8).hex()}.{extension}"
    file_storage.save(os.path.join(upload_dir, stored_name))
    return f"/static/uploads/contractor_quotes/{work_order_id}/{stored_name}"


def _save_contractor_quote_uploads(file_storages, work_order_id: int) -> tuple[list[str], list[str]]:
    uploaded_references: list[str] = []
    unsupported_filenames: list[str] = []
    for file_storage in file_storages or []:
        if not file_storage or not file_storage.filename:
            continue
        uploaded_reference = _save_contractor_quote_upload(file_storage, work_order_id)
        if uploaded_reference:
            uploaded_references.append(uploaded_reference)
        else:
            unsupported_filenames.append(file_storage.filename)
    return uploaded_references, unsupported_filenames


@contractor_bp.route('/dashboard')
@login_required(role='Contractor')
def contractor_dashboard():
    user = User.query.get(session.get('user_id'))
    if contractor_portal_denial_reason(user):
        flash('Contractor Logix is only available to contractor company users.', 'danger')
        return redirect(url_for('auth.login'))

    work_data = get_contractor_work_orders(user.contractor_id, user.id) if user and user.contractor_id else None
    calendar_data = calendar_context(user.contractor_id) if user and user.contractor_id else None
    gar_question = (request.args.get("gar_question") or "").strip()
    gar_inquiry_response = None
    if gar_question:
        gar_inquiry_response = build_gar_inquiry_response(
            gar_question,
            role_context="contractor",
            company_id=getattr(user, "company_id", None),
            user_id=getattr(user, "id", None),
            execute_source_query=True,
        )
    return render_template(
        'contractor_dashboard.html',
        work_data=work_data,
        calendar_data=calendar_data,
        gar_question=gar_question,
        gar_inquiry_response=gar_inquiry_response,
    )


def _current_contractor_user():
    user = User.query.get(session.get('user_id'))
    if contractor_portal_denial_reason(user):
        return None
    return user


def _contractor_work_filters():
    return ContractorWorkFilters(
        search=(request.args.get('search') or request.form.get('search') or '').strip(),
        status=(request.args.get('status') or request.form.get('status') or '').strip(),
    )


def _contractor_filter_args():
    return {
        key: value
        for key in ("search", "status", "queue")
        if (value := (request.form.get(key) or request.args.get(key) or "").strip())
    }


def _contractor_detail_redirect(work_order: WorkOrder, *, fallback_args: dict | None = None):
    return_to = (request.form.get("return_to") or request.args.get("return_to") or "").strip()
    if return_to == "docket" and work_order.job_docket:
        return redirect(url_for("contractor.job_docket_detail", docket_id=work_order.job_docket.id))
    if return_to == "detail":
        return redirect(url_for("contractor.work_order_detail", work_order_id=work_order.id))
    return redirect(url_for("contractor.work_orders", **(fallback_args or _contractor_filter_args())))


def _form_int(name: str) -> int | None:
    value = (request.form.get(name) or request.args.get(name) or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _form_decimal(name: str) -> Decimal | None:
    value = (request.form.get(name) or "").strip()
    if not value:
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return None
    return parsed if parsed >= 0 else None


@contractor_bp.route('/job-dockets/new', methods=['GET', 'POST'], endpoint='new_job_docket')
@login_required(role='Contractor')
def new_job_docket():
    user = _current_contractor_user()
    if not user:
        flash('Your contractor profile is not linked yet.', 'warning')
        return redirect(url_for('contractor.contractor_dashboard'))

    if request.method == 'POST':
        client_name = (request.form.get('client_name') or '').strip()
        scope_of_works = (request.form.get('scope_of_works') or '').strip()
        if not client_name or not scope_of_works:
            flash('Client name and work details are required before creating a standalone job docket.', 'warning')
            return render_template('contractor/job_docket_form.html', form=request.form)

        docket = create_standalone_job_docket(
            contractor_id=user.contractor_id,
            company_id=getattr(user, "company_id", None),
            created_by_id=user.id,
            external_work_order_reference=(request.form.get('external_work_order_reference') or '').strip(),
            client_name=client_name,
            property_name=(request.form.get('property_name') or '').strip(),
            address_line_1=(request.form.get('address_line_1') or '').strip(),
            address_line_2=(request.form.get('address_line_2') or '').strip(),
            town_city=(request.form.get('town_city') or '').strip(),
            region=(request.form.get('region') or '').strip(),
            postal_code=(request.form.get('postal_code') or '').strip(),
            country=(request.form.get('country') or '').strip(),
            block_name=(request.form.get('block_name') or '').strip(),
            core_name=(request.form.get('core_name') or '').strip(),
            unit_number=(request.form.get('unit_number') or '').strip(),
            required_trade=(request.form.get('required_trade') or '').strip(),
            priority=(request.form.get('priority') or '').strip(),
            scope_of_works=scope_of_works,
            access_notes=(request.form.get('access_notes') or '').strip(),
            contact_name=(request.form.get('contact_name') or '').strip(),
            contact_phone=(request.form.get('contact_phone') or '').strip(),
            contact_email=(request.form.get('contact_email') or '').strip(),
            instruction_source=(request.form.get('instruction_source') or 'Manual Instruction').strip(),
        )
        uploaded_references, unsupported_filenames = _save_contractor_docket_uploads(
            request.files.getlist("docket_files"),
            docket.id,
        )
        if uploaded_references:
            docket.evidence_links = uploaded_references
            docket.attachments_count = len(uploaded_references)
        if unsupported_filenames:
            flash(
                f"Some files were not attached because their type is not supported: {', '.join(unsupported_filenames)}.",
                'warning',
            )
        db.session.commit()
        flash('Standalone job docket created. Add it to the Contractor Calendar when ready.', 'success')
        return redirect(url_for('contractor.job_docket_detail', docket_id=docket.id))

    return render_template('contractor/job_docket_form.html', form={})


@contractor_bp.route('/work-orders')
@login_required(role='Contractor')
def work_orders():
    user = _current_contractor_user()
    if not user:
        flash('Your contractor profile is not linked yet.', 'warning')
        return redirect(url_for('contractor.contractor_dashboard'))

    filters = _contractor_work_filters()
    selected_queue = (request.args.get("queue") or request.form.get("queue") or "assigned").strip().lower()
    if selected_queue not in {"assigned", "quote_requests", "active", "submitted", "returned", "to_be_invoiced", "closed"}:
        selected_queue = "assigned"
    data = get_contractor_work_orders(user.contractor_id, user.id, filters=filters)
    data["lifecycle_by_work_order"] = {
        item.id: build_work_order_lifecycle_for_audience(item, "contractor")
        for item in data.get("work_orders", [])
    }
    data["gar_history_by_work_order"] = {
        item.id: build_work_order_relevant_history(
            item.id,
            audience="contractor",
            _work_order=item,
        )
        for item in data.get("work_orders", [])
    }
    data["completion_evidence_by_work_order"] = {
        item.id: build_completion_evidence_pack(item.completion)
        for item in data.get("work_orders", [])
    }
    data["return_context_by_work_order"] = {
        item.id: build_work_order_return_context(item)
        for item in data.get("work_orders", [])
    }
    data["review_cycle_by_work_order"] = {
        item.id: build_work_order_review_cycle(item)
        for item in data.get("work_orders", [])
    }
    data["progress_updates_by_work_order"] = {
        item.id: progress_updates_for_audience(item, "contractor")
        for item in data.get("work_orders", [])
    }
    return render_template('contractor/work_orders.html', filters=filters, selected_queue=selected_queue, **data)


def _contractor_work_order_or_404(work_order_id: int) -> tuple[User, WorkOrder]:
    user = _current_contractor_user()
    if not user:
        abort(403)

    work_order = WorkOrder.query.filter(WorkOrder.id == work_order_id).first_or_404()
    has_direct_assignment = work_order.contractor_id == user.contractor_id
    has_quote_invite = QuoteRecipient.query.filter_by(
        work_order_id=work_order.id,
        contractor_id=user.id,
        visible_to_contractor=True,
        archived_by_admin=False,
    ).first() is not None
    if not has_direct_assignment and not has_quote_invite:
        abort(404)
    return user, work_order


@contractor_bp.route('/work-orders/<int:work_order_id>', endpoint='work_order_detail')
@login_required(role='Contractor')
def work_order_detail(work_order_id):
    user, work_order = _contractor_work_order_or_404(work_order_id)
    can_manage_work_order = work_order.contractor_id == user.contractor_id
    quote_invite = QuoteRecipient.query.filter_by(
        work_order_id=work_order.id,
        contractor_id=user.id,
        visible_to_contractor=True,
        archived_by_admin=False,
    ).first()
    if quote_invite and not quote_invite.contractor_viewed:
        quote_invite.contractor_viewed = True
        quote_invite.contractor_viewed_at = datetime.utcnow()
        db.session.commit()
    quote_response = QuoteResponse.query.filter_by(
        work_order_id=work_order.id,
        contractor_id=user.id,
    ).first() if quote_invite else None
    quote_response_status = (getattr(quote_response, "status", "") or "").strip()
    quote_invite_response = (getattr(quote_invite, "response_status", "") or "").strip()
    quote_is_terminal = bool(
        quote_invite
        and (
            quote_invite.status == "Closed"
            or quote_invite_response in {"Approved", "Not Selected", "No Response", "Withdrawn"}
            or quote_response_status in {"Approved", "Not Selected", "Archived", "Recalled"}
            or (work_order.quote_status or "") == "Approved"
        )
    )
    active_quote_invite = bool(quote_invite and not quote_is_terminal)
    quote_outcome = None
    if quote_invite and quote_is_terminal:
        if quote_invite_response == "Approved" or quote_response_status == "Approved" or (
            can_manage_work_order and (work_order.quote_status or "") == "Approved"
        ):
            quote_outcome = "selected"
        elif quote_invite_response == "No Response":
            quote_outcome = "closed"
        else:
            quote_outcome = "not_selected"
    docket = build_contractor_work_order_docket(work_order, audience="contractor")
    return render_template(
        'contractor/work_order_detail.html',
        docket=docket,
        quote_invite=quote_invite,
        quote_response=quote_response,
        active_quote_invite=active_quote_invite,
        quote_outcome=quote_outcome,
        can_manage_work_order=can_manage_work_order,
        progress_updates=progress_updates_for_audience(work_order, "contractor"),
    )


@contractor_bp.route('/work-orders/<int:work_order_id>/quote-invite/<action>', methods=['POST'], endpoint='quote_invite_action')
@login_required(role='Contractor')
def quote_invite_action(work_order_id, action):
    user, work_order = _contractor_work_order_or_404(work_order_id)
    quote_invite = QuoteRecipient.query.filter_by(
        work_order_id=work_order.id,
        contractor_id=user.id,
        visible_to_contractor=True,
        archived_by_admin=False,
    ).first()
    if not quote_invite or quote_invite.status == "Closed" or (work_order.quote_status or "") == "Approved":
        flash('That quotation request has already been decided.', 'info')
        return redirect(url_for('contractor.work_order_detail', work_order_id=work_order.id))

    recipient = update_quote_recipient_decision(
        work_order_id=work_order.id,
        contractor_user_id=user.id,
        action=action,
        note=(request.form.get("decision_feedback") or "").strip(),
    )
    if not recipient:
        flash('That quotation request could not be updated.', 'warning')
    elif action == "decline":
        flash('Quotation request declined and returned to Works Logix.', 'success')
    else:
        flash('Quotation request marked as under review.', 'success')
    return redirect(url_for('contractor.work_orders', queue='quote_requests'))


@contractor_bp.route('/work-orders/<int:work_order_id>/submit-quote', methods=['POST'], endpoint='submit_quote')
@login_required(role='Contractor')
def submit_quote(work_order_id):
    user, work_order = _contractor_work_order_or_404(work_order_id)
    quote_invite = QuoteRecipient.query.filter_by(
        work_order_id=work_order.id,
        contractor_id=user.id,
        visible_to_contractor=True,
        archived_by_admin=False,
    ).first()
    if not quote_invite:
        flash('That quotation request could not be found.', 'warning')
        return redirect(url_for('contractor.work_orders', queue='quote_requests'))
    if quote_invite.status == "Closed" or (work_order.quote_status or "") == "Approved":
        flash('That quotation request has already been decided.', 'info')
        return redirect(url_for('contractor.work_order_detail', work_order_id=work_order.id))

    quote_file_path = _save_contractor_quote_upload(request.files.get("quote_file"), work_order.id)
    if not quote_file_path:
        flash('Attach the main quote file before submitting.', 'warning')
        return redirect(url_for('contractor.work_order_detail', work_order_id=work_order.id))

    additional_files, unsupported_filenames = _save_contractor_quote_uploads(
        request.files.getlist("quote_supporting_files"),
        work_order.id,
    )
    if unsupported_filenames:
        flash(
            f"Some supporting files were not attached because their type is not supported: {', '.join(unsupported_filenames)}.",
            'warning',
        )

    response = submit_quote_response(
        work_order_id=work_order.id,
        contractor_user_id=user.id,
        quote_file_path=quote_file_path,
        additional_files=additional_files,
        parsed_total=_form_decimal("quote_total"),
        parsed_summary=(request.form.get("quote_summary") or "").strip(),
        decision_note=(request.form.get("quote_note") or "").strip(),
    )
    if not response:
        flash('That quotation could not be submitted.', 'danger')
        return redirect(url_for('contractor.work_order_detail', work_order_id=work_order.id))

    flash('Quotation submitted to Works Logix for review.', 'success')
    return redirect(url_for('contractor.work_orders', queue='quote_requests'))


@contractor_bp.route('/work-orders/<int:work_order_id>/pdf', endpoint='work_order_pdf')
@login_required(role='Contractor')
def work_order_pdf(work_order_id):
    _user, work_order = _contractor_work_order_or_404(work_order_id)
    docket = build_contractor_work_order_docket(work_order, audience="contractor")
    if not docket["pdf_ready"]:
        flash('The work order PDF becomes available after you accept the job.', 'warning')
        return redirect(url_for('contractor.work_order_detail', work_order_id=work_order.id))

    pdf_stream = render_contractor_work_order_pdf(work_order)
    return send_file(
        pdf_stream,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{work_order.display_reference}-contractor-pack.pdf",
    )


@contractor_bp.route('/work-orders/feed.json', endpoint='work_orders_feed')
@login_required(role='Contractor')
def work_orders_feed():
    user = _current_contractor_user()
    if not user:
        return jsonify({"error": "contractor_profile_not_linked"}), 403

    filters = _contractor_work_filters()
    data = get_contractor_work_orders(user.contractor_id, user.id, filters=filters)
    return jsonify(contractor_work_queue_payload(data, filters))


@contractor_bp.route('/gar/feed.json', endpoint='gar_feed')
@login_required(role='Contractor')
def gar_feed():
    user = _current_contractor_user()
    if not user:
        return jsonify({"error": "contractor_profile_not_linked"}), 403

    data = get_contractor_work_orders(user.contractor_id, user.id, filters=_contractor_work_filters())
    payload = build_contractor_role_digest(user, data)
    return jsonify(attach_gar_capability_readiness(
        payload,
        role_context="contractor",
        question=(request.args.get("question") or "").strip() or None,
    ))


@contractor_bp.route('/gar/inquiry.json', endpoint='gar_inquiry')
@login_required(role='Contractor')
def gar_inquiry():
    user = _current_contractor_user()
    if not user:
        return jsonify({"error": "contractor_profile_not_linked"}), 403

    return jsonify(build_gar_inquiry_response(
        (request.args.get("question") or request.args.get("gar_question") or "").strip(),
        role_context="contractor",
        company_id=getattr(user, "company_id", None),
        user_id=user.id,
        execute_source_query=True,
    ))


@contractor_bp.route('/work-orders/<int:work_order_id>/<action>', methods=['POST'])
@login_required(role='Contractor')
def update_work_order(work_order_id, action):
    user = _current_contractor_user()
    if not user:
        flash('Your contractor profile is not linked yet.', 'warning')
        return redirect(url_for('contractor.contractor_dashboard'))

    if action not in {'accept', 'reject', 'start', 'complete'}:
        flash('That work order action is not available.', 'danger')
        return redirect(url_for('contractor.work_orders', **_contractor_filter_args()))

    uploaded_references, unsupported_filenames = _save_contractor_evidence_uploads(
        request.files.getlist("evidence_files"),
        work_order_id,
    )
    if unsupported_filenames:
        flash('One or more evidence files are not supported.', 'warning')
        docket_id = _form_int("docket_id")
        if request.form.get('return_to') == 'docket' and docket_id:
            return redirect(url_for('contractor.job_docket_detail', docket_id=docket_id))
        if request.form.get('return_to') == 'detail':
            return redirect(url_for('contractor.work_order_detail', work_order_id=work_order_id))
        return redirect(url_for('contractor.work_orders', **_contractor_filter_args()))

    work_order = contractor_update_work_order(
        work_order_id=work_order_id,
        contractor_id=user.contractor_id,
        user_id=user.id,
        action=action,
        completion_notes=(request.form.get('completion_notes') or '').strip(),
        evidence_reference=(request.form.get('evidence_reference') or '').strip(),
        evidence_references=uploaded_references,
    )
    if not work_order:
        flash('That work order is not assigned to your contractor profile.', 'danger')
        return redirect(url_for('contractor.work_orders', **_contractor_filter_args()))

    messages = {
        'accept': 'Work order accepted.',
        'reject': 'Work order returned to Works Logix.',
        'start': 'Work order marked as in progress.',
        'complete': 'Completion submitted to Works Logix.',
    }
    flash(messages[action], 'success')
    return _contractor_detail_redirect(work_order)


@contractor_bp.route('/work-orders/<int:work_order_id>/progress', methods=['POST'], endpoint='add_progress_update')
@login_required(role='Contractor')
def add_progress_update(work_order_id):
    user = _current_contractor_user()
    if not user:
        flash('Your contractor profile is not linked yet.', 'warning')
        return redirect(url_for('contractor.contractor_dashboard'))

    update_type = (request.form.get('update_type') or '').strip()
    visibility_scope = (request.form.get('visibility_scope') or '').strip()
    if update_type not in WORK_ORDER_UPDATE_TYPES or visibility_scope not in WORK_ORDER_PROGRESS_VISIBILITY:
        flash('Please select an update type and visibility before submitting.', 'warning')
        docket_id = _form_int("docket_id")
        if request.form.get('return_to') == 'docket' and docket_id:
            return redirect(url_for('contractor.job_docket_detail', docket_id=docket_id))
        if request.form.get('return_to') == 'detail':
            return redirect(url_for('contractor.work_order_detail', work_order_id=work_order_id))
        return redirect(url_for('contractor.work_orders', **_contractor_filter_args()))

    uploaded_references, unsupported_filenames = _save_contractor_evidence_uploads(
        request.files.getlist("progress_files"),
        work_order_id,
    )
    if unsupported_filenames:
        flash('One or more progress files are not supported.', 'warning')
        docket_id = _form_int("docket_id")
        if request.form.get('return_to') == 'docket' and docket_id:
            return redirect(url_for('contractor.job_docket_detail', docket_id=docket_id))
        if request.form.get('return_to') == 'detail':
            return redirect(url_for('contractor.work_order_detail', work_order_id=work_order_id))
        return redirect(url_for('contractor.work_orders', **_contractor_filter_args()))

    progress_update = add_work_order_progress_update(
        work_order_id=work_order_id,
        contractor_id=user.contractor_id,
        user_id=user.id,
        note=(request.form.get('progress_note') or '').strip(),
        visibility_scope=visibility_scope,
        update_type=update_type,
        evidence_links=uploaded_references,
    )
    if not progress_update:
        flash('Update could not be saved for this work order.', 'warning')
    else:
        flash('Completion submitted for review.' if progress_update.update_type == 'completion' else 'Update added.', 'success')

    work_order = WorkOrder.query.get(work_order_id)
    if work_order:
        return _contractor_detail_redirect(work_order)
    return redirect(url_for('contractor.work_orders', **_contractor_filter_args()))


@contractor_bp.route('/job-dockets/<int:docket_id>/private-work-log', methods=['POST'], endpoint='add_private_work_log')
@login_required(role='Contractor')
def add_private_work_log(docket_id):
    user = _current_contractor_user()
    if not user:
        flash('Your contractor profile is not linked yet.', 'warning')
        return redirect(url_for('contractor.contractor_dashboard'))

    job_docket = JobDocket.query.filter_by(
        id=docket_id,
        contractor_id=user.contractor_id,
    ).first_or_404()

    try:
        work_date = datetime.strptime(request.form.get('work_date') or '', "%Y-%m-%d").date()
    except ValueError:
        flash('Choose a valid date for the private work log.', 'warning')
        return redirect(url_for('contractor.job_docket_detail', docket_id=docket_id))

    labour_hours = _form_decimal("labour_hours")
    material_quantity = _form_decimal("material_quantity")
    material_cost = _form_decimal("material_cost")
    material_description = (request.form.get("material_description") or "").strip() or None
    material_unit = (request.form.get("material_unit") or "").strip() or None
    notes = (request.form.get("private_notes") or "").strip() or None

    if not any([labour_hours, material_description, material_quantity, material_cost, notes]):
        flash('Add hours, materials or an internal note before saving the materials and time entry.', 'warning')
        return redirect(url_for('contractor.job_docket_detail', docket_id=docket_id))

    private_log = JobDocketPrivateWorkLog(
        job_docket_id=job_docket.id,
        contractor_id=user.contractor_id,
        company_id=getattr(user, "company_id", None),
        created_by_id=user.id,
        work_date=work_date,
        labour_hours=labour_hours,
        material_description=material_description,
        material_quantity=material_quantity,
        material_unit=material_unit,
        material_cost=material_cost,
        notes=notes,
    )
    db.session.add(private_log)
    db.session.commit()
    flash('Materials and time entry saved.', 'success')
    return redirect(url_for('contractor.job_docket_detail', docket_id=docket_id))


@contractor_bp.route('/calendar', endpoint='calendar')
@login_required(role='Contractor')
def calendar():
    user = _current_contractor_user()
    if not user:
        flash('Your contractor profile is not linked yet.', 'warning')
        return redirect(url_for('contractor.contractor_dashboard'))

    filters = {
        "engineer_id": _form_int("engineer_id"),
        "team_id": _form_int("team_id"),
        "status": (request.args.get("status") or "").strip(),
    }
    return render_template(
        'contractor/calendar.html',
        **calendar_context(user.contractor_id, filters=filters),
    )


@contractor_bp.route('/calendar/feed.json', endpoint='calendar_feed')
@login_required(role='Contractor')
def calendar_feed():
    user = _current_contractor_user()
    if not user:
        return jsonify({"error": "contractor_profile_not_linked"}), 403

    filters = {
        "engineer_id": _form_int("engineer_id"),
        "team_id": _form_int("team_id"),
        "status": (request.args.get("status") or "").strip(),
    }
    context = calendar_context(user.contractor_id, filters=filters)
    context["days_ahead"] = _form_int("days_ahead") or 7
    return jsonify(contractor_schedule_feed_payload(context))


@contractor_bp.route('/today', endpoint='today')
@login_required(role='Contractor')
def today():
    user = _current_contractor_user()
    if not user:
        flash('Your contractor profile is not linked yet.', 'warning')
        return redirect(url_for('contractor.contractor_dashboard'))

    return render_template(
        'contractor/today.html',
        **contractor_today_schedule_context(user.contractor_id),
    )


@contractor_bp.route('/job-dockets/<int:docket_id>', endpoint='job_docket_detail')
@login_required(role='Contractor')
def job_docket_detail(docket_id):
    user = _current_contractor_user()
    if not user:
        flash('Your contractor profile is not linked yet.', 'warning')
        return redirect(url_for('contractor.contractor_dashboard'))

    job_docket = JobDocket.query.filter_by(
        id=docket_id,
        contractor_id=user.contractor_id,
    ).first_or_404()
    work_order = job_docket.work_order
    work_pack = (
        build_contractor_work_order_docket(work_order, audience="contractor")
        if work_order
        else build_standalone_job_docket_pack(job_docket)
    )
    selected_quote_response = (
        QuoteResponse.query.filter_by(
            work_order_id=work_order.id,
            is_selected=True,
        ).first()
        if work_order
        else None
    )
    engineers = (
        User.query
        .filter(User.contractor_id == user.contractor_id, User.is_active.is_(True))
        .order_by(User.full_name.asc())
        .all()
    )
    teams = (
        ContractorTeam.query
        .filter(ContractorTeam.contractor_id == user.contractor_id, ContractorTeam.is_active.is_(True))
        .order_by(ContractorTeam.name.asc())
        .all()
    )
    return render_template(
        'contractor/job_docket_detail.html',
        job_docket=job_docket,
        work_order=work_order,
        work_pack=work_pack,
        selected_quote_response=selected_quote_response,
        progress_updates=progress_updates_for_audience(work_order, "contractor") if work_order else [],
        private_work_logs=job_docket.private_work_logs,
        today=datetime.utcnow().date(),
        engineers=engineers,
        teams=teams,
    )


@contractor_bp.route('/job-dockets/<int:docket_id>/document', endpoint='job_docket_document')
@login_required(role='Contractor')
def job_docket_document(docket_id):
    user = _current_contractor_user()
    if not user:
        flash('Your contractor profile is not linked yet.', 'warning')
        return redirect(url_for('contractor.contractor_dashboard'))

    job_docket = JobDocket.query.filter_by(
        id=docket_id,
        contractor_id=user.contractor_id,
    ).first_or_404()
    payload = build_job_docket_document_payload(job_docket)
    return render_template(
        'contractor/job_docket_document.html',
        job_docket=job_docket,
        payload=payload,
        company=payload["render"].get("company") or {},
        document_heading="Job Docket Document Preview",
    )


@contractor_bp.route('/job-dockets/<int:docket_id>/payment-request-document', endpoint='job_docket_payment_request_document')
@login_required(role='Contractor')
def job_docket_payment_request_document(docket_id):
    user = _current_contractor_user()
    if not user:
        flash('Your contractor profile is not linked yet.', 'warning')
        return redirect(url_for('contractor.contractor_dashboard'))

    job_docket = JobDocket.query.filter_by(
        id=docket_id,
        contractor_id=user.contractor_id,
    ).first_or_404()
    payload = build_payment_request_document_payload(job_docket)
    return render_template(
        'contractor/job_docket_document.html',
        job_docket=job_docket,
        payload=payload,
        company=payload["render"].get("company") or {},
        document_heading="Payment Request Preview",
    )


@contractor_bp.route('/job-dockets/<int:docket_id>/invoice-prepared', methods=['POST'], endpoint='mark_job_docket_invoice_prepared')
@login_required(role='Contractor')
def mark_job_docket_invoice_prepared(docket_id):
    user = _current_contractor_user()
    if not user:
        flash('Your contractor profile is not linked yet.', 'warning')
        return redirect(url_for('contractor.contractor_dashboard'))

    job_docket = JobDocket.query.filter_by(
        id=docket_id,
        contractor_id=user.contractor_id,
    ).first_or_404()

    protected_statuses = {"invoice prepared", "invoiced", "paid", "settled"}
    invoice_status_key = (job_docket.invoice_status or "").strip().lower()
    if invoice_status_key in protected_statuses:
        flash('Invoice preparation is already recorded for this job docket.', 'info')
    else:
        job_docket.invoice_status = "Invoice Prepared"
        if (job_docket.payment_status or "").strip().lower() in {"", "not invoiced"}:
            job_docket.payment_status = "Not Paid"

        if job_docket.work_order:
            record_work_order_lifecycle_event(
                work_order=job_docket.work_order,
                event_type="contractor_invoice_prepared",
                title="Contractor payment request sent",
                source_module="Contractor Logix",
                actor_user_id=user.id,
                actor_label="Contractor",
                note="Contractor sent the completed job docket as a payment request for management and future Finance Logix review.",
                status_snapshot=job_docket.work_order.status,
                visibility_scope="Admin,PM,Contractor,Finance,GAR",
                event_metadata={
                    "job_docket_id": job_docket.id,
                    "job_docket_number": job_docket.docket_number,
                    "invoice_status": job_docket.invoice_status,
                    "payment_status": job_docket.payment_status,
                    "quotation_reference": job_docket.quotation_reference,
                },
            )

        db.session.commit()
        flash('Payment request sent for this job docket.', 'success')

    if request.form.get('return_to') == 'queue':
        filter_args = _contractor_filter_args()
        filter_args["queue"] = "to_be_invoiced"
        return redirect(url_for('contractor.work_orders', **filter_args))
    return redirect(url_for('contractor.job_docket_detail', docket_id=job_docket.id))


@contractor_bp.route('/job-dockets/<int:docket_id>/schedule', methods=['POST'], endpoint='schedule_job_docket')
@login_required(role='Contractor')
def schedule_docket(docket_id):
    user = _current_contractor_user()
    if not user:
        flash('Your contractor profile is not linked yet.', 'warning')
        return redirect(url_for('contractor.contractor_dashboard'))

    try:
        scheduled_date = datetime.strptime(request.form.get('scheduled_date') or '', "%Y-%m-%d").date()
    except ValueError:
        flash('Choose a valid scheduled date before adding the job to the calendar.', 'warning')
        if request.form.get('return_to') == 'docket':
            return redirect(url_for('contractor.job_docket_detail', docket_id=docket_id))
        return redirect(url_for('contractor.calendar'))

    def parse_time(field_name):
        value = (request.form.get(field_name) or "").strip()
        if not value:
            return None
        try:
            return datetime.strptime(value, "%H:%M").time()
        except ValueError:
            return None

    estimated_duration = _form_int('estimated_duration_minutes')
    assigned_engineer_id = _form_int('assigned_engineer_id')
    assigned_team_id = _form_int('assigned_team_id')

    if assigned_engineer_id and not User.query.filter_by(
        id=assigned_engineer_id,
        contractor_id=user.contractor_id,
        is_active=True,
    ).first():
        flash('Choose an engineer linked to this contractor account.', 'warning')
        if request.form.get('return_to') == 'docket':
            return redirect(url_for('contractor.job_docket_detail', docket_id=docket_id))
        return redirect(url_for('contractor.calendar'))

    if assigned_team_id and not ContractorTeam.query.filter_by(
        id=assigned_team_id,
        contractor_id=user.contractor_id,
        is_active=True,
    ).first():
        flash('Choose a team linked to this contractor account.', 'warning')
        if request.form.get('return_to') == 'docket':
            return redirect(url_for('contractor.job_docket_detail', docket_id=docket_id))
        return redirect(url_for('contractor.calendar'))

    docket, entry = schedule_job_docket(
        docket_id=docket_id,
        contractor_id=user.contractor_id,
        scheduled_date=scheduled_date,
        start_time=parse_time('start_time'),
        end_time=parse_time('end_time'),
        estimated_duration_minutes=estimated_duration,
        assigned_engineer_id=assigned_engineer_id,
        assigned_team_id=assigned_team_id,
        notes=(request.form.get('notes') or '').strip(),
        scheduled_by_id=user.id,
    )
    if not docket or not entry:
        flash('That job docket is not available for this contractor account.', 'danger')
        if request.form.get('return_to') == 'docket':
            return redirect(url_for('contractor.job_docket_detail', docket_id=docket_id))
        return redirect(url_for('contractor.calendar'))

    if docket.work_order:
        record_work_order_lifecycle_event(
            work_order=docket.work_order,
            event_type="job_docket_scheduled",
            title="Job docket scheduled",
            source_module="Contractor Logix",
            actor_user_id=user.id,
            actor_label="Contractor",
            note=f"{docket.docket_number} scheduled for {entry.scheduled_date:%d %b %Y}.",
            status_snapshot=docket.work_order.status,
            visibility_scope="Admin,PM,Contractor,Member,GAR",
            event_metadata={
                "job_docket_id": docket.id,
                "job_docket_number": docket.docket_number,
                "calendar_entry_id": entry.id,
                "scheduled_date": entry.scheduled_date.isoformat(),
                "assigned_engineer_id": entry.assigned_engineer_id,
                "assigned_team_id": entry.assigned_team_id,
            },
        )
    db.session.commit()
    flash('Job docket scheduled and added to Contractor Calendar.', 'success')
    if request.form.get('return_to') == 'docket':
        return redirect(url_for('contractor.job_docket_detail', docket_id=docket.id))
    return redirect(url_for('contractor.calendar'))


@contractor_bp.route('/calendar.ics', endpoint='calendar_ics')
@login_required(role='Contractor')
def calendar_ics():
    user = _current_contractor_user()
    if not user:
        abort(403)

    ics_body = build_contractor_calendar_ics(
        contractor_calendar_entries_for_ics(user.contractor_id)
    )
    return Response(
        ics_body,
        mimetype='text/calendar',
        headers={
            "Content-Disposition": "attachment; filename=contractor-logix-calendar.ics",
        },
    )


def _contractor_settings_defaults(company) -> dict:
    defaults = {
        "calendar_feed_enabled": True,
        "default_update_visibility": "contractor_management",
        "completion_visibility": "all_parties",
        "require_completion_evidence": True,
        "auto_create_docket_on_accept": True,
        "payment_request_after_completion": True,
        "gar_context_enabled": True,
    }
    company_settings = getattr(company, "default_settings", None) or {}
    contractor_settings = company_settings.get("contractor_logix") if isinstance(company_settings, dict) else {}
    if isinstance(contractor_settings, dict):
        defaults.update({key: contractor_settings.get(key, value) for key, value in defaults.items()})
    return defaults


def _current_contractor_context():
    user = _current_contractor_user()
    if not user:
        return None, None, None
    return user, getattr(user, "contractor", None), getattr(user, "company", None)


def _parse_optional_date(value: str):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _contractor_bank_accounts(company):
    if not company:
        return []
    return (
        BankAccount.query.filter_by(owner_type="contractor", owner_id=company.id)
        .order_by(BankAccount.is_default.desc(), BankAccount.active.desc(), BankAccount.id.desc())
        .all()
    )


def _contractor_insurance_policies(company):
    if not company:
        return []
    return (
        InsurancePolicy.query.filter_by(company_id=company.id)
        .order_by(InsurancePolicy.active.desc(), InsurancePolicy.expiry_date.asc(), InsurancePolicy.id.desc())
        .all()
    )


CONTRACTOR_DOCUMENT_MODULE_KEY = "contractor_logix"
CONTRACTOR_DOCUMENT_TYPES = {"job_docket", "quote_response", "payment_request"}


def _normalise_document_key(value: str) -> str:
    return (value or "").strip().lower()


def _contractor_document_catalog(company_id: int | None) -> list[dict]:
    template_order = {
        "job_docket": 10,
        "quote_response": 20,
        "payment_request": 30,
    }
    templates = [
        template
        for template in document_template_catalog(company_id)
        if template.get("module_key") == CONTRACTOR_DOCUMENT_MODULE_KEY
        and template.get("document_type") in CONTRACTOR_DOCUMENT_TYPES
    ]
    return sorted(
        templates,
        key=lambda template: template_order.get(template.get("document_type"), 99),
    )


def _contractor_editable_document_template(
    company,
    document_type: str,
    *,
    persist_new: bool = False,
) -> CoreDocumentTemplate:
    template = CoreDocumentTemplate.query.filter_by(
        company_id=company.id,
        module_key=CONTRACTOR_DOCUMENT_MODULE_KEY,
        document_type=document_type,
        status="Active",
    ).order_by(CoreDocumentTemplate.id.desc()).first()
    if template:
        return template

    default_payload = get_document_template_payload(company.id, CONTRACTOR_DOCUMENT_MODULE_KEY, document_type)
    template = CoreDocumentTemplate(
        company_id=company.id,
        module_key=CONTRACTOR_DOCUMENT_MODULE_KEY,
        document_type=document_type,
        name=default_payload.get("name") or document_type.replace("_", " ").title(),
        description=default_payload.get("description"),
        status="Active",
        version_label=default_payload.get("version_label") or "v1",
        template_format=default_payload.get("template_format") or "html",
        html_body=default_payload.get("html_body"),
        terms_body=default_payload.get("terms_body"),
        footer_body=default_payload.get("footer_body"),
        logo_mode=default_payload.get("logo_mode") or "contractor",
        primary_brand_source=default_payload.get("primary_brand_source") or "contractor",
        include_signature_block=bool(default_payload.get("include_signature_block")),
        include_terms=bool(default_payload.get("include_terms", True)),
        number_prefix=default_payload.get("number_prefix"),
        sequence_padding=default_payload.get("sequence_padding") or 5,
        supported_output_formats=default_payload.get("supported_output_formats") or ["html", "pdf"],
        required_context_keys=default_payload.get("required_context_keys") or [],
        default_context=default_payload.get("default_context") or {},
        visibility_scope=default_payload.get("visibility_scope") or "company",
        created_by_id=session.get("user_id"),
        updated_by_id=session.get("user_id"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    if persist_new:
        db.session.add(template)
    return template


@contractor_bp.route('/settings', methods=['GET', 'POST'])
@login_required(role='Contractor')
def contractor_settings():
    user = _current_contractor_user()
    if not user:
        flash('Contractor Logix is only available to contractor company users.', 'danger')
        return redirect(url_for('auth.login'))

    contractor = getattr(user, "contractor", None)
    company = getattr(user, "company", None)
    settings_payload = _contractor_settings_defaults(company)

    if request.method == "POST":
        if not company:
            flash("A contractor company profile is required before settings can be saved.", "danger")
            return redirect(url_for("contractor.contractor_settings"))

        settings_action = (request.form.get("settings_action") or "save_settings").strip()

        company_settings = dict(company.default_settings or {}) if isinstance(company.default_settings, dict) else {}
        company_settings["contractor_logix"] = {
            "calendar_feed_enabled": request.form.get("calendar_feed_enabled") == "on",
            "default_update_visibility": (
                request.form.get("default_update_visibility") or "contractor_management"
            ).strip(),
            "completion_visibility": (
                request.form.get("completion_visibility") or "all_parties"
            ).strip(),
            "require_completion_evidence": request.form.get("require_completion_evidence") == "on",
            "auto_create_docket_on_accept": request.form.get("auto_create_docket_on_accept") == "on",
            "payment_request_after_completion": request.form.get("payment_request_after_completion") == "on",
            "gar_context_enabled": request.form.get("gar_context_enabled") == "on",
        }
        company.default_settings = company_settings
        company.updated_at = datetime.utcnow()
        db.session.commit()
        flash("Contractor Logix settings updated.", "success")
        return redirect(url_for("contractor.contractor_settings"))

    return render_template(
        'contractor/settings.html',
        contractor=contractor,
        company=company,
        contractor_settings=settings_payload,
        contractor_display_name=(
            getattr(contractor, "company_name", None)
            or getattr(company, "name", None)
            or getattr(user, "full_name", None)
            or "Contractor"
        ),
        contractor_trade=(
            getattr(contractor, "business_type", None)
            or getattr(contractor, "contractor_type", None)
            or "General contractor"
        ),
        module_contract=module_settings_by_key("contractor_logix"),
    )


@contractor_bp.route('/settings/company-profile', methods=['GET', 'POST'], endpoint='contractor_settings_profile')
@login_required(role='Contractor')
def contractor_settings_profile():
    user, contractor, company = _current_contractor_context()
    if not user:
        flash('Contractor Logix is only available to contractor company users.', 'danger')
        return redirect(url_for('auth.login'))
    if not company:
        flash("A contractor company profile is required before profile settings can be managed.", "danger")
        return redirect(url_for("contractor.contractor_settings"))

    if request.method == "POST":
        company.name = (request.form.get("name") or "").strip() or company.name
        company.registration_number = (request.form.get("registration_number") or "").strip() or None
        company.vat_number = (request.form.get("vat_number") or "").strip() or None
        company.email = (request.form.get("email") or "").strip() or None
        company.phone = (request.form.get("phone") or "").strip() or None
        company.website = (request.form.get("website") or "").strip() or None
        company.address_line1 = (request.form.get("address_line1") or "").strip() or None
        company.address_line2 = (request.form.get("address_line2") or "").strip() or None
        company.city = (request.form.get("city") or "").strip() or None
        company.state = (request.form.get("state") or "").strip() or None
        company.postal_code = (request.form.get("postal_code") or "").strip() or None
        company.country = (request.form.get("country") or "").strip() or None
        company.region = (request.form.get("region") or "").strip() or None
        company.currency = (request.form.get("currency") or "").strip() or company.currency or "EUR"
        company.timezone = (request.form.get("timezone") or "").strip() or company.timezone or "Europe/Dublin"
        company.preferred_language = (request.form.get("preferred_language") or "").strip() or company.preferred_language or "en"
        company.brand_primary_color = (request.form.get("brand_primary_color") or "").strip() or None
        company.brand_secondary_color = (request.form.get("brand_secondary_color") or "").strip() or None
        company.brand_color = company.brand_primary_color or company.brand_color
        company.updated_at = datetime.utcnow()
        db.session.commit()
        flash("Contractor company profile updated.", "success")
        return redirect(url_for("contractor.contractor_settings_profile"))

    return render_template(
        "contractor/settings_profile.html",
        company=company,
        contractor=contractor,
        contractor_display_name=(
            getattr(contractor, "company_name", None)
            or getattr(company, "name", None)
            or getattr(user, "full_name", None)
            or "Contractor"
        ),
    )


@contractor_bp.route('/settings/bank-accounts', methods=['GET', 'POST'], endpoint='contractor_settings_bank_accounts')
@login_required(role='Contractor')
def contractor_settings_bank_accounts():
    user, contractor, company = _current_contractor_context()
    if not user:
        flash('Contractor Logix is only available to contractor company users.', 'danger')
        return redirect(url_for('auth.login'))
    if not company:
        flash("A contractor company profile is required before bank accounts can be managed.", "danger")
        return redirect(url_for("contractor.contractor_settings"))

    if request.method == "POST":
        if request.form.get("is_default") == "on":
            BankAccount.query.filter_by(owner_type="contractor", owner_id=company.id).update({"is_default": False})

        bank_account = BankAccount(
            owner_type="contractor",
            owner_id=company.id,
            company_id=company.id,
            nickname=(request.form.get("nickname") or "").strip() or None,
            account_name=(request.form.get("account_name") or "").strip() or None,
            bank_name=(request.form.get("bank_name") or "").strip() or None,
            iban=(request.form.get("iban") or "").strip().upper() or None,
            bic_swift=(request.form.get("bic_swift") or "").strip().upper() or None,
            remittance_email=(request.form.get("remittance_email") or "").strip() or None,
            currency=(request.form.get("currency") or "").strip() or "EUR",
            account_type=(request.form.get("account_type") or "").strip() or "Operating",
            active=request.form.get("active") == "on",
            is_default=request.form.get("is_default") == "on",
        )
        db.session.add(bank_account)
        db.session.commit()
        flash("Contractor bank account added.", "success")
        return redirect(url_for("contractor.contractor_settings_bank_accounts"))

    return render_template(
        "contractor/settings_bank_accounts.html",
        company=company,
        contractor=contractor,
        bank_accounts=_contractor_bank_accounts(company),
    )


@contractor_bp.post(
    '/settings/bank-accounts/<int:account_id>/default',
    endpoint='contractor_settings_bank_account_default',
)
@login_required(role='Contractor')
def contractor_settings_bank_account_default(account_id):
    user, contractor, company = _current_contractor_context()
    if not user:
        flash('Contractor Logix is only available to contractor company users.', 'danger')
        return redirect(url_for('auth.login'))
    if not company:
        flash("A contractor company profile is required before bank accounts can be managed.", "danger")
        return redirect(url_for("contractor.contractor_settings"))

    account = BankAccount.query.filter_by(
        id=account_id,
        owner_type="contractor",
        owner_id=company.id,
    ).first_or_404()
    BankAccount.query.filter_by(owner_type="contractor", owner_id=company.id).update({"is_default": False})
    account.is_default = True
    account.active = True
    account.updated_at = datetime.utcnow()
    db.session.commit()
    flash("Default contractor bank account updated.", "success")
    return redirect(url_for("contractor.contractor_settings_bank_accounts"))


@contractor_bp.post(
    '/settings/bank-accounts/<int:account_id>/toggle',
    endpoint='contractor_settings_bank_account_toggle',
)
@login_required(role='Contractor')
def contractor_settings_bank_account_toggle(account_id):
    user, contractor, company = _current_contractor_context()
    if not user:
        flash('Contractor Logix is only available to contractor company users.', 'danger')
        return redirect(url_for('auth.login'))
    if not company:
        flash("A contractor company profile is required before bank accounts can be managed.", "danger")
        return redirect(url_for("contractor.contractor_settings"))

    account = BankAccount.query.filter_by(
        id=account_id,
        owner_type="contractor",
        owner_id=company.id,
    ).first_or_404()
    account.active = not account.active
    if not account.active:
        account.is_default = False
    account.updated_at = datetime.utcnow()
    db.session.commit()
    flash("Contractor bank account status updated.", "success")
    return redirect(url_for("contractor.contractor_settings_bank_accounts"))


@contractor_bp.route('/settings/insurance', methods=['GET', 'POST'], endpoint='contractor_settings_insurance')
@login_required(role='Contractor')
def contractor_settings_insurance():
    user, contractor, company = _current_contractor_context()
    if not user:
        flash('Contractor Logix is only available to contractor company users.', 'danger')
        return redirect(url_for('auth.login'))
    if not company:
        flash("A contractor company profile is required before insurance can be managed.", "danger")
        return redirect(url_for("contractor.contractor_settings"))

    if request.method == "POST":
        policy_type = (request.form.get("policy_type") or "").strip()
        if not policy_type:
            flash("Choose the policy type before saving.", "warning")
            return redirect(url_for("contractor.contractor_settings_insurance"))

        if request.form.get("is_default") == "on":
            InsurancePolicy.query.filter_by(company_id=company.id, policy_type=policy_type).update({"is_default": False})

        coverage_amount = None
        raw_amount = (request.form.get("coverage_amount") or "").strip()
        if raw_amount:
            try:
                coverage_amount = Decimal(raw_amount)
            except (InvalidOperation, ValueError):
                flash("Coverage amount must be a valid number.", "warning")
                return redirect(url_for("contractor.contractor_settings_insurance"))

        policy = InsurancePolicy(
            company_id=company.id,
            policy_type=policy_type,
            provider=(request.form.get("provider") or "").strip() or None,
            policy_number=(request.form.get("policy_number") or "").strip() or None,
            coverage_amount=coverage_amount,
            currency=(request.form.get("currency") or "").strip() or "EUR",
            start_date=_parse_optional_date(request.form.get("start_date") or ""),
            expiry_date=_parse_optional_date(request.form.get("expiry_date") or ""),
            document_path=(request.form.get("document_path") or "").strip() or None,
            active=request.form.get("active") == "on",
            is_default=request.form.get("is_default") == "on",
        )
        db.session.add(policy)
        db.session.commit()
        flash("Contractor insurance policy added.", "success")
        return redirect(url_for("contractor.contractor_settings_insurance"))

    return render_template(
        "contractor/settings_insurance.html",
        company=company,
        contractor=contractor,
        policies=_contractor_insurance_policies(company),
    )


@contractor_bp.post(
    '/settings/insurance/<int:policy_id>/default',
    endpoint='contractor_settings_insurance_default',
)
@login_required(role='Contractor')
def contractor_settings_insurance_default(policy_id):
    user, contractor, company = _current_contractor_context()
    if not user:
        flash('Contractor Logix is only available to contractor company users.', 'danger')
        return redirect(url_for('auth.login'))
    if not company:
        flash("A contractor company profile is required before insurance can be managed.", "danger")
        return redirect(url_for("contractor.contractor_settings"))

    policy = InsurancePolicy.query.filter_by(id=policy_id, company_id=company.id).first_or_404()
    InsurancePolicy.query.filter_by(company_id=company.id, policy_type=policy.policy_type).update({"is_default": False})
    policy.is_default = True
    policy.active = True
    policy.updated_at = datetime.utcnow()
    db.session.commit()
    flash("Default contractor insurance policy updated.", "success")
    return redirect(url_for("contractor.contractor_settings_insurance"))


@contractor_bp.post(
    '/settings/insurance/<int:policy_id>/toggle',
    endpoint='contractor_settings_insurance_toggle',
)
@login_required(role='Contractor')
def contractor_settings_insurance_toggle(policy_id):
    user, contractor, company = _current_contractor_context()
    if not user:
        flash('Contractor Logix is only available to contractor company users.', 'danger')
        return redirect(url_for('auth.login'))
    if not company:
        flash("A contractor company profile is required before insurance can be managed.", "danger")
        return redirect(url_for("contractor.contractor_settings"))

    policy = InsurancePolicy.query.filter_by(id=policy_id, company_id=company.id).first_or_404()
    policy.active = not policy.active
    if not policy.active:
        policy.is_default = False
    policy.updated_at = datetime.utcnow()
    db.session.commit()
    flash("Contractor insurance policy status updated.", "success")
    return redirect(url_for("contractor.contractor_settings_insurance"))


@contractor_bp.route(
    '/settings/document-templates',
    methods=['GET'],
    endpoint='contractor_document_templates',
)
@login_required(role='Contractor')
def contractor_document_templates():
    user = _current_contractor_user()
    if not user:
        flash('Contractor Logix is only available to contractor company users.', 'danger')
        return redirect(url_for('auth.login'))

    company = getattr(user, "company", None)
    if not company:
        flash("A contractor company profile is required before managing document templates.", "danger")
        return redirect(url_for("contractor.contractor_settings"))

    templates = _contractor_document_catalog(company.id)
    return render_template(
        "contractor/document_templates.html",
        company=company,
        templates=templates,
        contractor_display_name=(
            getattr(getattr(user, "contractor", None), "company_name", None)
            or getattr(company, "name", None)
            or getattr(user, "full_name", None)
            or "Contractor"
        ),
    )


@contractor_bp.route(
    '/settings/document-templates/<document_type>/edit',
    methods=['GET', 'POST'],
    endpoint='contractor_document_template_edit',
)
@login_required(role='Contractor')
def contractor_document_template_edit(document_type: str):
    user = _current_contractor_user()
    if not user:
        flash('Contractor Logix is only available to contractor company users.', 'danger')
        return redirect(url_for('auth.login'))

    company = getattr(user, "company", None)
    if not company:
        flash("A contractor company profile is required before document templates can be edited.", "danger")
        return redirect(url_for("contractor.contractor_settings"))

    document_type = _normalise_document_key(document_type)
    if (CONTRACTOR_DOCUMENT_MODULE_KEY, document_type) not in DOCUMENT_TEMPLATE_DEFAULTS:
        flash("That Contractor Logix document template is not registered.", "danger")
        return redirect(url_for("contractor.contractor_document_templates"))
    if document_type not in CONTRACTOR_DOCUMENT_TYPES:
        flash("That document template belongs to another module.", "danger")
        return redirect(url_for("contractor.contractor_document_templates"))

    template = _contractor_editable_document_template(company, document_type, persist_new=request.method == "POST")
    if request.method == "POST":
        try:
            template.name = (request.form.get("name") or "").strip() or template.name
            template.description = (request.form.get("description") or "").strip() or None
            template.logo_mode = (request.form.get("logo_mode") or "contractor").strip()
            template.primary_brand_source = (request.form.get("primary_brand_source") or "contractor").strip()
            template.number_prefix = (request.form.get("number_prefix") or "").strip().upper() or None
            template.terms_body = (request.form.get("terms_body") or "").strip() or None
            template.footer_body = (request.form.get("footer_body") or "").strip() or None
            template.html_body = (request.form.get("html_body") or "").strip() or None
            template.include_terms = request.form.get("include_terms") == "on"
            template.include_signature_block = request.form.get("include_signature_block") == "on"
            template.updated_by_id = session.get("user_id")
            template.updated_at = datetime.utcnow()
            db.session.commit()
            flash("Contractor document template updated.", "success")
            return redirect(url_for("contractor.contractor_document_templates"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("We could not save that document template. Please try again.", "danger")

    payload = get_document_template_payload(company.id, CONTRACTOR_DOCUMENT_MODULE_KEY, document_type)
    return render_template(
        "contractor/document_template_form.html",
        company=company,
        template=template,
        payload=payload,
    )


@contractor_bp.route(
    '/settings/document-templates/<document_type>/preview',
    methods=['GET'],
    endpoint='contractor_document_template_preview',
)
@login_required(role='Contractor')
def contractor_document_template_preview(document_type: str):
    user = _current_contractor_user()
    if not user:
        flash('Contractor Logix is only available to contractor company users.', 'danger')
        return redirect(url_for('auth.login'))

    company = getattr(user, "company", None)
    if not company:
        flash("A contractor company profile is required before document templates can be previewed.", "danger")
        return redirect(url_for("contractor.contractor_settings"))

    document_type = _normalise_document_key(document_type)
    if document_type not in CONTRACTOR_DOCUMENT_TYPES:
        flash("That document template belongs to another module.", "danger")
        return redirect(url_for("contractor.contractor_document_templates"))

    payload = document_template_preview_payload(company, CONTRACTOR_DOCUMENT_MODULE_KEY, document_type)
    return render_template(
        "contractor/document_template_preview.html",
        company=company,
        payload=payload,
    )


@contractor_bp.route('/settings/connections', methods=['GET', 'POST'], endpoint='contractor_settings_connections')
@login_required(role='Contractor')
def contractor_settings_connections():
    user = _current_contractor_user()
    if not user:
        flash('Contractor Logix is only available to contractor company users.', 'danger')
        return redirect(url_for('auth.login'))

    contractor = getattr(user, "contractor", None)
    company = getattr(user, "company", None)
    if not company:
        flash("A contractor company profile is required before managing connections.", "danger")
        return redirect(url_for("contractor.contractor_settings"))

    if request.method == "POST":
        settings_action = (request.form.get("settings_action") or "").strip()

        if settings_action == "create_connection_invite":
            try:
                invite = create_organisation_connection_invite(
                    source_company_id=company.id,
                    target_email=(request.form.get("target_email") or "").strip() or None,
                    connection_type="management_contractor",
                    allowed_modules=["works", "contractor", "gar_ai"],
                    created_by_user_id=getattr(user, "id", None),
                    notes="Created from Contractor Logix connection settings.",
                )
                db.session.commit()
                flash(f"Connection code created: {invite.invite_code}", "success")
            except ValueError as exc:
                db.session.rollback()
                flash(str(exc), "danger")
            return redirect(url_for("contractor.contractor_settings_connections"))

        if settings_action == "accept_connection_invite":
            invite_code = (request.form.get("invite_code") or "").strip().upper()
            if not invite_code:
                flash("Enter the connection code before connecting organisations.", "warning")
                return redirect(url_for("contractor.contractor_settings_connections"))
            try:
                accept_organisation_connection_invite(
                    invite_code=invite_code,
                    accepting_company_id=company.id,
                    accepted_by_user_id=getattr(user, "id", None),
                )
                db.session.commit()
                flash("Organisation connection accepted.", "success")
            except ValueError as exc:
                db.session.rollback()
                flash(str(exc), "danger")
            return redirect(url_for("contractor.contractor_settings_connections"))

        flash("Choose a connection action before saving.", "warning")
        return redirect(url_for("contractor.contractor_settings_connections"))

    return render_template(
        'contractor/settings_connections.html',
        contractor=contractor,
        company=company,
        contractor_display_name=(
            getattr(contractor, "company_name", None)
            or getattr(company, "name", None)
            or getattr(user, "full_name", None)
            or "Contractor"
        ),
        connection_context=module_connection_context(company, module_key="contractor_logix"),
    )


@contractor_bp.route('/inspections')
@login_required(role='Contractor')
def contractor_inspections():
    flash('Contractor inspections will open here as Contractor Logix is expanded.', 'info')
    return redirect(url_for('contractor.contractor_dashboard'))


@contractor_bp.route('/ppm-calendar')
@login_required(role='Contractor')
def contractor_ppm_calendar():
    return redirect(url_for('contractor.calendar'))


@contractor_bp.route('/upload-compliance-document', methods=['GET', 'POST'], endpoint='upload_compliance_document')

@login_required(role='Contractor')
def contractor_upload_compliance_document():
    if request.method == 'POST':
        document_type = request.form['document_type']
        expiry_date = request.form['expiry_date']
        file = request.files['document']

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', filename)
            file.save(os.path.join(current_app.root_path, 'static', file_path))

            doc = ContractorComplianceDocument(
                contractor_id=session.get('user')['id'],
                document_type=document_type,
                expiry_date=expiry_date,
                file_name=filename,
                file_path=file_path,
                is_required_for_work_order=False,  # Defaulted for contractor
                uploaded_by_id=session.get('user')['id']
            )
            db.session.add(doc)
            db.session.commit()

            flash('Document uploaded successfully!', 'success')
            return redirect(url_for('contractor.contractor_dashboard'))

    return render_template('contractor/upload_compliance_document.html')
