# app/models/role.py

from app.extensions import db
from datetime import datetime

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # e.g., SuperAdmin, Admin, Contractor, PM, Staff, Director

    # 🔁 Core Relationships
    users = db.relationship(
        'User',
        foreign_keys='User.role_id',  # ✅ Explicit to prevent ambiguity
        back_populates='role',
        lazy=True
    )
    permissions = db.relationship(
        'RolePermission',
        backref='role',
        lazy=True,
        cascade='all, delete-orphan'
    )

    # 📋 Description & Metadata
    description = db.Column(db.String(255), nullable=True)
    permissions_matrix = db.Column(db.JSON, nullable=True)
    default_dashboard = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_assignable = db.Column(db.Boolean, default=True)

    # 🧠 AI / GAR Intelligence Layer
    ai_restriction_level = db.Column(db.String(50), nullable=True)
    gar_notes = db.Column(db.Text, nullable=True)
    gar_ai_score = db.Column(db.Float, nullable=True)
    gar_privilege_conflicts = db.Column(db.Text, nullable=True)
    gar_risk_flag = db.Column(db.Boolean, default=False)

    # ✅ AI Suggestions & Governance Feedback
    gar_ai_suggestion = db.Column(db.Text, nullable=True)
    gar_ai_resolution = db.Column(db.Text, nullable=True)
    gar_feedback_status = db.Column(db.String(50), default='Pending')
    gar_flagged_at = db.Column(db.DateTime, nullable=True)
    gar_resolved_at = db.Column(db.DateTime, nullable=True)

    # 📅 Timestamps & Change Log
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 👤 Admin Change Tracking (also needs foreign_keys to avoid ambiguity)
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    updated_by = db.relationship('User', foreign_keys=[updated_by_id])

    def __repr__(self):
        return f"<Role {self.name}>"

