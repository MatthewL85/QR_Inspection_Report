from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class ChartOfAccount(db.Model):
    __tablename__ = 'chart_of_accounts'

    id = db.Column(db.Integer, primary_key=True)

    # 📘 Account Details
    account_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    # 🔄 Type and Structure
    account_type = db.Column(db.String(50), nullable=False, index=True)  # Asset, Liability, Equity, Revenue, Expense
    category = db.Column(db.String(50), nullable=True)
    parent_account_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id'), nullable=True)

    # 🌍 Integration
    external_reference = db.Column(db.String(100), nullable=True)
    external_system = db.Column(db.String(100), nullable=True)
    integration_status = db.Column(db.String(50), default='Pending')  # Synced, Pending, Error
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🤖 AI / GAR Enhancements
    is_ai_classified = db.Column(db.Boolean, default=False)
    ai_classification_notes = db.Column(db.Text, nullable=True)
    gar_risk_flag = db.Column(db.String(50), nullable=True)  # Low, Medium, High
    parsed_text = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔐 Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 🔁 Relationships
    parent_account = db.relationship('ChartOfAccount', remote_side=[id], backref='child_accounts')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    updated_by = db.relationship('User', foreign_keys=[updated_by_id])

    def __repr__(self):
        return f"<ChartOfAccount {self.account_code} - {self.name} ({self.account_type})>"
