# 📦 LogixPM Models – Fully Integrated, SaaS-Ready Architecture
from app import db  # ✅ Use the shared instance
from datetime import datetime
from flask_login import UserMixin

# ----------------------------
# USER TABLE
# ----------------------------
# Stores all users in the system (PMs, contractors, directors, admins, etc.)
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pin = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    company = db.relationship('Client', foreign_keys=[company_id], backref='users')

# ----------------------------
# CLIENT TABLE
# ----------------------------
# Stores management clients such as OMCs, HOAs, etc.
class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(250))
    postal_code = db.Column(db.String(20))
    registration_number = db.Column(db.String(50))
    vat_reg_number = db.Column(db.String(50))
    tax_number = db.Column(db.String(50))
    year_of_construction = db.Column(db.String(10))
    number_of_units = db.Column(db.Integer)
    client_type = db.Column(db.String(50))
    contract_value = db.Column(db.Numeric(10, 2), default=0.0)

    financial_year_end = db.Column(db.Date, nullable=True)  
    last_agm_date = db.Column(db.Date, nullable=True) 
    agm_completed = db.Column(db.Boolean, default=False)
 
    country = db.Column(db.String(100))
    region = db.Column(db.String(100))
    currency = db.Column(db.String(10))
    timezone = db.Column(db.String(50))
    preferred_language = db.Column(db.String(50))
    ownership_type = db.Column(db.String(50))

    transfer_of_common_area = db.Column(db.Boolean, default=False)
    deed_of_covenants = db.Column(db.String(250))
    data_protection_compliance = db.Column(db.String(50))
    consent_to_communicate = db.Column(db.Boolean, default=True)

    min_directors = db.Column(db.Integer)
    max_directors = db.Column(db.Integer)
    number_of_blocks = db.Column(db.Integer)
    block_names = db.Column(db.String(300))
    cores_per_block = db.Column(db.String(300))
    apartments_per_block = db.Column(db.String(300))

    assigned_pm_id = db.Column(db.Integer, db.ForeignKey('users.id'))  
    assigned_pm = db.relationship('User', backref='assigned_clients', foreign_keys=[assigned_pm_id])



    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ----------------------------
# COUNTRY CLIENT CONFIG TABLE
# ----------------------------
# Stores per-country default legal/ownership rules
class CountryClientConfig(db.Model):
    __tablename__ = 'country_client_config'

    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(100), nullable=False)
    client_type = db.Column(db.String(100), nullable=False)
    legal_basis = db.Column(db.String(300))
    currency = db.Column(db.String(10))
    ownership_types = db.Column(db.Text)  # Store as JSON string
    timezones = db.Column(db.Text)        # Store as JSON string
    regions = db.Column(db.Text)          # Store as JSON string
    is_commercial = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ----------------------------
# UNIT TABLE
# ----------------------------
# Tracks individual apartment/commercial units
class Unit(db.Model):
    __tablename__ = 'units'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    unit_label = db.Column(db.String(50))
    unit_type = db.Column(db.String(50))
    address_line_1 = db.Column(db.String(200))
    postal_code = db.Column(db.String(20))
    block_name = db.Column(db.String(100))
    floor_number = db.Column(db.String(50))
    square_meters = db.Column(db.Float)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    service_charge_scheme = db.Column(db.String(100))
    service_charge_percent = db.Column(db.Float)
    financial_year_start = db.Column(db.Date)
    financial_year_end = db.Column(db.Date)
    currency = db.Column(db.String(10), default="EUR")
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)


# ----------------------------
# EQUIPMENT TABLE
# ----------------------------
# Stores equipment assigned to each client/unit
class Equipment(db.Model):
    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)
    qr_code_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150))
    equipment_type = db.Column(db.String(50))
    serial_number = db.Column(db.String(100))
    model = db.Column(db.String(100))
    age = db.Column(db.String(50))
    maintenance_frequency = db.Column(db.String(50))
    warranty_expiry = db.Column(db.String(20))
    last_inspection = db.Column(db.String(20))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ----------------------------
# INSPECTIONS
# ----------------------------
# Inspections carried out on equipment
class Inspection(db.Model):
    __tablename__ = 'inspections'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    inspector_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    role = db.Column(db.String(50))
    inspection_date = db.Column(db.Date)
    status = db.Column(db.String(50))
    next_due = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ----------------------------
# ALERTS
# ----------------------------
# Tracks open issues flagged by inspections or staff
class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    priority = db.Column(db.String(20))
    status = db.Column(db.String(50), default='Open')
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'))
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    created_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ----------------------------
# MEDIA FILES
# ----------------------------
# Uploadable files tied to inspections, alerts, etc.
class MediaFile(db.Model):
    __tablename__ = 'media_files'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    file_path = db.Column(db.String(250))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    related_table = db.Column(db.String(50))
    related_id = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_type = db.Column(db.String(50))  # image, video, pdf, etc.
    visibility = db.Column(db.String(20), default='private')  # private/public
    description = db.Column(db.String(200))



# ----------------------------
# CAPEX MODULE
# ----------------------------
# Tracks capital expenditure requests and approvals
class CapexRequest(db.Model):
    __tablename__ = 'capex_requests'

    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(100))
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='Pending')
    file = db.Column(db.String(200))
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))


class CapexResponse(db.Model):
    __tablename__ = 'capex_responses'

    id = db.Column(db.Integer, primary_key=True)
    capex_request_id = db.Column(db.Integer, db.ForeignKey('capex_requests.id'))
    contractor_name = db.Column(db.String(100))
    quote_amount = db.Column(db.Float)
    file = db.Column(db.String(200))
    notes = db.Column(db.Text)
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


class CapexApproval(db.Model):
    __tablename__ = 'capex_approvals'

    id = db.Column(db.Integer, primary_key=True)
    capex_request_id = db.Column(db.Integer, db.ForeignKey('capex_requests.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approval_notes = db.Column(db.Text)
    status = db.Column(db.String(50))
    approved_at = db.Column(db.DateTime, default=datetime.utcnow)


# ----------------------------
# MANUAL TASKS & CONTRACTORS
# ----------------------------
# Tracks routine/manual tasks and assigned contractors
class ManualTask(db.Model):
    __tablename__ = 'manual_tasks'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    task_name = db.Column(db.String(150))
    frequency = db.Column(db.String(50))
    status = db.Column(db.String(50))
    due_date = db.Column(db.Date)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(120))


class ManualTaskContractor(db.Model):
    __tablename__ = 'manual_task_contractors'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('manual_tasks.id'))
    contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)


# ----------------------------
# DIRECTOR TO AREA ASSIGNMENT
# ----------------------------
# Associates directors with specific site areas
class DirectorAreaAssignment(db.Model):
    __tablename__ = 'director_area_assignments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    area = db.Column(db.String(100))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)


# ----------------------------
# NOTIFICATIONS
# ----------------------------
# Sends alerts/updates to users
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    message = db.Column(db.Text)
    type = db.Column(db.String(50))  # alert, capex, inspection, etc.
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ----------------------------
# WORK ORDERS
# ----------------------------
class WorkOrder(db.Model):
    __tablename__ = 'work_orders'

    id = db.Column(db.Integer, primary_key=True)
    request_type = db.Column(db.String(50), default='Work Order')  # Options: Work Order, Quotation Request
    description = db.Column(db.Text, nullable=False)
    occupant_name = db.Column(db.String(100))
    occupant_apartment = db.Column(db.String(50))
    occupant_phone = db.Column(db.String(20))
    business_type = db.Column(db.String(100))  # E.g., Plumbing, Electrical
    status = db.Column(db.String(50), default='Open')  # Open, Accepted, Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    client = db.relationship('Client')

    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    unit = db.relationship('Unit')

    preferred_contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    second_preferred_contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    accepted_contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    preferred_contractor = db.relationship('User', foreign_keys=[preferred_contractor_id], backref='preferred_work_orders')
    second_preferred_contractor = db.relationship('User', foreign_keys=[second_preferred_contractor_id], backref='secondary_work_orders')
    accepted_contractor = db.relationship('User', foreign_keys=[accepted_contractor_id], backref='accepted_work_orders')


# ----------------------------
# WORK ORDER COMPLETION
# ----------------------------
class WorkOrderCompletion(db.Model):
    __tablename__ = 'work_order_completions'

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), unique=True)
    completed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    completion_notes = db.Column(db.Text)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    work_order = db.relationship('WorkOrder', backref='completion')
    completed_by = db.relationship('User')


class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), unique=True, nullable=False)
    contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # PM or accounts

    invoice_number = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    tax_rate = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Numeric(10, 2))  # auto-calculated: amount + tax
    currency = db.Column(db.String(10), default="EUR")  # Allow multi-region use

    invoice_date = db.Column(db.Date, default=datetime.utcnow)
    due_date = db.Column(db.Date)

    file_url = db.Column(db.String(255))  # auto-generated PDF location
    notes = db.Column(db.Text)  # optional contractor/internal notes

    # Invoice Status Workflow
    status = db.Column(db.String(50), default='Pending')  
    # Options: Pending, Submitted, Under Review, Approved, Rejected, Paid, Cancelled

    submitted_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    rejected_reason = db.Column(db.Text)

    included_in_payment_run = db.Column(db.Boolean, default=False)  # Future flag
    paid_at = db.Column(db.DateTime)  # When paid

    finance_batch_id = db.Column(db.Integer, db.ForeignKey('payment_runs.id'))
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'))

    # Relationships
    work_order = db.relationship('WorkOrder', backref=db.backref('invoice', uselist=False))
    contractor = db.relationship('User', foreign_keys=[contractor_id], backref='submitted_invoices')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='approved_invoices')

class PaymentRun(db.Model):
    __tablename__ = 'payment_runs'

    id = db.Column(db.Integer, primary_key=True)
    run_name = db.Column(db.String(100))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    run_date = db.Column(db.Date)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relationships
    client = db.relationship('Client', backref='payment_runs')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    invoices = db.relationship('Invoice', backref='payment_run', lazy=True)


# ----------------------------
# CONTRACTOR PERFORMANCE
# ----------------------------
class ContractorPerformance(db.Model):
    __tablename__ = 'contractor_performance'

    id = db.Column(db.Integer, primary_key=True)
    contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'))
    response_time = db.Column(db.Integer)  # in minutes/hours
    completion_time = db.Column(db.Integer)
    performance_rating = db.Column(db.String(10))  # A, B, C, etc.

    contractor = db.relationship('User', backref='performance_records')
    work_order = db.relationship('WorkOrder')


# ----------------------------
# HR LOGIX MODULE
# ----------------------------

# Stores staff role, department, and status
class HRProfile(db.Model):
    __tablename__ = 'hr_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    job_title = db.Column(db.String(100))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    employment_status = db.Column(db.String(50))
    start_date = db.Column(db.Date)
    probation_end_date = db.Column(db.Date)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)

    # Relationships
    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("hr_profile", uselist=False))
    department = db.relationship("Department", backref="employees")
    manager = db.relationship("User", foreign_keys=[manager_id], backref="managed_profiles")

# Salary records by type (monthly, hourly, etc.)
class Salary(db.Model):
    __tablename__ = 'salaries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    payment_type = db.Column(db.String(50))
    amount = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(5))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)

    user = db.relationship("User", foreign_keys=[user_id])
    creator = db.relationship("User", foreign_keys=[created_by])


# Uploads and categorizes HR documents
class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255))
    file_type = db.Column(db.String(50))
    file_path = db.Column(db.String(255))
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    linked_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    linked_client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)

    uploaded_by_user = db.relationship("User", foreign_keys=[uploaded_by])
    user = db.relationship("User", foreign_keys=[linked_user_id])
    client = db.relationship("Client", foreign_keys=[linked_client_id])


# Tracks absence and leave requests
class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    leave_type = db.Column(db.String(50))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pending')
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    user = db.relationship("User", foreign_keys=[user_id])
    approver = db.relationship("User", foreign_keys=[approved_by])


# Performance reviews by manager/director
class PerformanceReview(db.Model):
    __tablename__ = 'performance_reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    review_date = db.Column(db.Date)
    score = db.Column(db.Integer)
    feedback = db.Column(db.Text)
    goals_set = db.Column(db.Text)

    user = db.relationship("User", foreign_keys=[user_id])
    reviewer = db.relationship("User", foreign_keys=[reviewer_id])


# Tracks certifications and uploaded docs
class Certification(db.Model):
    __tablename__ = 'certifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100))
    issued_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    uploaded_document_id = db.Column(db.Integer, db.ForeignKey('documents.id'))

    user = db.relationship("User", foreign_keys=[user_id])
    document = db.relationship("Document", foreign_keys=[uploaded_document_id])



# Lists departments and department managers
class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    budget = db.Column(db.Numeric(12, 2), nullable=True)
    description = db.Column(db.Text)

    manager = db.relationship("User", foreign_keys=[manager_id])


# Defines employment contract records
class EmploymentContract(db.Model):
    __tablename__ = 'employment_contracts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    contract_type = db.Column(db.String(50))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date, nullable=True)
    terms_summary = db.Column(db.Text)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'))

    user = db.relationship("User", foreign_keys=[user_id])
    document = db.relationship("Document", foreign_keys=[document_id])


# Logs exit information for terminated staff
class TerminationRecord(db.Model):
    __tablename__ = 'termination_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    termination_date = db.Column(db.Date)
    reason = db.Column(db.Text)
    exit_interview_notes = db.Column(db.Text)
    replacement_required = db.Column(db.Boolean, default=False)

    user = db.relationship("User", foreign_keys=[user_id])


# Director review of Property Manager performance
class PMReviewByDirector(db.Model):
    __tablename__ = 'pm_reviews_by_director'

    id = db.Column(db.Integer, primary_key=True)
    property_manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    director_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    review_period = db.Column(db.String(20))
    rating = db.Column(db.Integer)
    strengths = db.Column(db.Text)
    areas_for_improvement = db.Column(db.Text)
    overall_comment = db.Column(db.Text)

    property_manager = db.relationship("User", foreign_keys=[property_manager_id])
    director = db.relationship("User", foreign_keys=[director_id])
    client = db.relationship("Client", foreign_keys=[client_id])

# Director review of overall property management company
class ManagementCompanyReview(db.Model):
    __tablename__ = 'management_company_reviews'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    director_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    review_period = db.Column(db.String(20))
    communication_rating = db.Column(db.Integer)
    responsiveness_rating = db.Column(db.Integer)
    financial_transparency_rating = db.Column(db.Integer)
    value_rating = db.Column(db.Integer)
    overall_satisfaction_rating = db.Column(db.Integer)
    comments = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    director = db.relationship("User", foreign_keys=[director_id])
    company = db.relationship("Client", foreign_keys=[company_id])
    client = db.relationship("Client", foreign_keys=[client_id])

class ContractorComplianceDocument(db.Model):
    __tablename__ = 'contractor_compliance_documents'

    id = db.Column(db.Integer, primary_key=True)
    contractor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_type = db.Column(db.String(100), nullable=False)  # e.g., Insurance, Safety Cert
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Future Enhancements
    reminder_sent = db.Column(db.Boolean, default=False)  # If alert has been sent
    reminder_date = db.Column(db.DateTime, nullable=True)  # When the reminder was sent
    is_required_for_work_order = db.Column(db.Boolean, default=True)  # Gating logic
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # New Fields
    reviewed = db.Column(db.Boolean, default=False)  # Admin has verified the document
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Admin user
    reviewed_at = db.Column(db.DateTime, nullable=True)  # Timestamp of review

    # Relationships
    contractor = db.relationship('User', foreign_keys=[contractor_id], backref='compliance_documents')
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id])
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])
