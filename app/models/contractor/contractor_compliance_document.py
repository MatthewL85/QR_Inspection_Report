# app/models/contractor_compliance_document.py

from datetime import datetime
from app.extensions import db

class ContractorComplianceDocument(db.Model):
    __tablename__ = 'contractor_compliance_documents'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractors.id'), nullable=False)
    contractor = db.relationship('Contractor', backref='compliance_documents')

    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id])
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])

    # 📁 Document Metadata
    document_type = db.Column(db.String(100), nullable=False)     # e.g., insurance, H&S cert
    document_category = db.Column(db.String(100), nullable=True)  # Certificate, Policy, Report
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ AI Parsing Fields
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(100), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_profile_locked = db.Column(db.Boolean, default=False)
    ai_quality_score = db.Column(db.Float, nullable=True)
    flagged_sections = db.Column(db.JSON, nullable=True)  # e.g., {"terms": "missing", "limits": "low"}

    # ✅ GAR Governance
    is_compliant = db.Column(db.Boolean, default=True)
    gar_flagged_risks = db.Column(db.Text, nullable=True)
    gar_recommendations = db.Column(db.Text, nullable=True)
    gar_compliance_score = db.Column(db.Float, nullable=True)
    gar_ai_notes = db.Column(db.Text, nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🔐 Visibility & Consent
    is_required_for_work_order = db.Column(db.Boolean, default=True)
    is_private = db.Column(db.Boolean, default=False)
    consent_verified = db.Column(db.Boolean, default=False)
    visibility_scope = db.Column(db.String(100), default='Admin,PM,Director')

    # 📬 Workflow / Notifications
    reminder_sent = db.Column(db.Boolean, default=False)
    reminder_date = db.Column(db.DateTime, nullable=True)

    # 🧾 Review & Governance Tracking
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_comment = db.Column(db.Text, nullable=True)
    is_governing_doc = db.Column(db.Boolean, default=False)            # Required for operational eligibility
    audit_trail_linked = db.Column(db.Boolean, default=False)
    linked_policy_id = db.Column(db.Integer, nullable=True)            # Optional: link to InsurancePolicy or LegalDoc

    # 🔌 API / External Support
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)
    is_external = db.Column(db.Boolean, default=False)
    sync_status = db.Column(db.String(50), default='Pending')  # Synced, Pending, Failed

    def __repr__(self):
        return f"<ContractorComplianceDocument type={self.document_type} contractor_id={self.contractor_id}>"
