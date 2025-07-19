from datetime import datetime
from app.extensions import db

class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)

    # 🔧 Core Alert Info
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    category = db.Column(db.String(50))                  # e.g., Maintenance, H&S, Structural
    priority = db.Column(db.String(20))                  # Low, Medium, High, Critical
    status = db.Column(db.String(50), default='Open')    # Open, In Progress, Resolved, Escalated
    created_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 📎 Media / Attachments
    document_filename = db.Column(db.String(255))
    attachments_count = db.Column(db.Integer, default=0)
    media_uploaded = db.Column(db.Boolean, default=False)
    doc_links = db.Column(db.JSON, nullable=True)
    photo_links = db.Column(db.JSON, nullable=True)

    # 🔗 Foreign Keys
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'))
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    escalated_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    submitted_by = db.relationship("User", foreign_keys=[submitted_by_id])
    client = db.relationship("Client", backref="alerts")
    unit = db.relationship("Unit", backref="alerts")
    equipment = db.relationship("Equipment", backref="alerts")
    escalated_to = db.relationship("User", foreign_keys=[escalated_to_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])

    # 📋 Review Metadata
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_notes = db.Column(db.Text, nullable=True)

    # 🔐 Visibility & Privacy
    visibility_scope = db.Column(db.String(100), default='Admin,PM,Contractor')
    is_private = db.Column(db.Boolean, default=False)
    consent_verified = db.Column(db.Boolean, default=False)
    shared_with_director = db.Column(db.Boolean, default=False)

    # 🔌 External Sync & Source
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')
    is_external = db.Column(db.Boolean, default=False)

    # 🤖 AI Parsing Fields
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)
    ai_confidence_score = db.Column(db.Float, nullable=True)
    flagged_sections = db.Column(db.JSON, nullable=True)

    # 🧠 GAR Enhancement Fields
    gar_flagged_risks = db.Column(db.Text, nullable=True)
    gar_priority_score = db.Column(db.Float, nullable=True)
    gar_alignment_score = db.Column(db.Float, nullable=True)
    gar_recommendations = db.Column(db.Text, nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)
    is_governance_concern = db.Column(db.Boolean, default=False)
    escalation_required = db.Column(db.Boolean, default=False)
    escalated_at = db.Column(db.DateTime, nullable=True)

    # 💬 Interaction
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Alert id={self.id} title='{self.title}' status={self.status}>"

