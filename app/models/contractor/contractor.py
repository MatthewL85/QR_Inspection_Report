from datetime import datetime
from app.extensions import db

class Contractor(db.Model):
    __tablename__ = 'contractors'

    id = db.Column(db.Integer, primary_key=True)

    # 🎯 Core Company Details
    company_name = db.Column(db.String(255), nullable=False)
    registration_number = db.Column(db.String(100))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    contact_name = db.Column(db.String(100))
    contact_email = db.Column(db.String(255))
    address = db.Column(db.String(255))
    business_type = db.Column(db.String(100))      # Plumbing, Electrical, etc.
    contractor_type = db.Column(db.String(100))    # Sole Trader, Ltd, Partnership (optional)
    region = db.Column(db.String(100), nullable=True)
    coverage_area = db.Column(db.String(255), nullable=True)
    tags = db.Column(db.String(255), nullable=True)

    # 🔐 Security / Consent / Role Access
    is_active = db.Column(db.Boolean, default=True)
    consent_to_contact = db.Column(db.Boolean, default=False)
    visibility_scope = db.Column(db.String(100), default='Admin,PM')
    share_with_directors = db.Column(db.Boolean, default=False)

    # 🔌 External/API Fields
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    sync_status = db.Column(db.String(50), default='Pending')
    is_external = db.Column(db.Boolean, default=False)

    # 🤖 AI Parsing Fields
    parsed_summary = db.Column(db.Text)
    parsed_text = db.Column(db.Text)
    extracted_data = db.Column(db.JSON)
    parsing_status = db.Column(db.String(50), default="Pending")
    parsed_at = db.Column(db.DateTime)
    parsed_by_ai_version = db.Column(db.String(50))
    ai_profile_locked = db.Column(db.Boolean, default=False)
    ai_quality_score = db.Column(db.Float, nullable=True)

    # 🧠 GAR Governance
    compliance_score = db.Column(db.Float)
    performance_rating = db.Column(db.String(10))
    gar_trust_score = db.Column(db.Float)
    is_gar_preferred = db.Column(db.Boolean, default=False)
    gar_notes = db.Column(db.Text)
    risk_assessment = db.Column(db.String(20))
    compliance_flags = db.Column(db.Text, nullable=True)
    last_ai_audit_at = db.Column(db.DateTime)

    # 💰 Financial Health (AI or Manual)
    avg_invoice_turnaround_days = db.Column(db.Float, nullable=True)
    flagged_financial_issues = db.Column(db.Text, nullable=True)

    # 📊 Performance Metrics
    job_acceptance_rate = db.Column(db.Float, nullable=True)
    completion_success_rate = db.Column(db.Float, nullable=True)
    avg_response_time_minutes = db.Column(db.Float, nullable=True)

    # 💬 Interaction
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 📅 Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔗 Relationships
    work_orders = db.relationship("WorkOrder", backref="contractor_company", lazy=True)
    compliance_documents = db.relationship("ContractorComplianceDocument", back_populates="contractor", lazy=True)
    performance_records = db.relationship("ContractorPerformance", backref="contractor_entity", lazy=True)
    users = db.relationship('User', back_populates='contractor', lazy=True)

    def __repr__(self):
        return f"<Contractor {self.company_name} ({self.business_type})>"

    @property
    def name(self) -> str:
        """Display alias so templates can use contractor.name like client.name."""
        return self.company_name
