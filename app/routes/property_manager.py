from flask import Blueprint, render_template, session, request
from flask import request, redirect, url_for, flash
from datetime import datetime
from app.extensions import db
from app.models import CapexRequest, Client, ManualTask, Inspection, Equipment
from app.helpers.decorators import login_required
from flask import jsonify
from sqlalchemy import extract

property_manager_bp = Blueprint('property_manager', __name__)

@property_manager_bp.route('/dashboard')
@login_required(role='Property Manager')
def pm_dashboard():
    full_name = session['user']['full_name']

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

    return render_template('property_manager/property_manager_dashboard.html',
        capex_count=capex_count,
        inspection_count=inspection_count,
        client_count=len(assigned_clients),
        equipment=equipment,
        missed_tasks=missed_tasks,
        missed_tasks_count=len(missed_tasks)
    )

@property_manager_bp.route('/add-task', methods=['GET', 'POST'])
@login_required(role='Property Manager')
def add_manual_task():
    if request.method == 'POST':
        title = request.form.get('title')
        client = request.form.get('client')
        date = request.form.get('date')
        created_by = session['user']['full_name']

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
    full_name = session['user']['full_name']
    clients = Client.query.filter_by(assigned_pm_id=session.get('user_id')).all()
    return render_template('add_manual_task.html', clients=clients)

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

    full_name = session['user']['full_name']
    clients = Client.query.filter_by(assigned_pm_id=session.get('user_id')).all()
    return render_template('edit_task.html', task=task, clients=clients)


@property_manager_bp.route('/maintenance-calendar')
@login_required(role='Property Manager')
def property_manager_maintenance_planner():
    full_name = session['user']['full_name']
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
