def notify_users(message, capex_id=None, roles_to_notify=None, additional_emails=None):
    # Delayed import to avoid circular import
    from app import db
    from app.models import User, Notification

    recipients = set()

    # Get emails by role
    if roles_to_notify:
        users = User.query.filter(User.role.in_(roles_to_notify)).all()
        recipients.update(user.email for user in users)

    # Add manually specified emails
    if additional_emails:
        recipients.update(additional_emails)

    # Always notify admins silently
    admins = User.query.filter(User.role == 'Admin').all()
    recipients.update(admin.email for admin in admins)

    # Create notification entries
    for email in recipients:
        new_note = Notification(
            recipient_email=email,
            message=message,
            capex_id=capex_id
        )
        db.session.add(new_note)

    db.session.commit()
