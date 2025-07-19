from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class LoanDocument(db.Model):
    __tablename__ = 'loan_documents'

    id = db.Column(db.Integer, primary_key=True)

    # 🔐 Multi-Tenant Access
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    # 📎 Linked Loan
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)

    # 📄 Document Metadata
    title = db.Column(db.String(200), nullable=False)
    document_type = db.Column(db.String(100), nullable=False)  # Agreement, Notice, Schedule, etc.
    file_path = db.Column(db.String(300), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 📅 Validity & Lifecycle
    valid_from = db.Column(db.Date, nullable=True)
    valid_until = db.Column(db.Date, nullable=True)
    is_expired = db.Column(db.Boolean, default=False)
    version_number = db.Column(db.String(20), nullable=True)
    previous_version_id = db.Column(db.Integer, db.ForeignKey('loan_documents.id'), nullable=True)

    # 🔁 Versioning
    previous_version = db.relationship('LoanDocument', remote_side=[id], backref='next_versions')

    # ☁️ Cloud Storage Integration
    external_storage_id = db.Column(db.String(255), nullable=True)  # e.g. AWS S3, Azure Blob
    storage_provider = db.Column(db.String(100), nullable=True)  # e.g. 'AWS', 'Dropbox', 'Google Drive'
    download_token = db.Column(db.String(255), nullable=True)

    # 🧠 AI / GAR Fields
    parsed_summary = db.Column(db.Text, nullable=True)
    ai_tags = db.Column(db.Text, nullable=True)  # ["fixed", "secured", "EUR"]
    gar_risk_flag = db.Column(db.Boolean, default=False)
    gar_context_reference = db.Column(db.String(100), nullable=True)
    gar_notes = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(JSONB, nullable=True)

    # 🔐 Audit
    last_modified_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    last_modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ip_uploaded_from = db.Column(db.String(45), nullable=True)

    # 🔁 Relationships
    loan = db.relationship('Loan', backref='documents')
    company = db.relationship('Company', backref='loan_documents')
    client = db.relationship('Client', backref='loan_documents')
    uploaded_by = db.relationship('User', backref='uploaded_loan_documents', foreign_keys=[uploaded_by_id])
    last_modified_by = db.relationship('User', foreign_keys=[last_modified_by_id])

    def __repr__(self):
        return f"<LoanDocument {self.title} (Loan ID: {self.loan_id})>"

