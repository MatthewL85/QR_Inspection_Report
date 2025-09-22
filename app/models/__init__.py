from app.extensions import db

# ----------------------------
# Audit Models
# ----------------------------

from app.models.audit.audit_log import AuditLog
from app.models.audit.profile_change_log import ProfileChangeLog
from app.models.audit.password_change_log import PasswordChangeLog
from app.models.audit.email_log import EmailLog
from app.models.audit.contract_audit import ContractAudit

# ----------------------------
# Core System & Exports Models
# ----------------------------
from app.models.core.user import User
from app.models.core.role import Role
from app.models.core.role_permissions import RolePermission
from app.models.core.notification import Notification
from app.models.core.document import Document
from app.models.core.media_file import MediaFile
from app.models.exports.exported_file_log import ExportedFileLog

# ----------------------------
# Unit & Equipment
# ----------------------------
from app.models.members.unit import Unit
from app.models.maintenance.equipment import Equipment
from app.models.maintenance.inspection import Inspection
from app.models.maintenance.inspection_schedule import InspectionSchedule

# ----------------------------
# Clients / Companies
# ----------------------------
from app.models.client.client import Client
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.models.client.agm import AGM
from app.models.client.agm_participant import AGMParticipant
from app.models.client.board_meeting import BoardMeeting
from app.models.client.board_resolution import BoardResolution
from app.models.client.lease import Lease
from app.models.client.country_client_config import CountryClientConfig
from app.models.client.board_meeting_attendee import BoardMeetingAttendee
from app.models.client.meeting_integration import MeetingIntegration

# ----------------------------
# Contracts
# ----------------------------
from app.models.contracts.template import ContractTemplate
from app.models.contracts.template_version import ContractTemplateVersion
from app.models.contracts.client_contract import ClientContract

# ----------------------------
# Members
# ----------------------------
from app.models.members.member import Member
from app.models.members.resident import Resident
from app.models.members.member_approval import MemberApproval
from app.models.members.resident_request import ResidentRequest
from app.models.members.access_log import AccessLog
from app.models.members.tenancy import Tenancy

# ----------------------------
# Contractor / Works
# ----------------------------
from app.models.contractor.contractor import Contractor
from app.models.contractor.contractor_assignment import ContractorAssignment
from app.models.contractor.contractor_feedback import ContractorFeedback
from app.models.contractor.contractor_performance import ContractorPerformance
from app.models.contractor.contractor_compliance_document import ContractorComplianceDocument
from app.models.works.work_order import WorkOrder
from app.models.works.work_order_completion import WorkOrderCompletion
from app.models.works.work_order_settings import WorkOrderSettings
from app.models.works.work_order_setting_audit_log import WorkOrderSettingAuditLog
from app.models.works.work_order_policy import WorkOrderPolicy
from app.models.works.quote_response import QuoteResponse
from app.models.works.quote_recipient import QuoteRecipient
from app.models.works.special_project import ClientSpecialProject
from app.models.contractor.contractor_team import ContractorTeam
from app.models.contractor.team_message import TeamMessage
from app.models.contractor.team_schedule import TeamSchedule

# ----------------------------
# Maintenance / Manual Tasks
# ----------------------------
from app.models.maintenance.manual_task import ManualTask
from app.models.maintenance.manual_task_contractor import ManualTaskContractor
from app.models.maintenance.maintenance_request import MaintenanceRequest
from app.models.maintenance.alert import Alert  

# ----------------------------
# HR / Employment
# ----------------------------
from app.models.hr.hr_profile import HRProfile
from app.models.hr.salary import Salary
from app.models.hr.leave_request import LeaveRequest
from app.models.hr.performance_review import PerformanceReview
from app.models.hr.certification import Certification
from app.models.hr.employment_contract import EmploymentContract
from app.models.hr.termination_record import TerminationRecord
from app.models.hr.pm_review_by_director import PMReviewByDirector
from app.models.hr.management_company_review import ManagementCompanyReview
from app.models.hr.department import Department
from app.models.hr.hr_policy import HRPolicy
from app.models.hr.user_policy_acknowledgements import UserPolicyAcknowledgements
from app.models.hr.leave_balance_ledger import LeaveBalanceLedger
from app.models.hr.employee_onboarding import EmployeeOnboarding
from app.models.hr.employee_exit_process import EmployeeExitProcess
from app.models.hr.hr_settings import HRSettings
from app.models.hr.hr_setting_entry import HRSettingEntry
from app.models.hr.hr_visibility_control import HRVisibilityControl
from app.models.hr.hr_audit_log import HRAuditLog

# ----------------------------
# Finance / Accounting
# ----------------------------
from app.models.finance.account import Account
from app.models.finance.aged_creditor import AgedCreditor
from app.models.finance.aged_creditor_summary import AgedCreditorSummary
from app.models.finance.aged_debtor import AgedDebtor
from app.models.finance.aged_debtor_summary import AgedDebtorSummary
from app.models.finance.annual_service_charge_statements import AnnualServiceChargeStatement
from app.utils.finance.apportionment_engine import ApportionmentEngine
from app.models.finance.apportionment_audit_log import ApportionmentAuditLog
from app.models.finance.area_type import AreaType
from app.models.finance.balance_sheet import BalanceSheet
from app.models.finance.bank_reconciliation import BankReconciliation
from app.models.finance.bank_transaction import BankTransaction
from app.models.finance.budget import Budget
from app.models.finance.budget_allocation_log import BudgetAllocationLog
from app.models.finance.budget_approval import BudgetApproval
from app.models.finance.budget_category import BudgetCategory
from app.models.finance.budget_forecast import BudgetForecast
from app.models.finance.cashflow_statement import CashflowStatement
from app.models.finance.chart_of_account import ChartOfAccount
from app.models.finance.credit_note import CreditNote
from app.models.finance.cross_border_tax_compliance import CrossBorderTaxCompliance
from app.models.finance.debit_note import DebitNote
from app.models.finance.invoice import Invoice
from app.models.finance.transaction import Transaction
from app.models.finance.payment import Payment
from app.models.finance.payment_adjustment import PaymentAdjustment
from app.models.finance.payment_run import PaymentRun
from app.models.finance.finance_batch import FinanceBatch
from app.models.finance.arrears import Arrears
from app.models.finance.expenditure import Expenditure
from app.models.finance.service_charge import ServiceCharge
from app.models.finance.service_charge_payment import ServiceChargePayment
from app.models.finance.financial_audit_log import FinancialAuditLog
from app.models.finance.financial_report_config import FinancialReportConfig
from app.models.finance.debtor import Debtor
from app.models.finance.creditor import Creditor
from app.models.finance.general_ledger_entry import GeneralLedgerEntry
from app.models.finance.generated_report_log import GeneratedReportLog
from app.models.finance.late_fee_transaction_log import LateFeeTransactionLog
from app.models.finance.lease_apportionment_schedule import LeaseApportionmentSchedule
from app.models.finance.levy import Levy
from app.models.finance.levy_payment import LevyPayment
from app.models.finance.ledger_allocation import LedgerAllocation
from app.models.finance.ledger_entry import LedgerEntry
from app.models.finance.ledger_journal import LedgerJournal
from app.models.finance.loan import Loan
from app.models.finance.loan_document import LoanDocument
from app.models.finance.late_fee_interest_policy import LateFeeAndInterestPolicy
from app.models.finance.loan_interest_rate_history import LoanInterestRateHistory
from app.models.finance.loan_repayment_schedule import LoanRepaymentSchedule
from app.models.finance.loan_statement import LoanStatement
from app.models.finance.journal_batch import JournalBatch
from app.models.finance.journal_entry import JournalEntry
from app.models.finance.income_statement import IncomeStatement
from app.models.finance.outstanding_balance import OutstandingBalance
from app.models.finance.outstanding_supplier_invoice import OutstandingSupplierInvoice
from app.models.finance.payment_gateway_log import PaymentGatewayLog
from app.utils.finance.posting_engine import PostingEngine
from app.models.finance.reconciliation_batch import ReconciliationBatch
from app.models.finance.reconciliation_engine import ReconciliationEngine
from app.models.finance.reconciliation_status import ReconciliationStatus
from app.models.finance.refund import Refund
from app.models.finance.supplier_payment_reconciliation import SupplierPaymentReconciliation
from app.models.finance.tax_filing_remittance import TaxFilingRemittance
from app.models.finance.tax_rate import TaxRate
from app.models.finance.tax_transaction_log import TaxTransactionLog
from app.models.finance.trial_balance import TrialBalance
from app.models.finance.withholding_tax_entry import WithholdingTaxEntry


# ----------------------------
# Director Area Assignments
# ----------------------------
from app.models.director.director_area_assignment import DirectorAreaAssignment

# ----------------------------
# CAPEX
# ----------------------------
from app.models.capex.capex_request import CapexRequest
from app.models.capex.capex_approval import CapexApproval
from app.models.capex.capex_response import CapexResponse

# ----------------------------
# Company
# ----------------------------
from app.models.onboarding.company import Company
from app.models.onboarding.bank_account import BankAccount
from app.models.onboarding.insurance_policy import InsurancePolicy
from app.models.onboarding.emergency_contact import EmergencyContact
from app.models.occupancy_log import OccupancyLog

# ----------------------------
# GAR / AI Integration (Future-Ready)
# ----------------------------
# from app.models.gar.gar_chat_context_log import GARChatContextLog
# from app.models.gar.ai_suggestion_log import AISuggestionLog
# from app.models.gar.document_ai_parser import DocumentAIParser
# from app.models.gar.gar_session_log import GARSessionLog

# ----------------------------
# Communication
# ----------------------------
from app.models.communication.external_email_log import ExternalEmailLog
from app.models.communication.email_attachment import EmailAttachment