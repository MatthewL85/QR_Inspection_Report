from flask import url_for, current_app
from flask_mail import Message
from app.extensions import mail, serializer

def send_reset_email(user):
    token = serializer.dumps(user.email, salt='password-reset')
    reset_link = url_for('auth.reset_password_token', token=token, _external=True)

    msg = Message("Password Reset for LogixPM",
                  recipients=[user.email],
                  body=f"Hi {user.full_name},\n\nTo reset your password, click the link below:\n{reset_link}\n\nThis link will expire in 1 hour.\n\nIf you did not request this, please ignore this email.",
                  sender=current_app.config['MAIL_DEFAULT_SENDER'])

    mail.send(msg)
