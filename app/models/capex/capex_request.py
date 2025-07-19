from datetime import datetime
from app.extensions import db

class CapexRequest(db.Model):
    __tablename__ = 'capex_requests'

    id = db.Column(db.Integer, primary_key=True)

    # 🔧 Core Details
    area = db.Column(db.String(100), nullable=False)                     # e.g., "Landscaping", "Security", "Lift"
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Pending')                 # Pending, Approved, Rejected, In Review
    urgency = db.Column(db.String(50), default='Normal')                 # Normal, High, Critical
    estimated_cost = db.Column(db.Float, nullable=True)
    justification = db.Column(db.Text, nullable=True)
    file = db.Column(db.String(200))                                     # Uploaded request file path

    # 🔐 Submitter Info
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🏢 Related to Client & Unit
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)  # Optional: tie to specific unit
    is_owner = db.Column(db.Boolean, default=False)                      # Member/Owner
    is_resident = db.Column(db.Boolean, default=False)                   # Living in unit

    # ⚖️ GDPR Privacy & Control
    consent_to_publish = db.Column(db.Boolean, default=False)
    visibility_roles = db.Column(db.String(255), default='Super Admin,Admin,Property Manager,Director')  # No public by default
    gdpr_flagged = db.Column(db.Boolean, default=False)                 # Mark if user refuses data use

    # 🤖 AI Parsing Support (Phase 1)
    parsed_summary = db.Column(db.Text, nullable=True)                  # GAR summary of the request
    extracted_data = db.Column(db.JSON, nullable=True)                  # Structured data for rules engine
    parsing_status = db.Column(db.String(50), default='Pending')        # Pending, Completed, Failed
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)            # e.g., 'pdf', 'image', 'text'
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Decision Support (Phase 2)
    gar_flagged_risks = db.Column(db.Text, nullable=True)               # Legal, budget, safety risks
    gar_recommendations = db.Column(db.Text, nullable=True)
    gar_alignment_score = db.Column(db.Float, nullable=True)            # 0.00 to 1.00
    gar_suggested_priority = db.Column(db.String(20), nullable=True)    # e.g., High
    gar_recommendation_reason = db.Column(db.Text, nullable=True)       # Why GAR made this choice
    gar_review_score = db.Column(db.Float, nullable=True)
    is_gar_flagged = db.Column(db.Boolean, default=False)

    # ✅ GAR Chat Ready
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 📌 Classification & Governance
    tags = db.Column(db.String(255), nullable=True)                     # "security,upgrade"
    capex_type = db.Column(db.String(100), nullable=True)               # Emergency, Preventative
    risk_level = db.Column(db.String(20), nullable=True)                # Low, Medium, High

    # 🔁 Relationships
    client = db.relationship("Client", backref="capex_requests")
    unit = db.relationship("Unit", backref="unit_capex_requests")
    submitter = db.relationship("User", foreign_keys=[submitted_by], backref="submitted_capex_requests")
    approvals = db.relationship("CapexApproval", back_populates="request", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CapexRequest {self.area} | {self.status} | {self.submitted_at}>"

