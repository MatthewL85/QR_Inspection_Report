from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class AreaType(db.Model):
    __tablename__ = 'area_types'

    id = db.Column(db.Integer, primary_key=True)

    # 🏢 Area Classification
    name = db.Column(db.String(100), unique=True, nullable=False)  # e.g., Residential, Commercial, Car Park
    description = db.Column(db.Text, nullable=True)

    # 🌍 Multi-tenant Scope
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    # 🧠 AI & GAR Intelligence Fields
    ai_tag = db.Column(db.String(100), nullable=True)               # e.g., auto-detected zone type
    gar_risk_flag = db.Column(db.Boolean, default=False)            # Highlighted for review by GAR
    parsed_summary = db.Column(db.Text, nullable=True)              # AI-generated summary
    extracted_data = db.Column(JSONB, nullable=True)                # e.g., { "usage": "Residential", "density": "High" }
    gar_notes = db.Column(db.Text, nullable=True)                   # GAR insights, e.g., zoning conflict, non-compliance

    # 🌐 Integration Metadata (optional future use)
    external_reference = db.Column(db.String(100), nullable=True)   # e.g., BIM link, mapping API ref
    synced_with_gis = db.Column(db.Boolean, default=False)
    external_tags = db.Column(JSONB, nullable=True)                 # Open data classification, zoning codes, etc.

    # 🕒 Audit Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 🔁 Relationships
    company = db.relationship('Company', backref='area_types')
    client = db.relationship('Client', backref='area_types')
    created_by = db.relationship('User', backref='created_area_types', foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<AreaType {self.name} | Client={self.client_id}>"
