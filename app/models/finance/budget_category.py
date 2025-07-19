from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB


class BudgetCategory(db.Model):
    __tablename__ = 'budget_categories'

    id = db.Column(db.Integer, primary_key=True)

    # 📘 Category Metadata
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    # 🔗 Scope & Control
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    is_global = db.Column(db.Boolean, default=False)  # True = usable across same company

    # 🧾 Accounting Integration
    gl_code = db.Column(db.String(20), nullable=True)
    external_reference = db.Column(db.String(100), nullable=True)  # Xero/QuickBooks/etc.
    integration_status = db.Column(db.String(50), default='Not Synced')
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🧠 AI / GAR Intelligence
    ai_tag = db.Column(db.String(100), nullable=True)  # e.g., 'legal', 'landscaping', 'insurance'
    gar_risk_flag = db.Column(db.Boolean, default=False)
    ai_notes = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🏗️ Area Linking
    area_type_id = db.Column(db.Integer, db.ForeignKey('area_types.id'), nullable=True)

    # 🔐 Audit Trail
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔁 Relationships
    company = db.relationship('Company', backref='budget_categories')
    client = db.relationship('Client', backref='budget_categories')
    created_by = db.relationship('User', backref='created_budget_categories', foreign_keys=[created_by_id])
    area_type = db.relationship('AreaType', backref='budget_categories')

    def __repr__(self):
        return f"<BudgetCategory {self.name} (Client ID: {self.client_id})>"
