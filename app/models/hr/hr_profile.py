from datetime import datetime
from app.extensions import db

class HRProfile(db.Model):
    __tablename__ = 'hr_profiles'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("hr_profile", uselist=False))
    department = db.relationship('Department', back_populates='employees')
    manager = db.relationship("User", foreign_keys=[manager_id], backref="managed_profiles")

    # 📋 Employment Metadata
    job_title = db.Column(db.String(100), nullable=True)
    employment_status = db.Column(db.String(50))                          # Full-Time, Part-Time, Contract
    employment_type = db.Column(db.String(50), nullable=True)            # Permanent, Temporary, Intern
    employment_band = db.Column(db.String(50), nullable=True)            # A, B, C – internal grading
    start_date = db.Column(db.Date)
    probation_end_date = db.Column(db.Date)
    contract_reference = db.Column(db.String(100), nullable=True)
    hr_file_url = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # 🔐 Privacy & Consent Controls
    visibility_scope = db.Column(db.String(100), default='Admin,HR')     # Comma-delimited roles
    is_private = db.Column(db.Boolean, default=True)
    shared_with_director = db.Column(db.Boolean, default=False)
    consent_verified = db.Column(db.Boolean, default=False)              # Explicit GDPR-style consent

    # 🔌 API & External System Sync
    external_reference = db.Column(db.String(100), nullable=True)
    source_system = db.Column(db.String(100), nullable=True)             # e.g., BambooHR, ADP, CSV
    sync_status = db.Column(db.String(50), default='Pending')            # Pending / Synced / Failed
    is_external = db.Column(db.Boolean, default=False)

    # 🤖 AI + Parsing (Phase 1)
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)                   # e.g., {"probation": "3 months"}
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_confidence_score = db.Column(db.Float, nullable=True)
    ai_profile_locked = db.Column(db.Boolean, default=False)             # Freeze AI overwrite
    flagged_sections = db.Column(db.JSON, nullable=True)                 # e.g., {"start_date": "inconsistent"}

    # 🧠 AI HR Risk/Insight (Phase 2+)
    ai_hr_insights = db.Column(db.Text, nullable=True)                   # e.g., predicted attrition risk, comments

    # 🛡️ GAR Governance Review
    gar_flags = db.Column(db.Text, nullable=True)                        # Flagged clauses, red tape risks
    requires_hr_review = db.Column(db.Boolean, default=False)
    approved_by_hr = db.Column(db.Boolean, default=False)
    review_notes = db.Column(db.Text, nullable=True)

    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)


    def __repr__(self):
        return f"<HRProfile user_id={self.user_id} title='{self.job_title}'>"



