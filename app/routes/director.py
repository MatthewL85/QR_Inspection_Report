from app.helpers.decorators import login_required
from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify

from app.extensions import db
from app.models import User
from app.services.gar import attach_gar_capability_readiness, build_gar_inquiry_response, build_operational_digest

director_bp = Blueprint('director', __name__)

@director_bp.route('/dashboard')
@login_required(role='Director')
def dashboard():
    user = User.query.get(session.get('user_id'))
    if not user and session.get('user', {}).get('email'):
        user = User.query.filter_by(email=session['user']['email']).first()

    gar_question = (request.args.get("gar_question") or "").strip()
    company_id = getattr(user, 'company_id', None)
    gar_inquiry_response = None
    if gar_question:
        gar_inquiry_response = build_gar_inquiry_response(
            gar_question,
            role_context="director_governance",
            company_id=company_id,
            user_id=getattr(user, "id", None),
            execute_source_query=True,
        )

    return render_template(
        'director_dashboard.html',
        user=user,
        company=getattr(user, "company", None),
        capex_requests=[],
        areas=[],
        statuses=[],
        years=[],
        assignments={},
        gar_question=gar_question,
        gar_inquiry_response=gar_inquiry_response,
    )


@director_bp.route('/gar/feed.json', endpoint='gar_feed')
@login_required(role='Director')
def gar_feed():
    user = User.query.get(session.get('user_id'))
    if not user and session.get('user', {}).get('email'):
        user = User.query.filter_by(email=session['user']['email']).first()

    company_id = getattr(user, 'company_id', None)
    if not company_id:
        return jsonify({"error": "company_context_missing"}), 403

    payload = build_operational_digest(
        company_id=company_id,
        role_context="director_governance",
    )
    return jsonify(attach_gar_capability_readiness(
        payload,
        role_context="director_governance",
        question=(request.args.get("question") or "").strip() or None,
    ))


@director_bp.route('/gar/inquiry.json', endpoint='gar_inquiry')
@login_required(role='Director')
def gar_inquiry():
    user = User.query.get(session.get('user_id'))
    if not user and session.get('user', {}).get('email'):
        user = User.query.filter_by(email=session['user']['email']).first()

    company_id = getattr(user, 'company_id', None)
    if not company_id:
        return jsonify({"error": "company_context_missing"}), 403

    return jsonify(build_gar_inquiry_response(
        (request.args.get("question") or request.args.get("gar_question") or "").strip(),
        role_context="director_governance",
        company_id=company_id,
        user_id=getattr(user, "id", None),
        execute_source_query=True,
    ))

@director_bp.route('/settings')
def director_settings():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    user = User.query.filter_by(email=session['user']['email']).first()
    return render_template('director_settings.html', user=user)


@director_bp.route('/capex')
def director_capex_list():
    flash('Director CAPEX tracker will open here as Director Logix is expanded.', 'info')
    return redirect(url_for('director.dashboard'))


@director_bp.route('/inspections')
def director_view_inspections():
    flash('Director inspection reports will open here as Director Logix is expanded.', 'info')
    return redirect(url_for('director.dashboard'))


@director_bp.route('/documents')
def director_documents():
    flash('Director documents will open here as Director Logix is expanded.', 'info')
    return redirect(url_for('director.dashboard'))


@director_bp.route('/messages')
def director_messages():
    flash('Director messages will open here as Director Logix is expanded.', 'info')
    return redirect(url_for('director.dashboard'))


@director_bp.route('/update-profile', methods=['POST'])
def director_update_profile():
    user = User.query.filter_by(email=session['user']['email']).first()
    user.full_name = request.form['full_name'].strip()
    db.session.commit()
    flash("Profile updated successfully!", "success")
    return redirect(url_for('director.director_settings'))

@director_bp.route('/change-password', methods=['POST'])
def director_change_password():
    # logic for password change with hash check
    return redirect(url_for('director.director_settings'))
