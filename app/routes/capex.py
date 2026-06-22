# routes/capex.py
from flask import Blueprint, request, redirect, url_for, flash, render_template, current_app
from datetime import datetime
from flask_login import current_user, login_required
from app.models import CapexRequest, CapexApproval, CapexResponse, db
from app.helpers.notification_helpers import notify_users

capex_bp = Blueprint('capex', __name__)


@capex_bp.route('/capex/<int:capex_id>/responses', methods=['GET'], endpoint='view_responses')
@login_required
def view_responses(capex_id):
    capex_request = CapexRequest.query.get_or_404(capex_id)
    responses = (
        CapexResponse.query
        .filter_by(capex_request_id=capex_request.id, is_archived=False)
        .order_by(CapexResponse.submitted_at.desc())
        .all()
    )
    return render_template(
        'view_responses.html',
        capex_request=capex_request,
        responses=responses,
    )


@capex_bp.route('/capex-decision/<int:capex_id>/<action>', methods=['POST'])
@login_required
def capex_decision(capex_id, action):
    capex = CapexRequest.query.get_or_404(capex_id)

    status_map = {
        'approve': 'Approved',
        'decline': 'Rejected',
        'hold': 'Deferred',
    }
    if action not in status_map:
        flash("Invalid action.", "danger")
        return redirect(url_for('capex.view_responses', capex_id=capex_id))

    approval = CapexApproval(
        capex_request_id=capex.id,
        approved_by=current_user.id,
        status=status_map[action],
        approval_notes=request.form.get('note') or None,
        approved_at=datetime.utcnow(),
    )
    capex.status = status_map[action]
    db.session.add(approval)
    db.session.commit()

    try:
        notify_users(
            message=f"CAPEX '{capex.area}' was {status_map[action].lower()}.",
            capex_id=capex.id,
            roles_to_notify=["Director", "Property Manager"],
            additional_emails=[capex.submitter.email] if capex.submitter else None,
        )
    except Exception as exc:
        current_app.logger.warning("CAPEX notification failed: %s", exc)

    flash(f"CAPEX marked as {status_map[action].lower()}.", "success")
    return redirect(url_for('capex.view_responses', capex_id=capex_id))
