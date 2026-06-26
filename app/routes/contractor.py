import os
from datetime import datetime

from flask import Blueprint, Response, render_template, session, request, current_app, flash, redirect, url_for, jsonify, abort, send_file
from werkzeug.utils import secure_filename

from app.extensions import db
from app.helpers.decorators import login_required
from app.models import ContractorComplianceDocument
from app.models.contractor.contractor_team import ContractorTeam
from app.models.contractor.job_docket import JobDocket
from app.models.core.user import User
from app.services.gar import (
    attach_gar_capability_readiness,
    build_gar_inquiry_response,
    build_contractor_role_digest,
    build_work_order_relevant_history,
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
)
from app.services.contractor.job_docket_service import (
    build_contractor_calendar_ics,
    calendar_context,
    contractor_calendar_entries_for_ics,
    contractor_today_schedule_context,
    schedule_job_docket,
)
from app.services.works.audit_pack_service import build_completion_evidence_pack
from app.models.works.work_order import WorkOrder
from app.services.works.work_order_docket_service import (
    build_contractor_work_order_docket,
    render_contractor_work_order_pdf,
)

contractor_bp = Blueprint('contractor', __name__)

CONTRACTOR_EVIDENCE_UPLOAD_EXTENSIONS = {
    "jpg", "jpeg", "png", "gif", "webp", "heic",
    "mp4", "mov", "webm", "avi", "m4v",
    "pdf", "doc", "docx",
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


@contractor_bp.route('/dashboard')
@login_required(role='Contractor')
def contractor_dashboard():
    user = User.query.get(session.get('user_id'))
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
    if not user or not user.contractor_id:
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
        for key in ("search", "status")
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


@contractor_bp.route('/work-orders')
@login_required(role='Contractor')
def work_orders():
    user = _current_contractor_user()
    if not user:
        flash('Your contractor profile is not linked yet.', 'warning')
        return redirect(url_for('contractor.contractor_dashboard'))

    filters = _contractor_work_filters()
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
    return render_template('contractor/work_orders.html', filters=filters, **data)


def _contractor_work_order_or_404(work_order_id: int) -> tuple[User, WorkOrder]:
    user = _current_contractor_user()
    if not user:
        abort(403)

    work_order = WorkOrder.query.filter(
        WorkOrder.id == work_order_id,
        WorkOrder.contractor_id == user.contractor_id,
    ).first_or_404()
    return user, work_order


@contractor_bp.route('/work-orders/<int:work_order_id>', endpoint='work_order_detail')
@login_required(role='Contractor')
def work_order_detail(work_order_id):
    _user, work_order = _contractor_work_order_or_404(work_order_id)
    docket = build_contractor_work_order_docket(work_order, audience="contractor")
    return render_template(
        'contractor/work_order_detail.html',
        docket=docket,
        progress_updates=progress_updates_for_audience(work_order, "contractor"),
    )


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
        download_name=f"WO-{work_order.id}-contractor-pack.pdf",
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
        filters=filters,
        **calendar_context(user.contractor_id, filters=filters),
    )


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
    work_pack = build_contractor_work_order_docket(work_order, audience="contractor")
    return render_template(
        'contractor/job_docket_detail.html',
        job_docket=job_docket,
        work_order=work_order,
        work_pack=work_pack,
        progress_updates=progress_updates_for_audience(work_order, "contractor"),
    )


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
        return redirect(url_for('contractor.calendar'))

    if assigned_team_id and not ContractorTeam.query.filter_by(
        id=assigned_team_id,
        contractor_id=user.contractor_id,
        is_active=True,
    ).first():
        flash('Choose a team linked to this contractor account.', 'warning')
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
        return redirect(url_for('contractor.calendar'))

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


@contractor_bp.route('/settings')
@login_required()
def contractor_settings():
    return render_template('contractor/settings.html')


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

@login_required()
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
