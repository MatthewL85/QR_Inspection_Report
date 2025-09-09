from app.extensions import db
from datetime import datetime

class PasswordChangeLog(db.Model):
    __tablename__ = 'password_change_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Link to User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', backref=db.backref('password_logs', lazy='dynamic'))

    # 📅 When the change occurred
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 🌍 Metadata for audit
    ip_address = db.Column(db.String(45), nullable=True)           # Supports IPv6
    user_agent = db.Column(db.String(255), nullable=True)

    # 🔐 Source of change
    change_type = db.Column(db.String(20), default='manual')       # Options: 'manual', 'reset'

    # 📝 Optional: Notes or reason (e.g. admin force-reset)
    notes = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<PasswordChangeLog user_id={self.user_id} type={self.change_type} time={self.timestamp}>"
