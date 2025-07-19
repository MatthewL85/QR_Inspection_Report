from datetime import datetime
from app.extensions import db

class CapexApproval(db.Model):
    __tablename__ = 'capex_approvals'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    capex_request_id = db.Column(db.Integer, db.ForeignKey('capex_requests.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 📋 Approval Info
    approval_notes = db.Column(db.Text)
    status = db.Column(db.String(50), default='Pending')                # Pending, Approved, Rejected, Deferred, etc.
    approved_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🧠 AI Parsing & Decision Summary
    parsed_summary = db.Column(db.Text, nullable=True)                  # GAR human-readable decision summary
    extracted_data = db.Column(db.JSON, nullable=True)                  # JSON structured data (source info)
    parsing_status = db.Column(db.String(50), default='Pending')        # Parsing state
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)            # Portal, PDF, Email
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Decision Support
    gar_alignment_score = db.Column(db.Float)                           # 0.00–1.00 score for consistency with policy
    gar_decision_alignment = db.Column(db.String(100))                  # Aligned, Conflict, Insufficient Data
    gar_rationale = db.Column(db.Text)                                  # Why GAR supports/flags the decision
    gar_flagged_risks = db.Column(db.Text)                              # Governance concerns, anomalies
    is_gar_recommended = db.Column(db.Boolean, default=False)           # GAR recommendation flag

    # ✅ Interaction & Feedback
    gar_chat_ready = db.Column(db.Boolean, default=False)               # Enable for frontend Q&A/chat
    gar_feedback = db.Column(db.Text, nullable=True)                    # Director/PM feedback on AI suggestion

    # 🔁 Relationships
    request = db.relationship("CapexRequest", back_populates="approvals")
    approver = db.relationship("User", foreign_keys=[approved_by], backref="capex_approvals")

    def __repr__(self):
        return f'<CapexApproval #{self.id} for Request {self.capex_request_id}>'

