# app/models/occupancy_log.py

from datetime import datetime
from app.extensions import db

class OccupancyLog(db.Model):
    __tablename__ = 'occupancy_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Unit relationship
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    unit = db.relationship('Unit', backref='occupancy_history')

    # 🔗 User relationship (resident, tenant, or owner at that time)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='occupancy_logs')

    # 🕒 Timeframe of occupancy
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # Null = currently active

    # 🏷️ Role during occupancy
    role = db.Column(db.String(50), nullable=False)  # 'owner', 'tenant', 'resident'

    # 📋 Context
    change_reason = db.Column(db.String(255), nullable=True)  # e.g., 'Lease Ended', 'Sold Unit'
    notes = db.Column(db.Text, nullable=True)

    # 🔐 Role-based Access
    visibility_scope = db.Column(db.String(100), default='Admin,PM,Director')
    is_private = db.Column(db.Boolean, default=False)

    # 🤖 AI + GAR Chat Ready
    parsed_context = db.Column(db.Text, nullable=True)                      # AI-generated natural language summary
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Governance Layer
    gar_flags = db.Column(db.Text, nullable=True)                           # e.g., "overlapping lease", "tenant mismatch"
    gar_alignment_score = db.Column(db.Float, nullable=True)               # 0.0 – 1.0
    gar_risk_level = db.Column(db.String(20), nullable=True)               # Low, Medium, High
    gar_recommendation = db.Column(db.Text, nullable=True)                 # "Review termination date"
    requires_governance_review = db.Column(db.Boolean, default=False)

    # 🕓 Audit Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<OccupancyLog Unit={self.unit_id} User={self.user_id} Role={self.role}>"

