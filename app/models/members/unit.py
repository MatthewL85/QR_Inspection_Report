# app/models/unit.py

from datetime import datetime
from app.extensions import db
from app.models.members.member import member_units

class Unit(db.Model):
    __tablename__ = 'units'

    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Core Relationships
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # 📌 Core Identifiers
    unit_label = db.Column(db.String(50), nullable=False)  # A101, Apt 3B
    unit_type = db.Column(db.String(50))                   # Residential, Commercial, Duplex, etc.
    address_line_1 = db.Column(db.String(200))
    postal_code = db.Column(db.String(20))
    block_name = db.Column(db.String(100))
    floor_number = db.Column(db.String(50))
    square_meters = db.Column(db.Float)

    # 👥 Ownership & Occupancy
    members = db.relationship('Member', secondary=member_units, back_populates='units')  # Legal owner(s)

    resident_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resident = db.relationship("User", foreign_keys=[resident_id], backref="units_residing")

    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    tenant = db.relationship("User", foreign_keys=[tenant_id], backref="units_tenanted")

    occupancy_status = db.Column(db.String(50), default='unknown')  # owned, rented, vacant, under_construction
    is_occupied = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    last_inspection_date = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text)

    # 💰 Financial Info
    service_charge_scheme = db.Column(db.String(100))
    service_charge_percent = db.Column(db.Float)
    service_charge_amount = db.Column(db.Numeric(10, 2), default=0.00)
    billing_frequency = db.Column(db.String(50))  # Monthly, Quarterly, Annually
    financial_year_start = db.Column(db.Date)
    financial_year_end = db.Column(db.Date)
    currency = db.Column(db.String(10), default="EUR")
    financial_account_ref = db.Column(db.String(100), nullable=True)

    # 📄 Lease Info
    lease_start_date = db.Column(db.Date)
    lease_end_date = db.Column(db.Date)

    # 🤖 AI / GAR Integration
    document_filename = db.Column(db.String(255))
    ai_summary = db.Column(db.Text)
    ai_parsed_lease_terms = db.Column(db.Text)
    ai_extracted_floorplan_info = db.Column(db.Text)
    ai_utility_flag = db.Column(db.Text)
    ai_key_clauses = db.Column(db.JSON)
    ai_service_charge_risks = db.Column(db.Text)
    ai_occupancy_type = db.Column(db.String(50))  # member-occupied / rented
    ai_compliance_notes = db.Column(db.Text)
    ai_source_type = db.Column(db.String(50))
    ai_confidence_score = db.Column(db.Float)
    ai_parsed_at = db.Column(db.DateTime)
    parsed_by_ai_version = db.Column(db.String(50))
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_lease_term_risk_score = db.Column(db.Float)

    # ⚖️ GAR Evaluation
    gar_recommendations = db.Column(db.Text)
    gar_flagged_clauses = db.Column(db.JSON)
    gar_risk_score = db.Column(db.Float, nullable=True)
    gar_alignment_status = db.Column(db.String(100), nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # 🕒 Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 🔁 Relationships
    company = db.relationship('Company', back_populates='units')
    client = db.relationship('Client', backref='units')

    def __repr__(self):
        return f"<Unit {self.unit_label} | Client {self.client_id}>"


