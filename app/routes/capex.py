# routes/capex.py
from flask import Blueprint, request, session, redirect, url_for, flash
from datetime import datetime
from app.models import CapexRequest, CapexApproval, User, DirectorAreaAssignment, db
from app.helpers.notification_helpers import notify_users

capex_bp = Blueprint('capex', __name__)

@capex_bp.route('/capex-decision/<int:capex_id>/<action>', methods=['POST'])
def capex_decision(capex_id, action):
    if 'user' not in session:
        flash("Login required.", "danger")
        return redirect(url_for('login'))

    user_email = session['user']['email']
    user_role = session['user']['role']

    capex = CapexRequest.query.get_or_404(capex_id)

    if action not in ['approve', 'decline', 'hold']:
        flash("Invalid action.", "danger")
        return redirect(url_for('view_responses', capex_id=capex_id))

    approval = CapexApproval(
        capex_id=capex.id,
        approved_by=user_email,
        decision=action,
        decision_date=datetime.utcnow()
    )
    db.session.add(approval)
    db.session.commit()

    notify_users(
        message=f"CAPEX '{capex.area}' was {action}d.",
        capex_id=capex.id,
        roles_to_notify=["Director", "Property Manager"],
        additional_emails=[capex.submitted_by]
    )

    flash(f"CAPEX {action}d successfully.", "success")
    return redirect(url_for('view_responses', capex_id=capex_id))
