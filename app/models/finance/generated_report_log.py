from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates

class GeneratedReportLog(db.Model):
    __tablename__ = 'generated_report_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Relationships
    config_id = db.Column(db.Integer, db.ForeignKey('financial_report_configs.id'), nullable=True)
    generated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)

    # 📄 Output Metadata
    report_name = db.Column(db.String(255), nullable=True, index=True)
    output_format = db.Column(db.String(10), default='PDF')  # PDF, CSV, XLS, JSON
    output_path = db.Column(db.String(255), nullable=True)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    report_status = db.Column(db.String(50), default='Completed')  # Pending, Failed, Completed

    # 🤖 AI / GAR Integration
    parsed_summary = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)
    ai_scorecard = db.Column(JSONB, nullable=True)
    ai_analysis = db.Column(db.Text, nullable=True)
    gar_insight_score = db.Column(db.Float, nullable=True)  # 0.0 - 1.0 accuracy / compliance score
    gar_recommendations = db.Column(db.Text, nullable=True)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    flagged_by_gar = db.Column(db.Boolean, default=False)
    context_tags = db.Column(db.ARRAY(db.String(50)), nullable=True)
    role_visibility = db.Column(db.ARRAY(db.String(50)), nullable=True)

    # 🧠 GAR Chat Integration
    gar_chat_ready = db.Column(db.Boolean, default=False)              # Available for GAR Q&A
    gar_feedback = db.Column(db.Text, nullable=True)                   # Optional feedback on GAR result

    # 🔌 3rd-Party Integration
    external_export_id = db.Column(db.String(100), nullable=True)
    synced_with = db.Column(db.String(50), nullable=True)  # e.g., 'Xero', 'PowerBI'
    sync_status = db.Column(db.String(50), default='Not Synced')  # Synced, Failed, Pending
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # 🔐 Audit Trail
    ip_generated_from = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔗 Relationships
    generated_by = db.relationship("User", foreign_keys=[generated_by_id])
    financial_report_config = db.relationship("FinancialReportConfig", backref="generated_reports")
    client = db.relationship("Client", backref="report_logs")
    unit = db.relationship("Unit", backref="report_logs")

    def __repr__(self):
        return f"<GeneratedReportLog {self.report_name or self.output_format} @ {self.generated_at}>"

