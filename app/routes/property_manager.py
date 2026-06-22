from flask import Blueprint, render_template, session, request
from flask import request, redirect, url_for, flash
from datetime import datetime
from app.extensions import db
from app.models import CapexRequest, Client, ManualTask, Inspection, Equipment
from app.helpers.decorators import login_required
from flask import jsonify
from sqlalchemy import extract
from app.services.works.workflow_service import (
    WorksFilters,
    assign_contractor_to_work_order,
    build_command_centre,
    convert_member_request_to_work_order,
    works_command_centre_payload,
)
from app.services.gar import attach_gar_capability_readiness, build_gar_inquiry_response, build_operational_digest

property_manager_bp = Blueprint('property_manager', __name__)


def _session_user_full_name() -> str:
    session_user = session.get('user') or {}
    return session_user.get('full_name') or session_user.get('name') or 'Property Manager'


@property_manager_bp.route('/dashboard')
@login_required(role='Property Manager')
def pm_dashboard():
    full_name = _session_user_full_name()
    company_id = session.get('company_id') or (session.get('user') or {}).get('company_id')
    gar_question = (request.args.get("gar_question") or "").strip()

    # ✅ Get all clients assigned to this manager
    assigned_clients = Client.query.filter_by(assigned_pm_id=session.get('user_id')).all()
    client_ids = [c.id for c in assigned_clients]
    client_names = [c.name for c in assigned_clients]

    # ✅ CAPEX: Filter by client name (stored as string in CapexRequest)
    capex_count = CapexRequest.query.filter(CapexRequest.client_id.in_(client_ids)).count()

    # ✅ Equipment linked by client_id
    equipment = Equipment.query.filter(Equipment.client_id.in_(client_ids)).all()
    equipment_ids = [e.id for e in equipment]

    # ✅ Inspections linked to the equipment
    inspection_count = Inspection.query.filter(Inspection.equipment_id.in_(equipment_ids)).count()

    # ✅ Manual tasks (e.g. missed/scheduled tasks logged by PM)
    missed_tasks = ManualTask.query.filter(
        ManualTask.client_id.in_(client_ids),
        ManualTask.status == 'Missed'
    ).all()
    works_context = (
        build_command_centre(
            company_id=company_id,
            filters=WorksFilters(allowed_client_ids=tuple(client_ids)),
        )
        if company_id else {"stats": {}, "operational_queues": {}}
    )
    works_gar_contractor_quality = (
        works_context.get("gar_works_intelligence", {})
        .get("pattern_memory", {})
        .get("patterns", {})
        .get("contractor_quality", [])
    )
    gar_inquiry_response = None
    if gar_question:
        gar_inquiry_response = build_gar_inquiry_response(
            gar_question,
            role_context="property_manager",
            company_id=company_id,
            user_id=session.get('user_id'),
            allowed_client_ids=tuple(client_ids),
            execute_source_query=True,
        )

    return render_template('property_manager/property_manager_dashboard.html',
        capex_count=capex_count,
        full_name=full_name,
        company_id=company_id,
        inspection_count=inspection_count,
        client_count=len(assigned_clients),
        equipment=equipment,
        missed_tasks=missed_tasks,
        missed_tasks_count=len(missed_tasks),
        works_stats=works_context.get("stats", {}),
        works_operational_queues=works_context.get("operational_queues", {}),
        works_next_actions=works_context.get("next_actions", []),
        works_gar_contractor_quality=works_gar_contractor_quality,
        gar_question=gar_question,
        gar_inquiry_response=gar_inquiry_response,
    )


def _pm_client_ids():
    return tuple(
        client.id
        for client in Client.query.filter_by(assigned_pm_id=session.get('user_id')).all()
    )


def _works_filter_args():
    return {
        key: value
        for key in ("search", "client_id", "status")
        if (value := (request.form.get(key) or request.args.get(key) or "").strip())
    }


@property_manager_bp.route('/work-orders', methods=['GET'])
@login_required(role='Property Manager')
def work_orders():
    company_id = session.get('company_id')
    if not company_id:
        flash("Company context is missing. Please log in again.", "danger")
        return redirect(url_for('auth.login'))

    filters = WorksFilters(
        search=request.args.get("search", "").strip(),
        client_id=request.args.get("client_id", type=int),
        status=request.args.get("status", "").strip(),
        allowed_client_ids=_pm_client_ids(),
    )
    data = build_command_centre(company_id=company_id, filters=filters, include_gar_history=True)
    return render_template(
        'property_manager/work_orders.html',
        filters=filters,
        **data,
    )


@property_manager_bp.route('/work-orders/feed.json', methods=['GET'])
@login_required(role='Property Manager')
def work_orders_feed():
    company_id = session.get('company_id')
    if not company_id:
        return jsonify({"error": "company_context_missing"}), 403

    filters = WorksFilters(
        search=request.args.get("search", "").strip(),
        client_id=request.args.get("client_id", type=int),
        status=request.args.get("status", "").strip(),
        allowed_client_ids=_pm_client_ids(),
    )
    data = build_command_centre(company_id=company_id, filters=filters, include_gar_history=True)
    return jsonify(works_command_centre_payload(data, filters, role_context="property_manager"))


@property_manager_bp.route('/work-orders/repeated-returns', methods=['GET'])
@login_required(role='Property Manager')
def work_orders_repeated_returns():
    company_id = session.get('company_id')
    if not company_id:
        flash("Company context is missing. Please log in again.", "danger")
        return redirect(url_for('auth.login'))

    filters = WorksFilters(
        search=request.args.get("search", "").strip(),
        client_id=request.args.get("client_id", type=int),
        status=request.args.get("status", "").strip(),
        allowed_client_ids=_pm_client_ids(),
    )
    data = build_command_centre(company_id=company_id, filters=filters, include_gar_history=True)
    return render_template(
        "works/repeated_returns.html",
        layout_template="base.html",
        dashboard_endpoint="property_manager.pm_dashboard",
        dashboard_label="Dashboard",
        command_centre_endpoint="property_manager.work_orders",
        workspace_title="Repeated Returns",
        workspace_subtitle="Management review for contractor completions returned more than once.",
        filters=filters,
        **data,
    )


@property_manager_bp.route('/gar/feed.json', methods=['GET'])
@login_required(role='Property Manager')
def gar_feed():
    company_id = session.get('company_id')
    if not company_id:
        return jsonify({"error": "company_context_missing"}), 403

    payload = build_operational_digest(
        company_id=company_id,
        role_context="property_manager",
        allowed_client_ids=_pm_client_ids(),
    )
    return jsonify(attach_gar_capability_readiness(
        payload,
        role_context="property_manager",
        question=(request.args.get("question") or "").strip() or None,
    ))


@property_manager_bp.route('/gar/inquiry.json', methods=['GET'])
@login_required(role='Property Manager')
def gar_inquiry():
    company_id = session.get('company_id')
    if not company_id:
        return jsonify({"error": "company_context_missing"}), 403

    return jsonify(build_gar_inquiry_response(
        (request.args.get("question") or request.args.get("gar_question") or "").strip(),
        role_context="property_manager",
        company_id=company_id,
        user_id=session.get('user_id'),
        allowed_client_ids=_pm_client_ids(),
        execute_source_query=True,
    ))


@property_manager_bp.route('/work-orders/member-requests/<int:request_id>/convert', methods=['POST'])
@login_required(role='Property Manager')
def convert_member_request(request_id):
    company_id = session.get('company_id')
    if not company_id:
        flash("Company context is missing. Please log in again.", "danger")
        return redirect(url_for('auth.login'))

    work_order = convert_member_request_to_work_order(
        request_id=request_id,
        company_id=company_id,
        created_by_id=session.get('user_id'),
        allowed_client_ids=_pm_client_ids(),
        access_context="assigned_property_manager",
    )
    if not work_order:
        flash("That request could not be converted for your assigned developments.", "danger")
        return redirect(url_for('property_manager.work_orders', **_works_filter_args()))

    flash("Member request converted to a Works Logix work order.", "success")
    return redirect(url_for('property_manager.work_orders', **_works_filter_args()))


@property_manager_bp.route('/work-orders/<int:work_order_id>/assign-contractor', methods=['POST'])
@login_required(role='Property Manager')
def assign_work_order_contractor(work_order_id):
    company_id = session.get('company_id')
    contractor_id = request.form.get("contractor_id", type=int)
    if not company_id or not contractor_id:
        flash("Choose a contractor before assigning this work order.", "warning")
        return redirect(url_for('property_manager.work_orders', **_works_filter_args()))

    work_order = assign_contractor_to_work_order(
        work_order_id=work_order_id,
        company_id=company_id,
        contractor_id=contractor_id,
        allowed_client_ids=_pm_client_ids(),
        assigned_by_id=session.get('user_id'),
        access_context="assigned_property_manager",
    )
    if not work_order:
        flash("That work order could not be assigned for your developments.", "danger")
        return redirect(url_for('property_manager.work_orders', **_works_filter_args()))

    flash("Work order assigned to contractor.", "success")
    return redirect(url_for('property_manager.work_orders', **_works_filter_args()))

@property_manager_bp.route('/add-task', methods=['GET', 'POST'])
@login_required(role='Property Manager')
def add_manual_task():
    if request.method == 'POST':
        title = request.form.get('title')
        client = request.form.get('client')
        date = request.form.get('date')
        created_by = _session_user_full_name()

        new_task = ManualTask(
            title=title,
            client=client,
            date=date,
            created_by=created_by,
            status='Scheduled',
            completed='no'
        )
        db.session.add(new_task)
        db.session.commit()
        flash("Manual task created successfully.", "success")
        return redirect(url_for('property_manager.pm_dashboard'))

    # For the dropdown list
    full_name = _session_user_full_name()
    clients = Client.query.filter_by(assigned_pm_id=session.get('user_id')).all()
    return render_template('add_task.html', clients=clients)

@property_manager_bp.route('/complete-task', methods=['POST'])
@login_required(role='Property Manager')
def complete_task():
    task_id = request.form.get('task_id')
    task = ManualTask.query.get(task_id)

    if task:
        task.completed = 'yes'
        task.status = 'Complete'
        db.session.commit()
        flash("Task marked as complete.", "success")
    else:
        flash("Task not found.", "danger")

    return redirect(url_for('property_manager.pm_dashboard'))

@property_manager_bp.route('/edit-task', methods=['GET', 'POST'])
@login_required(role='Property Manager')
def edit_task():
    task_id = request.args.get('task_id')
    task = ManualTask.query.get(task_id)

    if not task:
        flash('Task not found.', 'danger')
        return redirect(url_for('property_manager.pm_dashboard'))

    if request.method == 'POST':
        task.title = request.form['title']
        task.client = request.form['client']
        task.date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        task.status = request.form['status']
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('property_manager.pm_dashboard'))

    full_name = _session_user_full_name()
    clients = Client.query.filter_by(assigned_pm_id=session.get('user_id')).all()
    return render_template('edit_task.html', task=task, clients=clients)


@property_manager_bp.route('/maintenance-calendar')
@login_required(role='Property Manager')
def property_manager_maintenance_planner():
    full_name = _session_user_full_name()
    assigned_clients = Client.query.filter_by(assigned_pm_id=session.get('user_id')).all()
    client_ids = [c.id for c in assigned_clients]
    client_names = [c.name for c in assigned_clients]

    # 🔍 Filters from query params
    status_filter = request.args.get('status')
    client_filter = request.args.get('client')

    # Base task query
    task_query = ManualTask.query.filter(ManualTask.client_id.in_(client_ids))

    if status_filter:
        task_query = task_query.filter_by(status=status_filter)
    if client_filter:
        task_query = task_query.filter_by(client=client_filter)

    tasks = task_query.all()

    # 🎯 Event rendering for FullCalendar
    events = []
    for task in tasks:
        events.append({
            'id': task.id,
            'title': f"{task.task_name} ({task.status})",
            'start': task.due_date.strftime('%Y-%m-%d'),
            'color': (
                '#f44336' if task.status == 'Missed' else
                '#4caf50' if task.status == 'Complete' else
                '#ff9800'
            ),
            'url': url_for('property_manager.edit_task') + f'?task_id={task.id}'
        })

    # 🎯 Summary counts (full month, not filtered)
    now = datetime.now()
    base_filter = [
        ManualTask.client_id.in_(client_ids),
        extract('month', ManualTask.due_date) == now.month,
        extract('year', ManualTask.due_date) == now.year
    ]

    missed_count = ManualTask.query.filter(*base_filter, ManualTask.status == 'Missed').count()
    complete_count = ManualTask.query.filter(*base_filter, ManualTask.status == 'Complete').count()
    scheduled_count = ManualTask.query.filter(*base_filter, ManualTask.status == 'Scheduled').count()

    return render_template('maintenance_calendar.html',
        events=events,
        clients=assigned_clients,  # For dropdowns
        missed_count=missed_count,
        complete_count=complete_count,
        scheduled_count=scheduled_count
    )

@property_manager_bp.route('/update-task-date', methods=['POST'])
@login_required(role='Property Manager')
def update_task_date():
    data = request.get_json()
    task = ManualTask.query.get(data.get('task_id'))
    if task:
        task.date = datetime.strptime(data.get('new_date'), '%Y-%m-%d')
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False)

@property_manager_bp.route('/settings')
@login_required()
def pm_settings():
    return render_template('property_manager/settings.html')
