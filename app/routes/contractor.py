import os

from flask import Blueprint, render_template, session, request, current_app, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

from app.extensions import db
from app.helpers.decorators import login_required
from app.models import ContractorComplianceDocument
from app.models.core.user import User
from app.services.gar import (
    attach_gar_capability_readiness,
    build_gar_inquiry_response,
    build_contractor_role_digest,
    build_work_order_relevant_history,
)
from app.services.works.workflow_service import (
    ContractorWorkFilters,
    build_work_order_lifecycle_for_audience,
    build_work_order_return_context,
    build_work_order_review_cycle,
    contractor_work_queue_payload,
    contractor_update_work_order,
    get_contractor_work_orders,
)
from app.services.works.audit_pack_service import build_completion_evidence_pack

contractor_bp = Blueprint('contractor', __name__)

@contractor_bp.route('/dashboard')
@login_required(role='Contractor')
def contractor_dashboard():
    user = User.query.get(session.get('user_id'))
    work_data = get_contractor_work_orders(user.contractor_id, user.id) if user and user.contractor_id else None
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
    return render_template('contractor/work_orders.html', filters=filters, **data)


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

    if action not in {'accept', 'start', 'complete'}:
        flash('That work order action is not available.', 'danger')
        return redirect(url_for('contractor.work_orders', **_contractor_filter_args()))

    work_order = contractor_update_work_order(
        work_order_id=work_order_id,
        contractor_id=user.contractor_id,
        user_id=user.id,
        action=action,
        completion_notes=(request.form.get('completion_notes') or '').strip(),
        evidence_reference=(request.form.get('evidence_reference') or '').strip(),
    )
    if not work_order:
        flash('That work order is not assigned to your contractor profile.', 'danger')
        return redirect(url_for('contractor.work_orders', **_contractor_filter_args()))

    messages = {
        'accept': 'Work order accepted.',
        'start': 'Work order marked as in progress.',
        'complete': 'Completion submitted to Works Logix.',
    }
    flash(messages[action], 'success')
    return redirect(url_for('contractor.work_orders', **_contractor_filter_args()))

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
    flash('The contractor PPM calendar will open here as Contractor Logix is expanded.', 'info')
    return redirect(url_for('contractor.contractor_dashboard'))


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
