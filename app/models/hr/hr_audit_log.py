from datetime import datetime
from app.extensions import db

class HRAuditLog(db.Model):
    __tablename__ = 'hr_audit_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🧑‍💼 Who made the change
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    actor = db.relationship('User', foreign_keys=[actor_id], backref='hr_actions_performed')

    # 👤 Who the change affects
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    target_user = db.relationship('User', foreign_keys=[target_user_id], backref='hr_audit_entries')

    # 🗂️ Context of Change
    module = db.Column(db.String(100), nullable=False)             # e.g., 'Salary', 'Leave', 'HRProfile'
    record_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)              # Create, Update, Delete, Approve

    field_changed = db.Column(db.String(100), nullable=True)
    previous_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)

    # 📝 Optional Audit Detail
    notes = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(50), default='Manual')            # Manual, Automated, API

    # 🧠 AI / GAR Metadata
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_flags = db.Column(db.Text, nullable=True)                   # e.g., "Below market salary"
    gar_risk_score = db.Column(db.Float, nullable=True)            # 0.0–1.0
    gar_feedback = db.Column(db.Text, nullable=True)               # GAR summary

    # 📅 Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)

    # 🔐 Visibility / Audit Controls
    visibility_scope = db.Column(db.String(100), default="Admin,HR")  # Comma-separated roles
    is_private = db.Column(db.Boolean, default=False)                 # Manual override

    def __repr__(self):
        return f"<HRAuditLog module='{self.module}' action='{self.action}' actor={self.actor_id} timestamp={self.timestamp}>"
