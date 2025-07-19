# app/models/exports/exported_file_log.py

from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class ExportedFileLog(db.Model):
    __tablename__ = 'exported_file_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Source Context
    export_type = db.Column(db.String(100), nullable=False)  # e.g., ledger_summary, aged_debtors, vat_return
    related_model = db.Column(db.String(100), nullable=True)  # Optional: 'LedgerJournal', etc.
    related_id = db.Column(db.Integer, nullable=True)

    # 📁 File Details
    file_path = db.Column(db.String(255), nullable=False)
    file_format = db.Column(db.String(10), nullable=False, default='PDF')  # PDF, CSV, XLS, etc.
    file_name = db.Column(db.String(150), nullable=True)
    download_url = db.Column(db.String(255), nullable=True)  # Optional: link to retrieve/download

    # 🔐 Security, GDPR & Role-Aware Access
    visibility_scope = db.Column(db.String(50), default='Admin')  
    # Options: Admin, PM, Director, MemberOwner, ResidentTenant
    is_sensitive = db.Column(db.Boolean, default=False)  # GDPR: restrict certain roles (e.g., directors can't see resident files)
    redacted_for_public = db.Column(db.Boolean, default=False)  # If true, a redacted version may be exposed to non-privileged roles

    # 👥 Ownership and Access Links
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)  # Link to a specific unit
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Usually the member (owner)
    resident_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Could be same as owner if self-occupied

    # 🧠 AI / GAR Enhancements
    parsed_summary = db.Column(db.Text, nullable=True)  # AI-generated human-readable summary
    extracted_data = db.Column(JSONB, nullable=True)    # AI-parsed JSON fields (e.g., invoice totals)
    gar_context_reference = db.Column(db.String(100), nullable=True)  # For contextual threading
    gar_notes = db.Column(db.Text, nullable=True)  # Optional notes left by GAR
    flagged_by_gar = db.Column(db.Boolean, default=False)

    # 📜 Audit Trail
    exported_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    exported_by = db.relationship('User', foreign_keys=[exported_by_id])
    exported_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🧪 Future-Proof Flags
    is_api_exposed = db.Column(db.Boolean, default=False)  # Whether this file is visible via external API endpoints
    metadata_tags = db.Column(JSONB, nullable=True)  # Optional: searchable metadata tags (e.g., {"type": "compliance", "doc": "AGM"})

    def __repr__(self):
        return f"<ExportedFileLog {self.export_type}.{self.file_format} by={self.exported_by_id}>"
