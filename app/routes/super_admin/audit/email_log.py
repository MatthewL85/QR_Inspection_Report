@super_admin_bp.route('/audit/email-logs', methods=['GET'], endpoint='view_email_logs')
@super_admin_required
def view_email_logs():
    from app.models.core.user import User  # 👈 Needed to resolve names
    from app.models.audit.email_log import EmailLog

    filters = {
        'user_id': request.args.get('user_id', type=int),
        'email_type': request.args.get('email_type', type=str),
        'delivery_status': request.args.get('delivery_status', type=str)
    }

    query = EmailLog.query

    if filters['user_id']:
        query = query.filter_by(user_id=filters['user_id'])
    if filters['email_type']:
        query = query.filter_by(email_type=filters['email_type'])
    if filters['delivery_status']:
        query = query.filter_by(delivery_status=filters['delivery_status'])

    logs = query.order_by(EmailLog.timestamp.desc()).all()
    users = User.query.with_entities(User.id, User.full_name).all()

    return render_template('super_admin/audit/email_logs.html', logs=logs, users=users, filters=filters)
