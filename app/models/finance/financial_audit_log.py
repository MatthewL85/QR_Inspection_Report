from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from app.extensions import db

class FinancialAuditLog(db.Model):
    __tablename__ = 'financial_audit_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔍 Action Metadata
    action_type = db.Column(db.String(100), nullable=False, index=True)  # create, update, delete
    table_name = db.Column(db.String(100), nullable=False, index=True)
    record_id = db.Column(db.Integer, nullable=False, index=True)
    field_changed = db.Column(db.String(100), nullable=True)
    previous_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)

    # 👤 User Context
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_role = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(100), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    # 📅 Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🤖 AI / GAR Context
    flagged_by_ai = db.Column(db.Boolean, default=False)
    reason_for_flag = db.Column(db.String(255), nullable=True)
    ai_recommendation = db.Column(db.String(255), nullable=True)
    is_gar_verified = db.Column(db.Boolean, default=False)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    gar_flag_confidence = db.Column(db.Float, nullable=True)  # ✅ NEW
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🔌 External Sync & Governance
    sync_status = db.Column(db.String(50), default='Not Synced')
    external_system = db.Column(db.String(100), nullable=True)
    external_reference = db.Column(db.String(100), nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🛡️ Compliance & Context
    is_data_protection_event = db.Column(db.Boolean, default=False)  # ✅ NEW
    linked_module = db.Column(db.String(100), nullable=True)         # ✅ NEW

    # 🔁 Relationships
    user = db.relationship('User', backref='financial_audit_logs')

    def __repr__(self):
        return f"<Audit {self.action_type} on {self.table_name}:{self.record_id} at {self.timestamp}>"

