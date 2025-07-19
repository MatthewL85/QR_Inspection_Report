from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB


class CashflowStatement(db.Model):
    __tablename__ = 'cashflow_statements'

    id = db.Column(db.Integer, primary_key=True)

    # 📆 Reporting Period
    report_date = db.Column(db.Date, nullable=False, index=True)

    # 🏢 Contextual References
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 💸 Financial Sections
    operating_activities = db.Column(db.Numeric(precision=12, scale=2), default=0)
    investing_activities = db.Column(db.Numeric(precision=12, scale=2), default=0)
    financing_activities = db.Column(db.Numeric(precision=12, scale=2), default=0)
    net_cash_flow = db.Column(db.Numeric(precision=12, scale=2), default=0)

    # 📊 Optional Detailed Breakdown
    breakdown_operating = db.Column(JSONB, nullable=True)
    breakdown_investing = db.Column(JSONB, nullable=True)
    breakdown_financing = db.Column(JSONB, nullable=True)

    # 🤖 AI / GAR Enhancements
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_summary = db.Column(db.Text, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    gar_insights = db.Column(db.Text, nullable=True)
    gar_recommendation = db.Column(db.String(255), nullable=True)
    gar_context_reference = db.Column(db.String(255), nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)  # e.g., ["Admin", "Director"]

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🕵️‍♂️ Audit & Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔗 Relationships
    client = db.relationship('Client', backref='cashflow_statements')
    unit = db.relationship('Unit', backref='cashflow_statements')
    created_by = db.relationship('User', backref='generated_cashflow_statements')

    def __repr__(self):
        return f"<CashFlowStatement client_id={self.client_id} report_date={self.report_date}>"

