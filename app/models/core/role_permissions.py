from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

class RolePermission(db.Model):
    __tablename__ = 'role_permissions'

    id = db.Column(db.Integer, primary_key=True)

    # 🔐 Role this permission set belongs to
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)

    # 🛠️ Context / Feature Group
    context = db.Column(db.String(100), nullable=False)
    # Examples: 'WorkOrders', 'Finance', 'HR', 'Users', 'Reports', 'GAR', 'Inspection', 'Invoices'

    # ✅ Permission Flags (standardized CRUD + control flags)
    can_create = db.Column(db.Boolean, default=False)
    can_view = db.Column(db.Boolean, default=False)
    can_edit = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    can_approve = db.Column(db.Boolean, default=False)  # For approval flows (CAPEX, invoices, users)
    can_submit = db.Column(db.Boolean, default=False)   # For forms, quotes, reports, etc.
    gar_enabled = db.Column(db.Boolean, default=False)  # Access to GAR tools in this module

    # 🔄 Optional Dynamic Rules / Limits
    rules = db.Column(JSONB, nullable=True)
    # Example: {"limit_per_day": 10, "requires_2fa": true, "restricted_hours": "08:00-18:00"}

    # 🧠 AI / GAR Impact Fields
    gar_flagged = db.Column(db.Boolean, default=False)
    gar_risk_score = db.Column(db.Float, nullable=True)
    gar_conflict_reason = db.Column(db.Text, nullable=True)
    gar_flagged_at = db.Column(db.DateTime, nullable=True)
    gar_resolution = db.Column(db.Text, nullable=True)
    gar_resolved_at = db.Column(db.DateTime, nullable=True)
    gar_suggestion = db.Column(db.Text, nullable=True)  # e.g., “Restrict edit access to Finance after hours”

    # 📅 Metadata
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    created_by = db.relationship('User', foreign_keys=[created_by_id])
    updated_by = db.relationship('User', foreign_keys=[updated_by_id])

    def __repr__(self):
        return f"<RolePermission {self.context} (Role ID {self.role_id})>"

