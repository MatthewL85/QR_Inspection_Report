from datetime import datetime
from app.extensions import db

class WorkOrderPolicy(db.Model):
    __tablename__ = 'work_order_policies'

    id = db.Column(db.Integer, primary_key=True)

    # 🏢 Multi-Tenant Support
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)  # Optional: specific to site

    # 📋 Core Policy Info
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100))                    # e.g., SLA, Safety, Escalation
    version = db.Column(db.String(20), default='1.0')
    description = db.Column(db.Text, nullable=True)         # Human-readable description
    document_url = db.Column(db.String(255), nullable=True) # Optional policy file

    # 🗓 Effective Timeline
    effective_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    # 👤 Ownership & Audit
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    # 🤖 AI Parsing & Summary
    parsed_summary = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)
    parsing_status = db.Column(db.String(50), default='Pending')
    parsed_at = db.Column(db.DateTime)
    parsed_by_ai_version = db.Column(db.String(50))
    ai_source_type = db.Column(db.String(50))
    is_ai_processed = db.Column(db.Boolean, default=False)

    # 🧠 GAR Insights
    gar_flags = db.Column(db.Text, nullable=True)                  # e.g., “missing escalation clause”
    gar_compliance_score = db.Column(db.Float, nullable=True)     # 0.0 – 1.0
    gar_recommendation = db.Column(db.Text, nullable=True)
    is_governance_approved = db.Column(db.Boolean, default=False)

    # 💬 GAR Chat / Interaction
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🔁 Relationships
    company = db.relationship('Company', backref='work_order_policies')
    client = db.relationship('Client', backref='work_order_policies')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_work_order_policies')
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id], backref='reviewed_work_order_policies')

    def __repr__(self):
        return f"<WorkOrderPolicy title='{self.title}' version={self.version} active={self.is_active}>"
