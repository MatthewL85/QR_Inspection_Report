# app/models/finance/lease_apportionment_schedule.py

from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates

class LeaseApportionmentSchedule(db.Model):
    __tablename__ = 'lease_apportionment_schedules'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Associations
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False, index=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('leases.id'), nullable=True)  # Optional future linkage
    year = db.Column(db.Integer, nullable=False, index=True)

    # ⚖️ Apportionment Method
    method = db.Column(db.String(50), nullable=False, index=True)  # Fixed %, Area, Equal, Custom
    percentage = db.Column(db.Numeric(6, 4), nullable=True)
    area_m2 = db.Column(db.Numeric(10, 2), nullable=True)
    custom_formula = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)

    # 📎 Additional Context
    lease_reference = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # 🤖 AI / GAR Fields
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    gar_notes = db.Column(db.Text, nullable=True)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)

    # 🔌 3rd-Party Integration
    external_reference = db.Column(db.String(100), nullable=True)  # e.g., Lease ID in another system
    external_system = db.Column(db.String(100), nullable=True)     # e.g., MRI, Yardi
    sync_status = db.Column(db.String(50), default='Pending')      # Synced, Failed, Manual
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🔐 Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    modified_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    modified_by = db.relationship('User', foreign_keys=[modified_by_id])

    # Relationships
    client = db.relationship('Client', backref='apportionment_schedules')
    unit = db.relationship('Unit', backref='apportionment_schedules')

    def __repr__(self):
        return f"<LeaseApportionmentSchedule Unit={self.unit_id} Method={self.method} %={self.percentage}>"

