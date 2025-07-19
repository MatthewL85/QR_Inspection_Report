from datetime import datetime
from app.extensions import db

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)

    # 📌 Core Info
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    budget = db.Column(db.Numeric(12, 2), nullable=True)
    currency = db.Column(db.String(10), default="EUR")
    fiscal_year_start = db.Column(db.Date, nullable=True)
    department_code = db.Column(db.String(50), unique=True, nullable=True)
    cost_center_code = db.Column(db.String(50), nullable=True)

    # 🔐 Governance
    visibility_scope = db.Column(db.String(100), default='HR,Admin')
    is_active = db.Column(db.Boolean, default=True)
    is_budget_locked = db.Column(db.Boolean, default=False)
    external_reference = db.Column(db.String(100), nullable=True)
    synced_with_hris = db.Column(db.Boolean, default=False)

    # 🔗 Leadership
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 🤖 Phase 1: AI Processing Fields
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 Phase 2: GAR Intelligence & Decision Support
    gar_scorecard = db.Column(db.JSON, nullable=True)                    # {"spend_efficiency": 0.88, "leadership": 0.93}
    gar_flagged_issues = db.Column(db.Text, nullable=True)
    gar_recommendation = db.Column(db.Text, nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 📅 Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔁 Relationships
    manager = db.relationship("User", foreign_keys=[manager_id], backref="managed_departments")
    employees = db.relationship("HRProfile", backref="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name} (ID: {self.id})>"
