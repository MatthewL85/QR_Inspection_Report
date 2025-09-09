# app/models/audit.py

from app.extensions import db
from datetime import datetime

class ProfileChangeLog(db.Model):
    __tablename__ = 'profile_change_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Audit Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)      # The user whose profile was changed
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)    # Who made the change (PM, admin, etc.)

    # 🔄 Change Tracking
    field_name = db.Column(db.String(100), nullable=False)        # Field that was changed (e.g., "role", "email")
    old_value = db.Column(db.String(255), nullable=True)
    new_value = db.Column(db.String(255), nullable=True)
    change_reason = db.Column(db.Text, nullable=True)             # Optional justification for the change
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # 🧠 GAR / AI Review Support
    parsed_summary = db.Column(db.Text, nullable=True)            # Human-readable summary (e.g., “Role changed from PM to Admin”)
    gar_flagged_risks = db.Column(db.Text, nullable=True)         # e.g., “Privilege escalation”
    gar_priority_score = db.Column(db.Float, nullable=True)       # GAR risk score or sensitivity (0.0 to 1.0)
    gar_chat_ready = db.Column(db.Boolean, default=False)         # Ready for AI-based discussion or audit
    gar_feedback = db.Column(db.Text, nullable=True)              # Human or AI review notes

    # 🔗 Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='change_logs')
    changed_by_user = db.relationship('User', foreign_keys=[changed_by], backref='changes_made')

    def __repr__(self):
        return f"<ProfileChangeLog user_id={self.user_id} field={self.field_name}>"
