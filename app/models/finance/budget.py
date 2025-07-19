from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB


class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)

    # 📆 Budget Scope
    fiscal_year = db.Column(db.String(9), nullable=False)  # Example: '2025/2026'
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)

    # 🔗 Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)  # Optional per-unit budgeting
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 🧾 Budget Details
    category = db.Column(db.String(150), nullable=False)  # e.g. 'Landscaping', 'Cleaning', 'Insurance'
    department = db.Column(db.String(100), nullable=True)  # Optional: link to a department/area
    budgeted_amount = db.Column(db.Numeric(12, 2), nullable=False)
    actual_amount = db.Column(db.Numeric(12, 2), default=0.00)
    variance = db.Column(db.Numeric(12, 2), default=0.00)
    notes = db.Column(db.Text, nullable=True)

    # 🤖 AI & GAR Enhancements
    ai_flagged = db.Column(db.Boolean, default=False)
    ai_summary = db.Column(db.Text, nullable=True)
    gar_score = db.Column(db.Float, nullable=True)
    ai_recommendation = db.Column(db.Text, nullable=True)
    gar_alerts = db.Column(JSONB, default={})
    ai_insights = db.Column(JSONB, default={})  # Historical context, trends, smart suggestions
    ai_scorecard = db.Column(JSONB, nullable=True)  # Optional scoring object for budgeting decisions
    flagged_by_gar = db.Column(db.Boolean, default=False)
    gar_context_reference = db.Column(db.String(255), nullable=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🌐 3rd-Party / System Integration
    external_reference = db.Column(db.String(100), nullable=True)  # Mapping to accounting/ERP system
    sync_status = db.Column(db.String(50), default='Not Synced')
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🛡️ Access & Metadata
    visibility_roles = db.Column(db.ARRAY(db.String(50)), nullable=True)  # e.g. ['Admin', 'PM']
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔁 ORM Relationships
    client = db.relationship('Client', backref='budgets')
    unit = db.relationship('Unit', backref='budgets')
    created_by = db.relationship('User', backref='created_budgets', foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<Budget {self.fiscal_year} - {self.category} - Budgeted: {self.budgeted_amount}>"

