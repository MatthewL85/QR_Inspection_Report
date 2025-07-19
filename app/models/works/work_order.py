# app/models/work_order.py

from app.extensions import db
from datetime import datetime

class WorkOrder(db.Model):
    __tablename__ = 'work_orders'

    id = db.Column(db.Integer, primary_key=True)

    # 🔧 Core Info
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractors.id'), nullable=True)
    title = db.Column(db.String(255))
    request_type = db.Column(db.String(50), default='Work Order')  # Work Order, Quote Request, Emergency Callout
    description = db.Column(db.Text, nullable=False)
    business_type = db.Column(db.String(100))  # Plumbing, Electrical, etc.
    status = db.Column(db.String(50), default='Open')  # Open, Quote Requested, Quote Submitted, Quote Approved, Accepted, Completed, Returned
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 👤 Occupant Info
    occupant_name = db.Column(db.String(100))
    occupant_apartment = db.Column(db.String(50))
    occupant_phone = db.Column(db.String(20))
    privacy_scope = db.Column(db.String(100), default='PropertyManagerOnly')
    access_masked = db.Column(db.Boolean, default=False)

    # 🗓️ Visit Planning
    preferred_visit_date = db.Column(db.Date, nullable=True)

    # 🔗 Relationships
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    client = db.relationship('Client', backref='work_orders')

    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    unit = db.relationship('Unit', backref='work_orders')

    preferred_contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    second_preferred_contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    accepted_contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    preferred_contractor = db.relationship('User', foreign_keys=[preferred_contractor_id], backref='preferred_work_orders')
    second_preferred_contractor = db.relationship('User', foreign_keys=[second_preferred_contractor_id], backref='secondary_work_orders')
    accepted_contractor = db.relationship('User', foreign_keys=[accepted_contractor_id], backref='accepted_work_orders')

    # ✅ NEW: Internal Assignment Fields
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_team_id = db.Column(db.Integer, db.ForeignKey('contractor_teams.id'), nullable=True)

    assigned_user = db.relationship('User', foreign_keys=[assigned_user_id], backref='assigned_work_orders')
    assigned_team = db.relationship('ContractorTeam', foreign_keys=[assigned_team_id], backref='assigned_work_orders')

    # 🧾 Quote Integration
    quote_requested = db.Column(db.Boolean, default=False)
    quote_deadline = db.Column(db.DateTime, nullable=True)
    quote_status = db.Column(db.String(50), default='Pending')  # Pending, Submitted, Approved, Rejected
    quote_approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    quote_approved_by = db.relationship('User', foreign_keys=[quote_approved_by_id], backref='approved_quotes')
    quote_approved_at = db.Column(db.DateTime, nullable=True)
    converted_to_work_order = db.Column(db.Boolean, default=False)

    # 🔄 Optional Linked Tables
    maintenance_request_id = db.Column(db.Integer, db.ForeignKey('maintenance_requests.id'), nullable=True)
    maintenance_request = db.relationship('MaintenanceRequest', backref='work_order', uselist=False)

    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'), nullable=True)
    alert = db.relationship('Alert', backref='work_orders')

    escalated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    escalated_by = db.relationship('User', foreign_keys=[escalated_by_id], backref='escalated_work_orders')

    completion = db.relationship('WorkOrderCompletion', backref='work_order', uselist=False)
    feedback = db.relationship('ContractorFeedback', backref='work_order', uselist=False)

    # 📎 External/API Fields
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    is_external = db.Column(db.Boolean, default=False)
    is_imported = db.Column(db.Boolean, default=False)
    geo_location = db.Column(db.String(100), nullable=True)

    # 📎 Document/Media Tracking
    attachments_count = db.Column(db.Integer, default=0)

    # 🤖 AI Parsing Fields (Phase 1)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)
    ai_field_ranking = db.Column(db.JSON, nullable=True)

    # 🧠 GAR Evaluation Fields (Phase 2+)
    gar_risk_level = db.Column(db.String(50))
    gar_urgency_score = db.Column(db.Float)
    gar_non_compliance_notes = db.Column(db.Text)
    gar_flagged = db.Column(db.Boolean, default=False)
    gar_recommended_action = db.Column(db.String(255))
    gar_alignment_score = db.Column(db.Float)
    gar_explanation = db.Column(db.Text, nullable=True)

    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🔁 Relationships to Quotes
    quote_responses = db.relationship('QuoteResponse', backref='work_order', lazy=True)
    quote_recipients = db.relationship('QuoteRecipient', backref='work_order', lazy=True)

    def __repr__(self):
        return f"<WorkOrder id={self.id} title='{self.title}' status={self.status}>"
