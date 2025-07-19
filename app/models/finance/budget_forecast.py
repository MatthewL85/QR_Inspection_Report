from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB


class BudgetForecast(db.Model):
    __tablename__ = 'budget_forecasts'

    id = db.Column(db.Integer, primary_key=True)

    # 📅 Period Info
    fiscal_year = db.Column(db.String(9), nullable=False)  # e.g., '2025/2026'
    forecast_date = db.Column(db.Date, default=datetime.utcnow)
    forecast_period = db.Column(db.String(50), nullable=True)  # Q1, Q2, Month name, etc.

    # 🔗 Associations
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 📊 Forecast Details
    category = db.Column(db.String(150), nullable=False)
    forecast_amount = db.Column(db.Numeric(12, 2), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    adjustment_reason = db.Column(db.Text, nullable=True)

    # 🤖 AI / GAR Intelligence
    ai_projection = db.Column(db.Numeric(12, 2), nullable=True)
    gar_risk_flag = db.Column(db.Boolean, default=False)
    ai_trend_summary = db.Column(db.Text, nullable=True)
    gar_recommendation = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(255), nullable=True)
    forecast_notes = db.Column(JSONB, default={})  # Smart notes, confidence intervals, models used
    ai_scorecard = db.Column(JSONB, nullable=True)  # Optional structured scoring

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🌐 Integration Metadata
    external_reference = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Not Synced')
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🔐 Auditing & Metadata
    visibility_roles = db.Column(db.ARRAY(db.String(50)), nullable=True)  # Optional scope control
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔁 Relationships
    client = db.relationship('Client', backref='budget_forecasts')
    unit = db.relationship('Unit', backref='budget_forecasts')
    created_by = db.relationship('User', backref='created_budget_forecasts', foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<BudgetForecast {self.fiscal_year} | {self.category} | {self.forecast_amount}>"
