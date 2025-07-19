# models/members/access_log.py

from datetime import datetime
from app.extensions import db

class AccessLog(db.Model):
    __tablename__ = 'access_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)

    user = db.relationship('User', backref='access_logs')
    unit = db.relationship('Unit', backref='access_logs')

    # 📥 Event Details
    access_type = db.Column(db.String(100), nullable=False)         # e.g., 'Resident Login', 'Doc View'
    success = db.Column(db.Boolean, default=True)                   # True = Successful login/view
    ip_address = db.Column(db.String(45), nullable=True)
    device_info = db.Column(db.String(255), nullable=True)
    geo_location = db.Column(db.String(100), nullable=True)         # Optional — "Dublin, Ireland"
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🧠 Privacy & Role Scope
    privacy_scope = db.Column(db.String(100), nullable=True)        # e.g., 'TenantOnly', 'DirectorShared'
    access_masked = db.Column(db.Boolean, default=False)            # Was data redacted for this viewer?

    # 🔌 External Integration
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    is_external = db.Column(db.Boolean, default=False)

    # 🤖 AI & GAR Fields
    parsed_context = db.Column(db.JSON, nullable=True)              # Structured metadata
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    gar_access_risk_score = db.Column(db.Float, nullable=True)      # AI/GAR score (e.g., 0.8 = unusual)
    gar_explanation = db.Column(db.Text, nullable=True)             # GAR rationale or pattern
    gar_flagged_event = db.Column(db.Boolean, default=False)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)        # Freeze if confirmed safe/suspicious

    def __repr__(self):
        return (
            f"<AccessLog user_id={self.user_id} access_type='{self.access_type}' "
            f"success={self.success} at={self.accessed_at}>"
        )


