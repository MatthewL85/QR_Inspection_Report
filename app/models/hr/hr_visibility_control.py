from datetime import datetime
from app.extensions import db

class HRVisibilityControl(db.Model):
    __tablename__ = 'hr_visibility_controls'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    viewer_role = db.Column(db.String(100), nullable=False)        # Director, HR, Admin
    viewer_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    module = db.Column(db.String(100), nullable=False)             # e.g., "HRProfile", "Salary", "LeaveRequest"
    field = db.Column(db.String(100), nullable=True)               # Optional: specify field-level visibility
    access_level = db.Column(db.String(50), default="Restricted")  # View, Edit, Restricted
    reason = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id], backref="visibility_settings")
    viewer_user = db.relationship("User", foreign_keys=[viewer_user_id], backref="visibility_permissions")

    def __repr__(self):
        return f"<HRVisibilityControl user={self.user_id} viewable_by={self.viewer_role}>"
