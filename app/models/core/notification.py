from datetime import datetime
from app.extensions import db

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 User Target
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient = db.relationship("User", backref="notifications")

    # 💬 Message & Type
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))  # alert, inspection, capex, policy, etc.
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔗 UI Routing Support
    link_url = db.Column(db.String(255), nullable=True)  # e.g., "/work_orders/123"

    # 🤖 AI Parsing (Phase 1)
    parsed_summary = db.Column(db.Text, nullable=True)            # AI-readable summary of message
    extracted_data = db.Column(db.JSON, nullable=True)            # Structured dict (target ID, type, etc.)
    parsing_status = db.Column(db.String(50), default='Pending')  # Pending, Completed, Failed
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)      # Source: webhook, upload, etc.
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Governance Support (Phase 2)
    priority_level = db.Column(db.String(20), default='Normal')   # High, Medium, Low
    gar_category = db.Column(db.String(100))                      # Governance Alert, Maintenance, etc.
    is_governance_related = db.Column(db.Boolean, default=False)
    suggested_action = db.Column(db.String(255))                  # e.g., "Escalate to Admin"
    ai_confidence = db.Column(db.Float, nullable=True)            # AI confidence score

    def __repr__(self):
        return f"<Notification to={self.recipient_id} type={self.type}>"
