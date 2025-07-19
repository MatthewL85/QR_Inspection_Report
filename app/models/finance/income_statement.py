from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates

class IncomeStatement(db.Model):
    __tablename__ = 'income_statements'

    id = db.Column(db.Integer, primary_key=True)

    # 📆 Reporting Period
    period_start = db.Column(db.Date, nullable=False, index=True)
    period_end = db.Column(db.Date, nullable=False, index=True)

    # 🏢 Contextual Links
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 💰 Financial Totals
    total_income = db.Column(db.Numeric(precision=12, scale=2), default=0)
    total_expenses = db.Column(db.Numeric(precision=12, scale=2), default=0)
    net_surplus = db.Column(db.Numeric(precision=12, scale=2), default=0)

    # 📊 Categorized Breakdown
    income_breakdown = db.Column(JSONB, nullable=True)   # e.g., { "Service Charges": 12000, "Rent": 3000 }
    expense_breakdown = db.Column(JSONB, nullable=True)  # e.g., { "Repairs": 2500, "Utilities": 1800 }

    # 🤖 AI / GAR Enhancements
    parsed_text = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    ai_summary = db.Column(db.Text, nullable=True)
    gar_insights = db.Column(db.Text, nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)
    gar_context_reference = db.Column(db.String(255), nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔌 3rd-Party Integration
    external_reference = db.Column(db.String(100), nullable=True)
    external_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Failed, Manual
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🕵️ Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔗 Relationships
    client = db.relationship('Client', backref='income_statements')
    unit = db.relationship('Unit', backref='income_statements')
    created_by = db.relationship('User', backref='generated_income_statements')

    def __repr__(self):
        return f"<IncomeStatement client_id={self.client_id} period={self.period_start} to {self.period_end}>"
