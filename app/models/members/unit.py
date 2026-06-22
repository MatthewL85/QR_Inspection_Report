# app/models/members/unit.py

from datetime import datetime
import uuid
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import validates
from app.extensions import db
from app.models.core.document import Document


class Block(db.Model):
    """
    Physical block / building within a client (estate / development).

    Shared across:
      - Property Management (LogixPM)
      - Works Logix (for asset locations)
      - Members Logix (for owner communications)
    """
    __tablename__ = "blocks"

    id = db.Column(db.Integer, primary_key=True)

    # Hierarchy
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    # Identity
    name = db.Column(db.String(128), nullable=False)
    code = db.Column(db.String(50), nullable=True)          # e.g. "Block A"
    description = db.Column(db.Text, nullable=True)

    # Meta
    building_type = db.Column(db.String(50), nullable=True) # apartment, mixed-use, car-park, etc.
    number_of_cores = db.Column(db.Integer, nullable=True)
    number_of_floors = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = db.relationship("Client", back_populates="blocks")
    company = db.relationship("Company", back_populates="blocks")
    cores = db.relationship("Core", back_populates="block", cascade="all, delete-orphan", lazy="dynamic")
    units = db.relationship("Unit", back_populates="block", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Block id={self.id} name={self.name} client_id={self.client_id}>"


class Core(db.Model):
    """
    Vertical core within a block (stair / lift core).
    """
    __tablename__ = "cores"

    id = db.Column(db.Integer, primary_key=True)
    block_id = db.Column(db.Integer, db.ForeignKey("blocks.id", ondelete="CASCADE"), nullable=False)

    name = db.Column(db.String(128), nullable=False)         # e.g. "Core 1"
    code = db.Column(db.String(50), nullable=True)           # e.g. "Stair 1"
    description = db.Column(db.Text, nullable=True)

    lift_count = db.Column(db.Integer, nullable=True)
    stair_count = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    block = db.relationship("Block", back_populates="cores")
    units = db.relationship("Unit", back_populates="core", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Core id={self.id} name={self.name} block_id={self.block_id}>"


class Unit(db.Model):
    """
    Core Unit / Apartment / Commercial Unit model.

    This is the central anchor for:
      - Members Logix (owners / communications)
      - Works Logix (work orders, inspections)
      - Finance Logix (service charge, arrears)
      - GAR (AI governance & lease intelligence)
    """
    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint(
            "client_id",
            "block_name",
            "unit_type",
            "unit_number",
            name="uq_units_client_block_type_number",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    unit_uid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)

    # 🔗 Core Relationships
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    block_id = db.Column(db.Integer, db.ForeignKey("blocks.id", ondelete="SET NULL"), nullable=True)
    core_id = db.Column(db.Integer, db.ForeignKey("cores.id", ondelete="SET NULL"), nullable=True)

    # Optional parent/child, e.g. car-space linked to apartment
    parent_unit_id = db.Column(db.Integer, db.ForeignKey("units.id", ondelete="SET NULL"), nullable=True)

    # 📌 Core Identifiers
    unit_label = db.Column(db.String(50), nullable=False)     # A101, Apt 3B, Unit 4
    unit_number = db.Column(db.String(50), nullable=True)     # generated/stable sequence: A-001
    unit_name = db.Column(db.String(120), nullable=True)      # human-friendly optional name
    unit_reference = db.Column(db.String(100), nullable=True) # external / legacy reference
    unit_type = db.Column(db.String(50), nullable=True)       # Residential, Commercial, Duplex, Parking, etc.
    unit_category = db.Column(db.String(50), nullable=True)   # e.g. "Apartment", "Retail", "Storage"

    address_line_1 = db.Column(db.String(200), nullable=True)
    address_line_2 = db.Column(db.String(200), nullable=True)
    town_city = db.Column(db.String(100), nullable=True)
    county_region = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True)

    block_name = db.Column(db.String(100), nullable=True)     # denormalised helper for quick display
    core_name = db.Column(db.String(100), nullable=True)      # denormalised helper for core/stair/lift core
    area_name = db.Column(db.String(100), nullable=True)      # denormalised helper for commercial/other areas
    entrance = db.Column(db.String(100), nullable=True)
    floor_number = db.Column(db.String(50), nullable=True)
    square_meters = db.Column(db.Float, nullable=True)
    bedrooms = db.Column(db.Integer, nullable=True)
    bathrooms = db.Column(db.Integer, nullable=True)

    # Parking / storage linkage (optional)
    parking_label = db.Column(db.String(50), nullable=True)
    storage_label = db.Column(db.String(50), nullable=True)
    letting_agent_name = db.Column(db.String(160), nullable=True)
    letting_agent_phone = db.Column(db.String(50), nullable=True)
    letting_agent_email = db.Column(db.String(255), nullable=True)
    letting_agent_address_line1 = db.Column(db.String(255), nullable=True)
    letting_agent_address_line2 = db.Column(db.String(255), nullable=True)
    letting_agent_city = db.Column(db.String(120), nullable=True)
    letting_agent_region = db.Column(db.String(120), nullable=True)
    letting_agent_postcode = db.Column(db.String(30), nullable=True)
    letting_agent_country = db.Column(db.String(120), nullable=True)
    letting_agent_notes = db.Column(db.Text, nullable=True)

    # 🔌 Utilities / meters (for future AI parsing & residents portal)
    electricity_mprn = db.Column(db.String(50), nullable=True)
    gas_mprn = db.Column(db.String(50), nullable=True)
    water_meter_reference = db.Column(db.String(50), nullable=True)

    # 📑 Occupancy & Status
    occupancy_status = db.Column(db.String(50), default="unknown")  # owned, rented, vacant, under_construction
    owner_portfolio_type = db.Column(db.String(80), nullable=True)
    owner_portfolio_name = db.Column(db.String(160), nullable=True)
    owner_portfolio_reference = db.Column(db.String(100), nullable=True)
    owner_portfolio_notes = db.Column(db.Text, nullable=True)
    sale_status = db.Column(db.String(50), nullable=True)
    conveyancing_status = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default="Active", nullable=False)
    autogenerated = db.Column(db.Boolean, default=False, nullable=False)
    is_common_area = db.Column(db.Boolean, default=False)
    is_occupied = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    last_inspection_date = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # -------------------------------
    # 💰 Service Charge / Finance
    # -------------------------------
    service_charge_scheme = db.Column(db.String(100), nullable=True)
    service_charge_percent = db.Column(db.Float, nullable=True)
    service_charge_amount = db.Column(db.Numeric(10, 2), default=0.00)
    billing_frequency = db.Column(db.String(50), nullable=True)  # Monthly, Quarterly, Annually
    financial_year_start = db.Column(db.Date, nullable=True)
    financial_year_end = db.Column(db.Date, nullable=True)
    currency = db.Column(db.String(10), default="EUR")
    financial_account_ref = db.Column(db.String(100), nullable=True)

    # Optional finance integration hooks
    finance_ledger_code = db.Column(db.String(100), nullable=True)
    finance_external_ref = db.Column(db.String(100), nullable=True)

    # -------------------------------
    # 📄 Lease Info
    # -------------------------------
    lease_start_date = db.Column(db.Date, nullable=True)
    lease_end_date = db.Column(db.Date, nullable=True)
    lease_term_years = db.Column(db.Float, nullable=True)
    lease_reference = db.Column(db.String(100), nullable=True)

    # -------------------------------
    # 🤖 AI / GAR Integration
    # -------------------------------
    document_filename = db.Column(db.String(255), nullable=True)
    ai_summary = db.Column(db.Text, nullable=True)
    ai_parsed_lease_terms = db.Column(db.Text, nullable=True)
    ai_extracted_floorplan_info = db.Column(db.Text, nullable=True)
    ai_utility_flag = db.Column(db.Text, nullable=True)
    ai_key_clauses = db.Column(db.JSON, nullable=True)
    ai_service_charge_risks = db.Column(db.Text, nullable=True)
    ai_occupancy_type = db.Column(db.String(50), nullable=True)  # member-occupied / rented
    ai_compliance_notes = db.Column(db.Text, nullable=True)
    ai_source_type = db.Column(db.String(50), nullable=True)
    ai_confidence_score = db.Column(db.Float, nullable=True)
    ai_parsed_at = db.Column(db.DateTime, nullable=True)
    parsed_by_ai_version = db.Column(db.String(50), nullable=True)
    is_ai_processed = db.Column(db.Boolean, default=False)
    ai_lease_term_risk_score = db.Column(db.Float, nullable=True)

    # -------------------------------
    # ⚖️ GAR Evaluation
    # -------------------------------
    gar_recommendations = db.Column(db.Text, nullable=True)
    gar_flagged_clauses = db.Column(db.JSON, nullable=True)
    gar_risk_score = db.Column(db.Float, nullable=True)
    gar_alignment_status = db.Column(db.String(100), nullable=True)
    gar_chat_ready = db.Column(db.Boolean, default=False)
    gar_feedback = db.Column(db.Text, nullable=True)

    # -------------------------------
    # 🕒 Audit Trail
    # -------------------------------
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # -------------------------------
    # 🔁 ORM Relationships
    # -------------------------------
    company = db.relationship("Company", back_populates="units")
    client = db.relationship("Client", back_populates="units")

    block = db.relationship("Block", back_populates="units")
    core = db.relationship("Core", back_populates="units")

    # Parent/child self-reference (e.g. apt with linked car space)
    parent_unit = db.relationship("Unit", remote_side=[id], backref="child_units")

    # Legal owners (Members) – via association table defined in member.py
    members = db.relationship(
        "Member",
        secondary="member_units",
        back_populates="units",
        lazy="dynamic",
    )

    membership_links = db.relationship(
        "UnitMembership",
        back_populates="unit",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # Occupants (Residents) – via Resident.unit relationship backref="residents"
    # We DO NOT define a 'residents' relationship here to avoid conflicts;
    # Resident model already has:
    #   unit = db.relationship("Unit", backref="residents")

    # 📎 Documents linked to this unit (leases, surveys, etc.)
    documents = db.relationship("Document", back_populates="unit", lazy="dynamic")

    @validates("ai_key_clauses", "gar_flagged_clauses")
    def validate_json_fields(self, key, value):
        """
        Ensure JSON-like fields are either None, dict, or list.
        This keeps GAR / AI parsing predictable across the platform.
        """
        if value is None:
            return None
        if not isinstance(value, (dict, list)):
            raise ValueError(f"{key} must be JSON serializable (dict or list)")
        return value

    def __repr__(self) -> str:
        return f"<Unit {self.unit_label} | Client {self.client_id}>"
