from datetime import datetime
from app.extensions import db

class QuoteRecipient(db.Model):
    __tablename__ = 'quote_recipients'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)
    contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invited_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 📅 Timing / Audit Trail
    invited_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)
    contractor_viewed_at = db.Column(db.DateTime, nullable=True)

    # 📊 Status Tracking
    status = db.Column(db.String(50), default='Invited')  # Invited, Responded, Closed
    response_status = db.Column(db.String(50), nullable=True)  # Approved, Not Selected, No Response, Withdrawn
    contractor_viewed = db.Column(db.Boolean, default=False)
    has_submitted_response = db.Column(db.Boolean, default=False)

    # 💬 Instructions & Notes
    notes = db.Column(db.Text, nullable=True)  # Optional custom message from PM
    invitation_message = db.Column(db.Text, nullable=True)  # Saved content of system-generated invite
    decision_feedback = db.Column(db.Text, nullable=True)  # Optional post-decision comments

    # 📬 Notification Tracking
    notification_sent = db.Column(db.Boolean, default=False)
    notification_sent_at = db.Column(db.DateTime, nullable=True)
    reminder_sent = db.Column(db.Boolean, default=False)
    reminder_sent_at = db.Column(db.DateTime, nullable=True)

    # 🔐 Visibility & Governance
    visibility_scope = db.Column(db.String(50), default='Private')  # Private, Shared, Auditable, Public
    visible_to_directors = db.Column(db.Boolean, default=False)  # Show in Capex/Quote review by board
    visible_to_contractor = db.Column(db.Boolean, default=True)
    archived_by_admin = db.Column(db.Boolean, default=False)

    # 🤖 AI & Auto-Selection Support
    auto_generated = db.Column(db.Boolean, default=False)  # Selected via matching AI or business logic
    selection_rank = db.Column(db.Integer, nullable=True)  # 1st match, 2nd match, etc.
    ai_suitability_score = db.Column(db.Float, nullable=True)  # Optional AI-matched contractor relevance

    # 🧠 GAR Support Fields (Governance AI Review)
    gar_visible = db.Column(db.Boolean, default=True)
    gar_flagged = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)
    gar_reason_excluded = db.Column(db.Text, nullable=True)
    gar_alignment_score = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<QuoteRecipient id={self.id} contractor={self.contractor_id} status={self.status}>"
