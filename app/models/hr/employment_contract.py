from datetime import datetime
from app.extensions import db

class EmploymentContract(db.Model):
    __tablename__ = 'employment_contracts'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'))

    # 📝 Contract Details
    contract_type = db.Column(db.String(50), nullable=False)                     # Full-Time, Contractor, Intern
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    terms_summary = db.Column(db.Text, nullable=True)
    contract_reference_code = db.Column(db.String(100), nullable=True)
    contract_status = db.Column(db.String(50), default="Active")                 # Active, Expired, Terminated, etc.

    # 🔐 Governance & Access
    visibility_scope = db.Column(db.String(100), default='HR,Admin')
    is_confidential = db.Column(db.Boolean, default=True)
    is_consent_verified = db.Column(db.Boolean, default=False)

    # 🔌 External/Integration Support
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')
    is_external = db.Column(db.Boolean, default=False)

    # 🤖 AI Parsing Fields (Phase 1)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)                           # {"notice_period": "30d", "type": "contractor"}
    ai_clause_map = db.Column(db.JSON, nullable=True)                            # {"termination": "...", "salary": "..."}
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_confidence_score = db.Column(db.Float, nullable=True)
    ai_lock = db.Column(db.Boolean, default=False)                               # Prevent re-parsing after verification

    # 🧠 GAR Intelligence & Risk Fields
    gar_scorecard = db.Column(db.JSON, nullable=True)                            # {"fairness": 0.85, "risk": 0.12}
    gar_flagged_clauses = db.Column(db.Text, nullable=True)
    gar_recommendation = db.Column(db.Text, nullable=True)
    gar_rank = db.Column(db.String(10), nullable=True)                           # A, B, C ranking
    is_gar_reviewed = db.Column(db.Boolean, default=False)

    # 💬 GAR Chat Interaction (Phase 2+)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 📅 Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔁 Relationships
    user = db.relationship("User", foreign_keys=[user_id], backref="employment_contracts")
    document = db.relationship("Document", foreign_keys=[document_id], backref="linked_contracts")

    def __repr__(self):
        return f"<EmploymentContract id={self.id} user_id={self.user_id} type={self.contract_type}>"

