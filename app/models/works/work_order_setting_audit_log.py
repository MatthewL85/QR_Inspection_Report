from datetime import datetime
from app.extensions import db

class WorkOrderSettingAuditLog(db.Model):
    __tablename__ = 'work_order_setting_audit_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Reference to the settings changed
    setting_id = db.Column(db.Integer, db.ForeignKey('work_order_settings.id'), nullable=False)
    changed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 📝 Change Metadata
    change_type = db.Column(db.String(50), nullable=False)  # Created, Updated, Deleted
    field_changed = db.Column(db.String(100), nullable=True)  # e.g., "allow_assign_to_staff"
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    change_reason = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # 🤖 AI / GAR Impact Analysis
    ai_impact_assessment = db.Column(db.Text, nullable=True)           # AI interpretation of impact
    gar_compliance_effect = db.Column(db.Text, nullable=True)          # Governance/Legal impact notes
    is_ai_flagged = db.Column(db.Boolean, default=False)
    gar_score_delta = db.Column(db.Float, nullable=True)               # Impact on GAR governance rating

    # 🤖 AI Parsing / Summary Fields
    parsed_summary = db.Column(db.Text, nullable=True)                 # Natural language summary of change
    extracted_data = db.Column(db.JSON, nullable=True)                 # AI-extracted key-value changes
    parsing_status = db.Column(db.String(50), default='Pending')       # Parsing status
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🔗 Relationships
    setting = db.relationship("WorkOrderSettings", backref="audit_logs")
    changed_by = db.relationship("User", foreign_keys=[changed_by_id])

    def __repr__(self):
        return (
            f"<WorkOrderSettingAuditLog setting_id={self.setting_id} "
            f"changed_by={self.changed_by_id} type={self.change_type}>"
        )
