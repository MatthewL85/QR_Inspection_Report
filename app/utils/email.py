# 📍 app/utils/email.py

from flask import url_for, current_app
from flask_mail import Message
from app.extensions import mail, serializer

# ✅ Generic email sender for any purpose
def send_email(subject, recipients, body, html=None, sender=None):
    sender = sender or current_app.config['MAIL_DEFAULT_SENDER']
    msg = Message(subject=subject, sender=sender, recipients=recipients, body=body, html=html)
    mail.send(msg)

# ✅ Reset-password-specific email (uses the generic sender)
def send_reset_email(user):
    token = serializer.dumps(user.email, salt='password-reset')
    reset_url = url_for('auth.reset_password_token', token=token, _external=True)

    subject = "🔐 Reset Your LogixPM Password"
    recipient = user.email
    body = f"""
Hi {user.full_name},

You requested to reset your password for LogixPM. Click the link below to set a new one:

{reset_url}

If you did not request this, please ignore this email or contact support.

This link will expire in 1 hour.

Thanks,  
The LogixPM Team
"""

    send_email(subject=subject, recipients=[recipient], body=body)
