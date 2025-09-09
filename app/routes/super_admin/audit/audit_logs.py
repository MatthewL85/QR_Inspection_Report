@super_admin_bp.route('/audit/password-changes', methods=['GET'], endpoint='view_password_logs')
@super_admin_required
def view_password_logs():
    logs = PasswordChangeLog.query.order_by(PasswordChangeLog.timestamp.desc()).all()
    return render_template('super_admin/audit/password_logs.html', logs=logs)
