from app.extensions import db
from datetime import datetime

class MaintenanceRequest(db.Model):
    __tablename__ = 'maintenance_requests'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    member_id = db.Column(
        db.Integer,
        db.ForeignKey('members.id', use_alter=True, name='fk_mr_member', deferrable=True, initially='DEFERRED'),
        nullable=False
    )
    member = db.relationship('Member', backref='maintenance_requests')

    unit_id = db.Column(
        db.Integer,
        db.ForeignKey('units.id', use_alter=True, name='fk_mr_unit', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    unit = db.relationship('Unit', backref='maintenance_requests')

    work_order_id = db.Column(
        db.Integer,
        db.ForeignKey('work_orders.id', use_alter=True, name='fk_mr_work_order', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    work_order = db.relationship('WorkOrder', backref='maintenance_request')

    requested_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', use_alter=True, name='fk_mr_requested_by', deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    requested_by = db.relationship('User', foreign_keys=[requested_by_id])

    # 📝 Request Details
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    urgency_level = db.Column(db.String(50), default='Normal')
    urgency_reason = db.Column(db.String(255), nullable=True)
    request_channel = db.Column(db.String(50), nullable=True)

    # 📎 Attachments / Media
    attachment_url = db.Column(db.String(500), nullable=True)
    attachments_count = db.Column(db.Integer, default=0)
    media_uploaded = db.Column(db.Boolean, default=False)
    doc_links = db.Column(db.JSON, nullable=True)
    photo_links = db.Column(db.JSON, nullable=True)

    # 🔐 Privacy & Consent
    visibility_scope = db.Column(db.String(100), default='Admin,PM')
    consent_verified = db.Column(db.Boolean, default=False)
    is_private = db.Column(db.Boolean, default=False)
    shared_with_director = db.Column(db.Boolean, default=False)

    # 🔌 External / API Integration
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    is_external = db.Column(db.Boolean, default=False)
    sync_status = db.Column(db.String(50), default='Pending')

    # 🤖 AI / GAR Fields
    ai_tags = db.Column(db.Text, nullable=True)
    ai_priority_score = db.Column(db.Float, nullable=True)
    gar_summary = db.Column(db.Text, nullable=True)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_confidence_score = db.Column(db.Float, nullable=True)
    ai_profile_locked = db.Column(db.Boolean, default=False)
    flagged_sections = db.Column(db.JSON, nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🗒️ Internal + Lifecycle
    status = db.Column(db.String(50), default='Pending')
    internal_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<MaintenanceRequest #{self.id} - {self.title}>'
