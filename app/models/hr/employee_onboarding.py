from datetime import datetime
from app.extensions import db

class EmployeeOnboarding(db.Model):
    __tablename__ = 'employee_onboarding'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # 🌐 Onboarding Stages
    onboarding_status = db.Column(db.String(50), default='Pending')  # Pending, In Progress, Completed, Terminated
    onboarding_type = db.Column(db.String(50), default='Full-Time')  # Full-Time, Contractor, Intern, etc.
    current_step = db.Column(db.String(100), nullable=True)          # e.g., Contract Signed, Documents Uploaded
    step_notes = db.Column(db.Text, nullable=True)

    # 🔹 Checklist Flags
    contract_signed = db.Column(db.Boolean, default=False)
    documents_uploaded = db.Column(db.Boolean, default=False)
    hr_policy_acknowledged = db.Column(db.Boolean, default=False)
    induction_completed = db.Column(db.Boolean, default=False)
    equipment_issued = db.Column(db.Boolean, default=False)

    # 🎓 Assigned Roles / Info
    job_title = db.Column(db.String(100), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    start_date = db.Column(db.Date, nullable=True)
    completion_date = db.Column(db.DateTime, nullable=True)          # When onboarding is fully completed

    # 🧐 AI/GAR Assistance
    ai_onboarding_path = db.Column(db.JSON, nullable=True)              # Suggested steps/tasks by AI
    gar_summary = db.Column(db.Text, nullable=True)
    gar_flagged_gaps = db.Column(db.Text, nullable=True)
    gar_readiness_score = db.Column(db.Float, nullable=True)           # 0.0 to 1.0
    ai_confidence_score = db.Column(db.Float, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    gar_chat_ready = db.Column(db.Boolean, default=False)

    # 🔍 Review & Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 🔗 Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='onboarding_profile')
    company = db.relationship('Company', backref='onboarding_records')
    department = db.relationship('Department', backref='onboarded_employees')
    manager = db.relationship('User', foreign_keys=[manager_id])
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_onboardings')
    updated_by = db.relationship('User', foreign_keys=[updated_by_id], backref='updated_onboardings')

    def __repr__(self):
        return f"<EmployeeOnboarding user_id={self.user_id} status='{self.onboarding_status}'>"

